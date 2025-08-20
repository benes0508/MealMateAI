#!/usr/bin/env python3
"""
Secure Multi-Collection Vector Database Loader for NewDataset13k
Enhanced version with security measures and no beverage collection
"""

import os
import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict

# Security check: Ensure API keys are in environment, not hardcoded
def check_api_security():
    """Check that API keys are properly secured"""
    print("🔒 SECURITY CHECK: Verifying API key configuration...")
    
    # Check if GOOGLE_API_KEY is in environment
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("💡 Please set GOOGLE_API_KEY in your .env file or environment")
        return False
    
    # Check if API key looks valid (starts with AIza and reasonable length)
    if not api_key.startswith("AIza") or len(api_key) < 35:
        print("⚠️  API key format appears invalid")
        return False
    
    # Security reminder
    print("✅ API key found in environment (secure)")
    print("🔒 Security reminder: Never commit API keys to git!")
    return True

# Set environment variables before imports
os.environ['TRANSFORMERS_NO_TF'] = '1'
print("🚀 Starting Secure Multi-Collection Vector DB Loader...")

import pandas as pd
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest
from google import genai
import requests
from qdrant_client.http.exceptions import ResponseHandlingException
import os

# === SECURITY-FIRST CONFIGURATION ===
CLASSIFICATION_RESULTS_PATH = "function_classification_results/function_classified_recipes.json"
VECTOR_SIZE = 768  # for all-mpnet-base-v2 embedding model

QDRANT_URL = "http://localhost:6333"
# Directory to cache generated summaries
SUMMARY_CACHE_DIR = "recipe_summaries"

# Collections to create (EXCLUDING beverages as requested)
SECURE_COLLECTIONS_CONFIG = {
    "desserts-sweets": {
        "description": "All sweet treats and desserts",
        "priority": "high", 
        "batch_size": 50,
        "estimated_count": 2465
    },
    "protein-mains": {
        "description": "Meat, poultry, seafood main dishes", 
        "priority": "high",
        "batch_size": 30,
        "estimated_count": 1379
    },
    "quick-light": {
        "description": "Fast preparation and light meals",
        "priority": "medium",
        "batch_size": 40,
        "estimated_count": 2476
    },
    "fresh-cold": {
        "description": "Salads and raw preparations",
        "priority": "medium", 
        "batch_size": 25,
        "estimated_count": 950
    },
    "baked-breads": {
        "description": "Baking-method specific items",
        "priority": "medium",
        "batch_size": 25,
        "estimated_count": 885
    },
    "comfort-cooked": {
        "description": "Slow-cooked and braised dishes",
        "priority": "low",
        "batch_size": 20,
        "estimated_count": 718
    },
    "breakfast-morning": {
        "description": "Morning-specific foods",
        "priority": "low", 
        "batch_size": 15,
        "estimated_count": 415
    },
    "plant-based": {
        "description": "Vegetarian and vegan dishes",
        "priority": "low",
        "batch_size": 10,
        "estimated_count": 78
    }
}

# Embedding optimization strategies per collection
EMBEDDING_STRATEGIES = {
    "desserts-sweets": {
        "focus_fields": ["title", "sweet_ingredients", "dessert_type"],
        "boost_keywords": ["chocolate", "vanilla", "sugar", "cake", "cookie"],
        "max_length": 400
    },
    "protein-mains": {
        "focus_fields": ["title", "protein_type", "cooking_method"],
        "boost_keywords": ["chicken", "beef", "salmon", "grilled", "roasted"],
        "max_length": 450
    },
    "quick-light": {
        "focus_fields": ["title", "simple_ingredients", "prep_method"],
        "boost_keywords": ["quick", "easy", "simple", "light", "fast"],
        "max_length": 350
    },
    "fresh-cold": {
        "focus_fields": ["title", "fresh_ingredients", "raw_prep"],
        "boost_keywords": ["fresh", "raw", "salad", "cold", "crisp"],
        "max_length": 400
    },
    "baked-breads": {
        "focus_fields": ["title", "flour_ingredients", "baking_method"],
        "boost_keywords": ["bread", "baked", "flour", "yeast", "oven"],
        "max_length": 400
    },
    "comfort-cooked": {
        "focus_fields": ["title", "comfort_ingredients", "slow_method"],
        "boost_keywords": ["braised", "stewed", "comfort", "warm", "hearty"],
        "max_length": 450
    },
    "breakfast-morning": {
        "focus_fields": ["title", "morning_ingredients", "breakfast_type"],
        "boost_keywords": ["breakfast", "morning", "eggs", "pancakes", "oats"],
        "max_length": 350
    },
    "plant-based": {
        "focus_fields": ["title", "plant_ingredients", "veggie_method"],
        "boost_keywords": ["vegetarian", "vegan", "plant", "vegetables", "beans"],
        "max_length": 400
    }
}

