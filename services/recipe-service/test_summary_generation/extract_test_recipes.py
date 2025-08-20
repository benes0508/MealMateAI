#!/usr/bin/env python3
"""
Extract 50 recipes for testing batch summary generation
"""

import json
import random
from pathlib import Path

# Configuration
SOURCE_FILE = "../function_classification_results/function_classified_recipes.json"
OUTPUT_FILE = "test_classified_recipes.json"
NUM_RECIPES = 50

def extract_test_recipes():
    """Extract a representative sample of recipes for testing"""
    
    print("📂 Loading full recipe dataset...")
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        all_recipes = json.load(f)
    
    print(f"✅ Loaded {len(all_recipes)} total recipes")
    
    # Group by collection to get diverse sample
    recipes_by_collection = {}
    for recipe_id, recipe_data in all_recipes.items():
        collection = recipe_data.get('collection')
        if collection not in recipes_by_collection:
            recipes_by_collection[collection] = []
        recipes_by_collection[collection].append((recipe_id, recipe_data))
    
    print("📊 Recipes by collection:")
    for collection, recipes in recipes_by_collection.items():
        print(f"   {collection}: {len(recipes)} recipes")
    
    # Sample recipes from each collection proportionally
    test_recipes = {}
    recipes_per_collection = max(1, NUM_RECIPES // len(recipes_by_collection))
    
    for collection, recipes in recipes_by_collection.items():
        # Sample from this collection
        sample_size = min(recipes_per_collection, len(recipes))
        sampled = random.sample(recipes, sample_size)
        
        for recipe_id, recipe_data in sampled:
            test_recipes[recipe_id] = recipe_data
        
        print(f"   ✅ Sampled {sample_size} recipes from {collection}")
    
    # If we need more recipes, fill up from largest collections
    if len(test_recipes) < NUM_RECIPES:
        remaining_needed = NUM_RECIPES - len(test_recipes)
        
        # Get all remaining recipes not yet selected
        remaining_recipes = []
        for recipe_id, recipe_data in all_recipes.items():
            if recipe_id not in test_recipes:
                remaining_recipes.append((recipe_id, recipe_data))
        
        # Randomly sample the remaining
        additional = random.sample(remaining_recipes, min(remaining_needed, len(remaining_recipes)))
        
        for recipe_id, recipe_data in additional:
            test_recipes[recipe_id] = recipe_data
        
        print(f"   ✅ Added {len(additional)} additional recipes")
    
    # Save test dataset
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_recipes, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎉 Test dataset created!")
    print(f"📁 Output file: {OUTPUT_FILE}")
    print(f"📊 Total test recipes: {len(test_recipes)}")
    
    # Show final distribution
    test_by_collection = {}
    for recipe_data in test_recipes.values():
        collection = recipe_data.get('collection')
        test_by_collection[collection] = test_by_collection.get(collection, 0) + 1
    
    print("\n📊 Test dataset distribution:")
    for collection, count in sorted(test_by_collection.items()):
        print(f"   {collection}: {count} recipes")
    
    return True

if __name__ == "__main__":
    # Set random seed for reproducible results
    random.seed(42)
    
    print("🧪 CREATING TEST DATASET FOR SUMMARY GENERATION")
    print("=" * 60)
    
    extract_test_recipes()
    
    print("\n✅ Test dataset ready!")
    print("💡 Run test_summary_generation.py to test batch processing")