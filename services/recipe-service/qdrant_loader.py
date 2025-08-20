#!/usr/bin/env python3
"""
Qdrant Vector Database Loader for MealMateAI Recipe Service
Loads recipe summaries into separate Qdrant collections for semantic search
"""

import os
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

# Set environment variables before imports
os.environ['TRANSFORMERS_NO_TF'] = '1'

try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest
    from qdrant_client.http.exceptions import ResponseHandlingException
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Please install required packages: pip install sentence-transformers qdrant-client")
    sys.exit(1)

# Configuration
CLASSIFICATION_RESULTS_PATH = "function_classification_results/function_classified_recipes.json"
SUMMARY_CACHE_DIR = "recipe_summaries"
QDRANT_URL = "http://localhost:6333"
VECTOR_SIZE = 768  # all-mpnet-base-v2 embedding dimensions

# 8 Collections to create (excluding beverages)
COLLECTIONS_CONFIG = {
    "baked-breads": {
        "description": "Baking-focused dishes",
        "estimated_count": 885,
        "batch_size": 50
    },
    "quick-light": {
        "description": "Fast preparation and light meals",
        "estimated_count": 2476,
        "batch_size": 100
    },
    "protein-mains": {
        "description": "Meat, poultry, seafood main dishes",
        "estimated_count": 1379,
        "batch_size": 75
    },
    "comfort-cooked": {
        "description": "Slow-cooked and braised dishes", 
        "estimated_count": 718,
        "batch_size": 50
    },
    "desserts-sweets": {
        "description": "All sweet treats and desserts",
        "estimated_count": 2465,
        "batch_size": 100
    },
    "breakfast-morning": {
        "description": "Morning-specific foods",
        "estimated_count": 415,
        "batch_size": 50
    },
    "plant-based": {
        "description": "Vegetarian and vegan dishes", 
        "estimated_count": 78,
        "batch_size": 25
    },
    "fresh-cold": {
        "description": "Salads and raw preparations",
        "estimated_count": 950,
        "batch_size": 75
    }
}