class SecureMultiCollectionLoader:
    """
    Secure multi-collection vector database loader with API key protection
    """
    
    def __init__(self):
        self.client = None
        self.model = None
        self.classified_recipes = None
        
        # Security check before proceeding
        if not check_api_security():
            print("❌ Security check failed. Please configure API keys properly.")
            sys.exit(1)
        # Initialize Gemini GenAI client
        self.genai_client = genai.Client()
        print("✅ Gemini GenAI client initialized")
        # Flag to force regenerating summaries, ignoring cache
        self.force_generate_summaries = False
    
    def initialize_embedding_model(self):
        """Initialize the embedding model using SentenceTransformer"""
        print("🔄 Loading embedding model (all-mpnet-base-v2)...")
        try:
            self.model = SentenceTransformer("all-mpnet-base-v2")
            print("✅ Embedding model loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading embedding model: {e}")
            return False
    def summarize_recipe(self, recipe_data):
        """
        Use Gemini API (via Google Generative Language) to produce a concise summary.
        (Legacy single-recipe version; prefer summarize_recipes for batch)
        """
        # Add context for Gemini summarization
        context = (
            "You are helping build MealMateAI, a semantic search service "
            "over multiple recipe collections. Collections and sizes:\n"
            "- desserts-sweets: 2465\n"
            "- protein-mains: 1379\n"
            "- quick-light: 2476\n"
            "- fresh-cold: 950\n"
            "- baked-breads: 885\n"
            "- comfort-cooked: 718\n"
            "- breakfast-morning: 415\n"
            "- plant-based: 78\n"
            "Embedding model used for indexing: all-mpnet-base-v2.\n"
            "Please provide a concise summary of the following recipe:"
        )
        blocks = [recipe_data.get("title", "")]
        ingredients = recipe_data.get("ingredients", [])
        if ingredients:
            blocks.append("Ingredients: " + ", ".join(ingredients))
        if "instructions" in recipe_data:
            blocks.append("Instructions: " + recipe_data.get("instructions"))
        recipe_text = "\n\n".join(blocks)
        prompts = [f"{context}\n\n{recipe_text}"]
        response = self.genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompts
        )
        # Extract single summary
        # If .text exists, use it
        if hasattr(response, "text"):
            return response.text
        # Otherwise, pull from candidates
        candidates = getattr(response, "candidates", [])
        if candidates:
            content = getattr(candidates[0], "content", None)
            if content and hasattr(content, "text"):
                return content.text
        return ""

    def summarize_recipes(self, recipes_data):
        """
        Use Gemini API to summarize a batch of recipes.
        Returns a list of summary strings, one per recipe.
        """
        # Add context for Gemini summarization
        context = (
            "You are helping build MealMateAI, a semantic search service "
            "over multiple recipe collections. Collections and sizes:\n"
            "- desserts-sweets: 2465\n"
            "- protein-mains: 1379\n"
            "- quick-light: 2476\n"
            "- fresh-cold: 950\n"
            "- baked-breads: 885\n"
            "- comfort-cooked: 718\n"
            "- breakfast-morning: 415\n"
            "- plant-based: 78\n"
            "Embedding model used for indexing: all-mpnet-base-v2.\n"
            "Please provide a concise summary of the following recipe:"
        )
        prompts = []
        for recipe_data in recipes_data:
            blocks = [recipe_data.get("title", "")]
            ingredients = recipe_data.get("ingredients", [])
            if ingredients:
                blocks.append("Ingredients: " + ", ".join(ingredients))
            if "instructions" in recipe_data:
                blocks.append("Instructions: " + recipe_data.get("instructions"))
            recipe_text = "\n\n".join(blocks)
            prompts.append(f"{context}\n\n{recipe_text}")
        
        # Batch call
        response = self.genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompts
        )
        summaries = []
        # If .text exists and single prompt, wrap it
        if hasattr(response, "text"):
            return [response.text]
        # Otherwise, iterate over candidates list
        for cand in getattr(response, "candidates", []):
            content = getattr(cand, "content", None)
            if content and hasattr(content, "text"):
                summaries.append(content.text)
            else:
                summaries.append("")
        return summaries
    
    def connect_to_qdrant(self):
        """Connect to Qdrant with error handling"""
        print(f"🔌 Connecting to Qdrant at {QDRANT_URL}...")
        
        try:
            self.client = QdrantClient(url=QDRANT_URL)
            # Test connection
            collections = self.client.get_collections()
            print("✅ Connected to Qdrant successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant: {e}")
            print("💡 Make sure Qdrant is running on port 6333")
            return False

    def clear_existing_collections(self):
        """Delete existing collections to start fresh."""
        print("🗑️  Clearing old collections…")
        for name in SECURE_COLLECTIONS_CONFIG.keys():
            try:
                self.client.delete_collection(collection_name=name)
                print(f" • Deleted collection '{name}'")
            except Exception as e:
                print(f" • Couldn’t delete '{name}' (might not exist): {e}")
    
    def load_classified_recipes(self):
        """Load pre-classified recipe data"""
        print(f"📂 Loading classified recipes from {CLASSIFICATION_RESULTS_PATH}...")
        
        try:
            with open(CLASSIFICATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
                self.classified_recipes = json.load(f)
            
            # Filter out beverages as requested
            filtered_recipes = {}
            removed_count = 0
            
            for recipe_id, recipe_data in self.classified_recipes.items():
                if recipe_data.get('collection') == 'beverages':
                    removed_count += 1
                else:
                    filtered_recipes[recipe_id] = recipe_data
            
            self.classified_recipes = filtered_recipes
            
            print(f"✅ Loaded {len(self.classified_recipes)} recipes")
            print(f"🚫 Excluded {removed_count} beverage recipes as requested")
            return True
            
        except FileNotFoundError:
            print(f"❌ Classification results not found at {CLASSIFICATION_RESULTS_PATH}")
            print("💡 Please run function_based_classifier.py first!")
            return False
        except Exception as e:
            print(f"❌ Error loading classification results: {e}")
            return False
    
    def create_secure_collections(self):
        """Create collections with proper error handling"""
        print("🏗️  Creating secure collections in Qdrant...")
        
        for collection_name, config in SECURE_COLLECTIONS_CONFIG.items():
            print(f"  📁 Creating collection: {collection_name}")
            print(f"     Description: {config['description']}")
            print(f"     Estimated size: {config['estimated_count']} recipes")
            
            try:
                # Recreate collection (removes existing data)
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
        
        print("✅ All secure collections created successfully")
        return True
    
    def optimize_embedding_text(self, recipe_data, collection_name):
        """Create optimized embedding text based on collection strategy"""
        strategy = EMBEDDING_STRATEGIES.get(collection_name, EMBEDDING_STRATEGIES["protein-mains"])
        
        # Get recipe details
        title = recipe_data.get('title', '')
        ingredients = recipe_data.get('ingredients', [])
        
        # Build embedding text
        text_parts = []
        
        # Always include title
        if title:
            text_parts.append(f"Recipe: {title}")
        
        # Add ingredients (limited to avoid noise)
        if ingredients:
            ingredients_text = ', '.join(ingredients[:8])  # Limit to first 8 ingredients
            text_parts.append(f"Ingredients: {ingredients_text}")
        
        # Add collection-specific boosts
        boost_keywords = strategy.get('boost_keywords', [])
        ingredients_lower = ' '.join(ingredients).lower()
        title_lower = title.lower()
        
        relevant_keywords = []
        for keyword in boost_keywords:
            if keyword in title_lower or keyword in ingredients_lower:
                relevant_keywords.append(keyword)
        
        if relevant_keywords:
            text_parts.append(f"Type: {', '.join(relevant_keywords[:3])}")
        
        # Combine and limit length
        combined_text = '\n'.join(text_parts)
        max_length = strategy.get('max_length', 400)
        
        if len(combined_text) > max_length:
            combined_text = combined_text[:max_length] + "..."
        
        return combined_text
    
    def embed_text(self, text):
        """Generate embedding vector for text using SentenceTransformer"""
        try:
            vector = self.model.encode(text, show_progress_bar=False)
            return vector.tolist()
        except Exception as e:
            print(f"⚠️  Error generating embedding: {e}")
            return [0.0] * VECTOR_SIZE
    
    def process_collections_securely(self):
        """Process recipes by collection with security and error handling"""
        print("🔄 Processing recipes by collection...")
        
        # Group recipes by collection (excluding beverages)
        recipes_by_collection = defaultdict(list)
        
        for recipe_id, recipe_data in self.classified_recipes.items():
            collection = recipe_data.get('collection')
            if collection in SECURE_COLLECTIONS_CONFIG:  # Only process allowed collections
                recipes_by_collection[collection].append((recipe_id, recipe_data))
        
        # Process each collection
        total_processed = 0
        processing_stats = {}
        
        for collection_name, recipes in recipes_by_collection.items():
            print(f"\n📁 Processing collection: {collection_name}")
            # Ensure cache folder for this collection
            col_cache_dir = Path(SUMMARY_CACHE_DIR) / collection_name
            col_cache_dir.mkdir(parents=True, exist_ok=True)
            print(f"   📊 {len(recipes)} recipes to process")
            
            config = SECURE_COLLECTIONS_CONFIG[collection_name]
            batch_size = config["batch_size"]
            processed_count = 0
            error_count = 0
            
            # Process in batches
            for i in range(0, len(recipes), batch_size):
                batch = recipes[i:i + batch_size]
                points = []

                # Build summaries by checking cache and calling summarize_recipe per recipe
                summaries = []
                for idx, (recipe_id, recipe_data) in enumerate(batch):
                    cache_file = col_cache_dir / f"{recipe_id}.txt"
                    if cache_file.exists() and not self.force_generate_summaries:
                        summary = cache_file.read_text(encoding='utf-8')
                    else:
                        try:
                            summary = self.summarize_recipe(recipe_data)
                        except Exception as e:
                            print(f"     ⚠️  Summary generation failed for {recipe_id}: {e}")
                            summary = self.optimize_embedding_text(recipe_data, collection_name)
                        # Cache the summary
                        cache_file.write_text(summary or "", encoding='utf-8')
                    summaries.append(summary)

                # Now process each recipe with its summary
                for (recipe_id, recipe_data), summary in zip(batch, summaries):
                    try:
                        # Ensure summary is a non-empty string
                        if not summary:
                            summary = self.optimize_embedding_text(recipe_data, collection_name)
                        # Generate embedding from summary
                        vector = self.embed_text(summary)
                        
                        # Add summary to payload
                        payload = {
                            "recipe_id": int(recipe_id),
                            "title": recipe_data.get('title', ''),
                            "collection": collection_name,
                            "confidence": recipe_data.get('confidence', 0),
                            "image_name": recipe_data.get('image_name', ''),
                            "ingredients_count": len(recipe_data.get('ingredients', [])),
                            "summary": summary
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
                        error_count += 1
                        continue
                
                # Upload batch securely
                if points:
                    try:
                        self.client.upsert(collection_name=collection_name, points=points)
                        processed_count += len(points)
                        print(f"     ✅ Batch {i//batch_size + 1}: {len(points)} recipes uploaded")
                        
                    except Exception as e:
                        print(f"     ❌ Error uploading batch: {e}")
                        error_count += len(points)
            
            processing_stats[collection_name] = {
                "processed": processed_count,
                "errors": error_count,
                "total": len(recipes)
            }
            
            print(f"   🎉 Collection '{collection_name}' complete:")
            print(f"     ✅ Processed: {processed_count}")
            print(f"     ❌ Errors: {error_count}")
            
            total_processed += processed_count
        
        return total_processed, processing_stats
    
    def create_collection_metadata(self, processing_stats):
        """Create secure metadata about collections"""
        metadata = {
            "created_at": pd.Timestamp.now().isoformat(),
            "security_measures": [
                "API keys stored in environment variables only",
                "No hardcoded credentials",
                "Beverage collection excluded as requested",
                "Error handling and validation implemented"
            ],
            "collections": {},
            "processing_stats": processing_stats,
            "total_recipes_processed": sum(stats["processed"] for stats in processing_stats.values())
        }

        # Get collection info from Qdrant, fallback to raw HTTP if client schema mismatch
        for collection_name in SECURE_COLLECTIONS_CONFIG.keys():
            try:
                try:
                    info = self.client.get_collection(collection_name)
                    vectors_count = info.vectors_count
                    points_count = info.points_count
                except ResponseHandlingException:
                    # Fallback to raw HTTP if client schema mismatch
                    resp = requests.get(f"{QDRANT_URL}/collections/{collection_name}")
                    resp.raise_for_status()
                    data = resp.json().get("result", {})
                    vectors_count = data.get("indexed_vectors_count", data.get("vectors_count", 0))
                    points_count = data.get("points_count", 0)

                metadata["collections"][collection_name] = {
                    "vectors_count": vectors_count,
                    "points_count": points_count,
                    "config": SECURE_COLLECTIONS_CONFIG[collection_name],
                    "embedding_strategy": EMBEDDING_STRATEGIES[collection_name]
                }

            except Exception as e:
                metadata["collections"][collection_name] = {"error": str(e)}

        # Save metadata securely
        metadata_file = "secure_collection_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, default=str)

        print(f"💾 Secure metadata saved to {metadata_file}")
        return metadata
    
    def run_secure_pipeline(self):
        """Run the complete secure pipeline"""
        print("🚀 STARTING SECURE MULTI-COLLECTION PIPELINE")
        print("=" * 60)
        print("🔒 Security-first approach with API key protection")
        print("🚫 Beverages collection excluded as requested")
        print("=" * 60)
        
        # Prepare summary cache directory
        Path(SUMMARY_CACHE_DIR).mkdir(parents=True, exist_ok=True)
        # Step 1: Load and filter data
        if not self.load_classified_recipes():
            return False
        
        # Step 2: Initialize embedding model
        if not self.initialize_embedding_model():
            return False
        
        # Step 3: Connect to Qdrant
        if not self.connect_to_qdrant():
            return False

        # Step 3.5: Clear out any old collections
        self.clear_existing_collections()
        
        # Step 4: Create secure collections
        if not self.create_secure_collections():
            return False
        
        # Step 5: Process recipes securely
        total_processed, processing_stats = self.process_collections_securely()
        
        # Step 6: Create metadata
        metadata = self.create_collection_metadata(processing_stats)
        
        print("\n🎉 SECURE PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"📊 Total recipes processed: {total_processed}")
        print(f"📁 Collections created: {len(SECURE_COLLECTIONS_CONFIG)}")
        print(f"🚫 Beverages excluded: ✅")
        print(f"🔒 Security measures: ✅")
        print("🚀 Vector database ready for optimized search!")
        
        return True

def main():
    """Main execution with security checks"""
    print("🔒 SECURE MULTI-COLLECTION VECTOR DATABASE SETUP")
    print("=" * 60)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generate-summaries",
        action="store_true",
        help="Override cached summaries and regenerate all via Gemini"
    )
    args = parser.parse_args()

    loader = SecureMultiCollectionLoader()
    # Honor --generate-summaries flag
    loader.force_generate_summaries = args.generate_summaries
    success = loader.run_secure_pipeline()
    
    if success:
        print("\n✅ Secure multi-collection setup complete!")
        print("🎯 Collections optimized for semantic search performance")
        print("🔒 All security measures implemented")
    else:
        print("\n❌ Pipeline failed. Please check errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())