#!/usr/bin/env python3
"""
Multi-Collection Vector Database Loader
Enhanced version of KaggleRecipeVectorDB with smart collection organization
"""

import os
import json
from pathlib import Path
print("🚀 Starting MultiCollectionVectorDB script...")

# Set environment variables
os.environ['TRANSFORMERS_NO_TF'] = '1'
print("✅ Set TRANSFORMERS_NO_TF environment variable")

import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from refined_collection_strategy import EMBEDDING_STRATEGIES

print("✅ Imported all required modules")

# === CONFIGURATION ===
CSV_PATH = "kaggleRecipes/recipes.csv"
CLASSIFICATION_RESULTS_PATH = "classification_results/classified_recipes.json"
VECTOR_SIZE = 384  # for all-MiniLM-L6-v2 embedding model
QDRANT_URL = "http://localhost:6333"

# Collection configurations
COLLECTIONS_CONFIG = {
    "desserts-sweets": {"priority": "high", "batch_size": 50},
    "sides-sauces": {"priority": "medium", "batch_size": 30},
    "salads-fresh": {"priority": "medium", "batch_size": 30},
    "drinks-beverages": {"priority": "low", "batch_size": 20},
    "appetizers-snacks": {"priority": "medium", "batch_size": 25},
    "breads-baked": {"priority": "medium", "batch_size": 25},
    "meat-mains": {"priority": "high", "batch_size": 30},
    "breakfast-brunch": {"priority": "medium", "batch_size": 20},
    "soups-stews": {"priority": "low", "batch_size": 15},
    "international": {"priority": "low", "batch_size": 15}
}

print(f"📝 Configuration loaded - {len(COLLECTIONS_CONFIG)} collections defined")