class QdrantLoader:
    """
    Loads recipe summaries into Qdrant vector database with separate collections
    """
    
    def __init__(self):
        self.client = None
        self.model = None
        self.classified_recipes = None
        self.stats = {
            "total_loaded": 0,
            "collections_created": 0,
            "errors": 0,
            "skipped": 0
        }
        
    def initialize(self):
        """Initialize Qdrant client and embedding model"""
        print("🚀 QDRANT VECTOR DATABASE LOADER")
        print("=" * 50)
        print(f"🔧 Configuration:")
        print(f"   QDRANT_URL: {QDRANT_URL}")
        print(f"   VECTOR_SIZE: {VECTOR_SIZE}")
        print(f"   Collections to load: {len(COLLECTIONS_CONFIG)}")
        print()
        
        # Initialize Qdrant client
        print(f"🔌 Connecting to Qdrant at {QDRANT_URL}...")
        try:
            self.client = QdrantClient(url=QDRANT_URL)
            # Test connection
            collections = self.client.get_collections()
            print(f"✅ Connected to Qdrant (found {len(collections.collections)} existing collections)")
            if collections.collections:
                print(f"   Existing collections: {[c.name for c in collections.collections]}")
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant: {e}")
            print(f"   Error details: {type(e).__name__}: {e}")
            print("💡 Make sure Qdrant is running: docker run -p 6333:6333 qdrant/qdrant")
            return False
        
        # Initialize embedding model
        print("🤖 Loading embedding model (all-mpnet-base-v2)...")
        print("   This may take a moment on first run...")
        try:
            self.model = SentenceTransformer("all-mpnet-base-v2")
            print("✅ Embedding model loaded successfully")
            print(f"   Model max sequence length: {self.model.max_seq_length}")
        except Exception as e:
            print(f"❌ Failed to load embedding model: {e}")
            print(f"   Error details: {type(e).__name__}: {e}")
            return False
        
        return True
    
    def load_classified_recipes(self):
        """Load classified recipes data"""
        print(f"📂 Loading classified recipes from {CLASSIFICATION_RESULTS_PATH}...")
        
        try:
            import os
            file_size = os.path.getsize(CLASSIFICATION_RESULTS_PATH) / (1024 * 1024)  # MB
            print(f"   File size: {file_size:.1f} MB")
            
            with open(CLASSIFICATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
                self.classified_recipes = json.load(f)
            
            print(f"✅ Loaded {len(self.classified_recipes)} classified recipes")
            
            # Count recipes per collection
            collection_counts = {}
            for recipe_data in self.classified_recipes.values():
                collection = recipe_data.get('collection', 'unknown')
                collection_counts[collection] = collection_counts.get(collection, 0) + 1
            
            print("   Recipe distribution by collection:")
            for collection, count in sorted(collection_counts.items()):
                print(f"     {collection}: {count} recipes")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ Classification results not found at {CLASSIFICATION_RESULTS_PATH}")
            print(f"   Current directory: {os.getcwd()}")
            return False
        except Exception as e:
            print(f"❌ Error loading classification results: {e}")
            print(f"   Error details: {type(e).__name__}: {e}")
            return False
    
    def create_collection(self, collection_name: str, description: str) -> bool:
        """Create a Qdrant collection if it doesn't exist"""
        # First, try to get existing collection info
        try:
            collection_info = self.client.get_collection(collection_name)
            print(f"   📁 Collection '{collection_name}' already exists (vectors: {collection_info.vectors_count})")
            return True
        except:
            # Collection doesn't exist, try to create it
            pass
        
        # Try to create the collection
        print(f"   🏗️  Creating collection '{collection_name}': {description}")
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=rest.VectorParams(
                    size=VECTOR_SIZE,
                    distance=rest.Distance.COSINE
                )
            )
            self.stats["collections_created"] += 1
            print(f"   ✅ Collection '{collection_name}' created successfully")
            return True
            
        except Exception as e:
            # If creation failed due to collection existing, that's fine
            error_msg = str(e).lower()
            if "409" in error_msg or "already exists" in error_msg or "conflict" in error_msg:
                print(f"   📁 Collection '{collection_name}' already exists (detected during creation)")
                return True
            else:
                print(f"   ❌ Error creating collection '{collection_name}': {e}")
                return False
    
    def load_recipe_summary(self, recipe_id: str, collection_name: str) -> Optional[str]:
        """Load recipe summary from cache"""
        summary_file = Path(SUMMARY_CACHE_DIR) / collection_name / f"{recipe_id}.txt"
        
        try:
            if summary_file.exists():
                content = summary_file.read_text(encoding='utf-8').strip()
                if content:
                    return content
                else:
                    print(f"     ⚠️  Empty summary file for recipe {recipe_id}")
                    return None
            else:
                print(f"     ⚠️  No summary file found for recipe {recipe_id}")
                return None
        except Exception as e:
            print(f"     ❌ Error reading summary for recipe {recipe_id}: {e}")
            return None
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text"""
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            print(f"     ❌ Error generating embedding: {e}")
            return None
    
    def load_collection_data(self, collection_name: str) -> bool:
        """Load all recipes for a specific collection into Qdrant"""
        print(f"\n📁 Processing collection: {collection_name}")
        
        config = COLLECTIONS_CONFIG[collection_name]
        description = config["description"]
        batch_size = config["batch_size"]
        expected_count = config["estimated_count"]
        
        print(f"   🎯 Target: {description}")
        print(f"   📊 Expected: ~{expected_count} recipes")
        print(f"   🔢 Batch size: {batch_size}")
        
        # Create collection
        if not self.create_collection(collection_name, description):
            return False
        
        # Get recipes for this collection
        print(f"   🔍 Scanning classified recipes for collection '{collection_name}'...")
        collection_recipes = []
        for recipe_id, recipe_data in self.classified_recipes.items():
            if recipe_data.get('collection') == collection_name:
                collection_recipes.append((recipe_id, recipe_data))
        
        if not collection_recipes:
            print(f"   ⚠️  No recipes found for collection {collection_name}")
            return True
        
        print(f"   📊 Found {len(collection_recipes)} recipes (expected ~{expected_count})")
        
        # Check existing vectors in collection
        existing_count = 0
        try:
            collection_info = self.client.get_collection(collection_name)
            existing_count = collection_info.vectors_count
            print(f"   📈 Collection currently has {existing_count} vectors")
            
            if existing_count >= len(collection_recipes):
                print(f"   ✅ Collection appears complete, skipping")
                self.stats["total_loaded"] += existing_count  # Count as loaded
                return True
        except Exception as e:
            print(f"   ⚠️  Could not check existing vectors: {e}")
            pass
        
        # Load recipes in batches
        print(f"   🚀 Starting batch processing...")
        loaded_count = 0
        skipped_count = 0
        total_batches = (len(collection_recipes) + batch_size - 1) // batch_size
        
        for i in range(0, len(collection_recipes), batch_size):
            batch = collection_recipes[i:i + batch_size]
            batch_num = i//batch_size + 1
            
            print(f"   🔄 Processing batch {batch_num}/{total_batches}: {len(batch)} recipes...")
            
            # Prepare batch data
            points = []
            batch_skipped = 0
            
            for j, (recipe_id, recipe_data) in enumerate(batch):
                # Progress indicator for large batches
                if len(batch) >= 50 and j % 25 == 0 and j > 0:
                    print(f"     ⏳ Progress: {j}/{len(batch)} recipes processed...")
                
                # Load summary
                summary = self.load_recipe_summary(recipe_id, collection_name)
                if not summary:
                    batch_skipped += 1
                    continue
                
                # Generate embedding
                embedding = self.generate_embedding(summary)
                if not embedding:
                    batch_skipped += 1
                    continue
                
                # Prepare metadata
                payload = {
                    "recipe_id": recipe_id,
                    "title": str(recipe_data.get('title', ''))[:100],  # Limit title length
                    "collection": collection_name,
                    "confidence": recipe_data.get('confidence', 0),
                    "summary": summary[:500],  # Truncate for storage efficiency
                    "ingredients_preview": str(recipe_data.get('ingredients', []))[:200],
                    "instructions_preview": str(recipe_data.get('instructions', ''))[:200]
                }
                
                # Create point
                try:
                    point = rest.PointStruct(
                        id=int(recipe_id),
                        vector=embedding,
                        payload=payload
                    )
                    points.append(point)
                except Exception as e:
                    print(f"     ⚠️  Error creating point for recipe {recipe_id}: {e}")
                    batch_skipped += 1
                    continue
            
            # Insert batch into Qdrant
            if points:
                try:
                    print(f"     📤 Inserting {len(points)} vectors into Qdrant...")
                    self.client.upsert(
                        collection_name=collection_name,
                        points=points
                    )
                    loaded_count += len(points)
                    print(f"   ✅ Batch {batch_num} completed: {len(points)} vectors inserted")
                    
                    # Brief pause to avoid overwhelming the database
                    time.sleep(0.2)
                    
                except Exception as e:
                    print(f"   ❌ Error inserting batch {batch_num}: {e}")
                    print(f"      Error details: {type(e).__name__}: {e}")
                    self.stats["errors"] += 1
            else:
                print(f"   ⚠️  Batch {batch_num} skipped: no valid vectors")
            
            skipped_count += batch_skipped
            
            # Progress summary for large collections
            if total_batches > 5:
                progress = (batch_num / total_batches) * 100
                print(f"   📊 Progress: {progress:.1f}% ({loaded_count} loaded, {skipped_count} skipped)")
        
        print(f"   🎉 Collection {collection_name} completed: {loaded_count} loaded, {skipped_count} skipped")
        self.stats["total_loaded"] += loaded_count
        self.stats["skipped"] += skipped_count
        
        # Final verification
        try:
            final_info = self.client.get_collection(collection_name)
            final_count = final_info.vectors_count
            print(f"   ✅ Final verification: {final_count} vectors in collection")
        except Exception as e:
            print(f"   ⚠️  Could not verify final count: {e}")
        
        return True
    
    def load_all_collections(self):
        """Load all configured collections"""
        print(f"\n🎯 Loading {len(COLLECTIONS_CONFIG)} collections...")
        
        success_count = 0
        
        for collection_name in COLLECTIONS_CONFIG.keys():
            if self.load_collection_data(collection_name):
                success_count += 1
            else:
                print(f"❌ Failed to load collection: {collection_name}")
        
        return success_count == len(COLLECTIONS_CONFIG)
    
    def print_final_stats(self):
        """Print final loading statistics"""
        print(f"\n🎉 VECTOR DATABASE LOADING COMPLETE!")
        print("=" * 50)
        print(f"📊 Collections created: {self.stats['collections_created']}")
        print(f"📈 Total vectors loaded: {self.stats['total_loaded']}")
        print(f"⚠️  Recipes skipped: {self.stats['skipped']}")
        print(f"❌ Errors encountered: {self.stats['errors']}")
        print("=" * 50)
        
        # Show collection summary
        print("\n📁 COLLECTION SUMMARY:")
        for collection_name in COLLECTIONS_CONFIG.keys():
            try:
                collection_info = self.client.get_collection(collection_name)
                print(f"   {collection_name}: {collection_info.vectors_count} vectors")
            except:
                print(f"   {collection_name}: Error reading collection")
        
        print(f"\n🚀 Vector database ready for semantic search!")
        print(f"💡 Use test_qdrant_cli.py to test search functionality")

def main():
    """Main execution"""
    loader = QdrantLoader()
    
    # Initialize
    if not loader.initialize():
        return 1
    
    # Load classified recipes
    if not loader.load_classified_recipes():
        return 1
    
    # Load all collections
    if not loader.load_all_collections():
        print("❌ Some collections failed to load")
        return 1
    
    # Print stats
    loader.print_final_stats()
    
    return 0

if __name__ == "__main__":
    exit(main())