class MultiCollectionVectorDB:
    """
    Manages multiple Qdrant collections for optimized recipe search
    """
    
    def __init__(self, qdrant_url=QDRANT_URL):
        self.qdrant_url = qdrant_url
        self.client = None
        self.model = None
        self.classified_recipes = None
        self.original_recipes = None
        
    def initialize_embedding_model(self):
        """Initialize the embedding model using SentenceTransformer"""
        print("🔄 Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        print("✅ Embedding model loaded successfully")
    
    def connect_to_qdrant(self):
        """Connect to Qdrant vector database"""
        print(f"🔌 Connecting to Qdrant at {self.qdrant_url}...")
        self.client = QdrantClient(url=self.qdrant_url)
        print("✅ Connected to Qdrant successfully")
    
    def load_classification_results(self):
        """Load pre-classified recipe data"""
        print(f"📂 Loading classification results from {CLASSIFICATION_RESULTS_PATH}...")
        
        try:
            with open(CLASSIFICATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
                self.classified_recipes = json.load(f)
            print(f"✅ Loaded {len(self.classified_recipes)} classified recipes")
            
            # Also load original CSV for complete data
            self.original_recipes = pd.read_csv(CSV_PATH)
            print(f"✅ Loaded {len(self.original_recipes)} original recipes from CSV")
            
            return True
            
        except FileNotFoundError:
            print(f"❌ Classification results not found at {CLASSIFICATION_RESULTS_PATH}")
            print("💡 Please run recipe_classifier.py first!")
            return False
        except Exception as e:
            print(f"❌ Error loading classification results: {e}")
            return False
    
    def create_collections(self):
        """Create all collection schemas in Qdrant"""
        print("🏗️  Setting up collections in Qdrant...")
        
        for collection_name, config in COLLECTIONS_CONFIG.items():
            print(f"  📁 Creating collection: {collection_name}")
            
            try:
                # Recreate collection (this will delete existing data)
                self.client.recreate_collection(
                    collection_name=collection_name,
                    vectors_config=rest.VectorParams(
                        size=VECTOR_SIZE, 
                        distance=rest.Distance.COSINE
                    ),
                )
                print(f"  ✅ Collection '{collection_name}' created successfully")
                
            except Exception as e:
                print(f"  ❌ Error creating collection '{collection_name}': {e}")
                return False
        
        print("✅ All collections created successfully")
        return True
    
    def optimize_embedding_text(self, recipe_data, collection_name):
        """
        Create optimized embedding text based on collection-specific strategy
        """
        # Get embedding strategy for this collection
        strategy = EMBEDDING_STRATEGIES.get(collection_name, EMBEDDING_STRATEGIES["international"])
        
        # Extract recipe information
        original_data = recipe_data.get('original_data', {})
        name = recipe_data.get('name', '')
        ingredients = original_data.get('ingredients', '')
        cuisine_path = original_data.get('cuisine_path', '')
        
        # Build optimized embedding text based on strategy
        focus_fields = strategy.get('focus_fields', ['recipe_name', 'ingredients'])
        
        text_parts = []
        
        if 'recipe_name' in focus_fields:
            text_parts.append(f"Recipe: {name}")
        
        if 'main_ingredients' in focus_fields or 'ingredients' in focus_fields:
            # Limit ingredients to avoid noise (first 300 chars)
            ingredients_short = ingredients[:300] if ingredients else ""
            text_parts.append(f"Ingredients: {ingredients_short}")
        
        if 'cuisine_type' in focus_fields and cuisine_path:
            text_parts.append(f"Cuisine: {cuisine_path}")
        
        # Add collection-specific enhancements
        enhance_with = strategy.get('enhance_with', [])
        
        if 'dessert_type' in enhance_with and collection_name == 'desserts-sweets':
            if any(keyword in name.lower() for keyword in ['cake', 'pie', 'cookie', 'tart']):
                dessert_type = next((keyword for keyword in ['cake', 'pie', 'cookie', 'tart'] 
                                   if keyword in name.lower()), 'dessert')
                text_parts.append(f"Type: {dessert_type}")
        
        if 'protein_type' in enhance_with and collection_name == 'meat-mains':
            if any(protein in ingredients.lower() for protein in ['chicken', 'beef', 'pork', 'fish']):
                protein_type = next((protein for protein in ['chicken', 'beef', 'pork', 'fish'] 
                                   if protein in ingredients.lower()), 'meat')
                text_parts.append(f"Protein: {protein_type}")
        
        # Combine all parts
        optimized_text = "\n".join(text_parts)
        
        # Limit total length to avoid token limits
        if len(optimized_text) > 500:
            optimized_text = optimized_text[:500] + "..."
        
        return optimized_text
    
    def embed_text(self, text):
        """Generate embedding vector for text using SentenceTransformer"""
        # Returns a list of floats, length VECTOR_SIZE (384)
        vector = self.model.encode(text, show_progress_bar=False)
        return vector.tolist()
    
    def process_recipes_by_collection(self):
        """
        Process and upload recipes organized by collection
        """
        print("🔄 Processing recipes by collection...")
        
        # Group recipes by collection
        recipes_by_collection = {}
        for recipe_id, recipe_data in self.classified_recipes.items():
            collection = recipe_data['collection']
            if collection not in recipes_by_collection:
                recipes_by_collection[collection] = []
            recipes_by_collection[collection].append((recipe_id, recipe_data))
        
        # Process each collection
        total_processed = 0
        
        for collection_name, recipes in recipes_by_collection.items():
            print(f"\n📁 Processing collection: {collection_name}")
            print(f"   📊 {len(recipes)} recipes to process")
            
            # Get collection config
            config = COLLECTIONS_CONFIG.get(collection_name, {"batch_size": 20})
            batch_size = config["batch_size"]
            
            processed_count = 0
            
            # Process recipes in batches
            for i in range(0, len(recipes), batch_size):
                batch = recipes[i:i + batch_size]
                points = []
                
                for recipe_id, recipe_data in batch:
                    try:
                        # Create optimized embedding text
                        embed_text = self.optimize_embedding_text(recipe_data, collection_name)
                        
                        # Generate embedding
                        vector = self.embed_text(embed_text)
                        
                        # Prepare payload with enhanced metadata
                        original_data = recipe_data.get('original_data', {})
                        payload = {
                            "recipe_id": int(recipe_id),
                            "recipe_name": recipe_data.get('name', ''),
                            "collection": collection_name,
                            "classification_confidence": recipe_data.get('confidence', 0),
                            "ingredients": original_data.get('ingredients', ''),
                            "cuisine_path": original_data.get('cuisine_path', ''),
                            "prep_time": original_data.get('prep_time', ''),
                            "cook_time": original_data.get('cook_time', ''),
                            "servings": original_data.get('servings', ''),
                            "embedding_text": embed_text[:200] + "..." if len(embed_text) > 200 else embed_text
                        }
                        
                        # Create point
                        point = rest.PointStruct(
                            id=int(recipe_id),
                            vector=vector,
                            payload=payload,
                        )
                        points.append(point)
                        
                    except Exception as e:
                        print(f"     ⚠️  Error processing recipe {recipe_id}: {e}")
                        continue
                
                # Upload batch to Qdrant
                if points:
                    try:
                        self.client.upsert(collection_name=collection_name, points=points)
                        processed_count += len(points)
                        print(f"     ✅ Batch {i//batch_size + 1}: {len(points)} recipes uploaded")
                    except Exception as e:
                        print(f"     ❌ Error uploading batch: {e}")
            
            print(f"   🎉 Collection '{collection_name}' complete: {processed_count} recipes processed")
            total_processed += processed_count
        
        print(f"\n🎉 All collections processed! Total: {total_processed} recipes")
        return total_processed
    
    def create_collection_info(self):
        """Create metadata about collections for the query router"""
        collection_info = {}
        
        for collection_name in COLLECTIONS_CONFIG.keys():
            try:
                # Get collection info from Qdrant
                info = self.client.get_collection(collection_name)
                
                collection_info[collection_name] = {
                    "vectors_count": info.vectors_count,
                    "indexed_vectors_count": info.indexed_vectors_count,
                    "points_count": info.points_count,
                    "segments_count": info.segments_count,
                    "config": COLLECTIONS_CONFIG[collection_name],
                    "embedding_strategy": EMBEDDING_STRATEGIES.get(collection_name, {})
                }
                
            except Exception as e:
                print(f"⚠️  Could not get info for collection {collection_name}: {e}")
                collection_info[collection_name] = {"error": str(e)}
        
        # Save collection info
        info_file = "multi_collection_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(collection_info, f, indent=2, default=str)
        
        print(f"💾 Collection info saved to {info_file}")
        return collection_info
    
    def run_full_pipeline(self):
        """
        Run the complete multi-collection vector DB setup pipeline
        """
        print("🚀 STARTING MULTI-COLLECTION VECTOR DB PIPELINE")
        print("=" * 60)
        
        # Step 1: Initialize components
        if not self.load_classification_results():
            return False
        
        self.initialize_embedding_model()
        self.connect_to_qdrant()
        
        # Step 2: Create collections
        if not self.create_collections():
            return False
        
        # Step 3: Process and upload recipes
        total_processed = self.process_recipes_by_collection()
        
        # Step 4: Create collection metadata
        collection_info = self.create_collection_info()
        
        print("\n🎉 PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📊 Total recipes processed: {total_processed}")
        print(f"📁 Collections created: {len(COLLECTIONS_CONFIG)}")
        print(f"🔍 Vector database ready for optimized search!")
        
        return True

def main():
    """Main execution function"""
    loader = MultiCollectionVectorDB()
    
    success = loader.run_full_pipeline()
    
    if success:
        print("\n✅ Multi-collection vector database setup complete!")
        print("🚀 Ready for enhanced recipe search performance!")
    else:
        print("\n❌ Pipeline failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())