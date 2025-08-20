#!/usr/bin/env python3
"""
Analyze cuisine_path distribution in Kaggle recipes dataset
to determine optimal collection organization strategy
"""

import pandas as pd
import json
from collections import Counter, defaultdict
import re
from pathlib import Path

# Configuration
CSV_PATH = "kaggleRecipes/recipes.csv"
OUTPUT_DIR = "cuisine_analysis"

def clean_cuisine_path(cuisine_path):
    """Clean and normalize cuisine path strings"""
    if pd.isna(cuisine_path) or cuisine_path == "":
        return "uncategorized"
    
    # Remove leading/trailing slashes and convert to lowercase
    cleaned = str(cuisine_path).strip("/").lower()
    return cleaned

def extract_cuisine_categories(cuisine_path):
    """Extract meaningful cuisine categories from path"""
    if not cuisine_path or cuisine_path == "uncategorized":
        return ["uncategorized"]
    
    # Split by forward slashes and clean up
    parts = [part.strip() for part in cuisine_path.split("/") if part.strip()]
    
    # Common cuisine patterns to look for
    cuisine_keywords = {
        "italian": ["italian", "italy", "pasta", "pizza", "risotto"],
        "asian": ["asian", "chinese", "japanese", "thai", "korean", "vietnamese"],
        "indian": ["indian", "india", "curry"],
        "mexican": ["mexican", "mexico", "tex-mex", "latin"],
        "american": ["american", "usa", "southern", "bbq", "comfort"],
        "french": ["french", "france"],
        "mediterranean": ["mediterranean", "greek", "middle eastern"],
        "desserts": ["desserts", "dessert", "sweet", "cake", "cookie", "pie"],
        "healthy": ["healthy", "diet", "low-fat", "vegetarian", "vegan"],
        "breakfast": ["breakfast", "brunch"],
        "appetizers": ["appetizers", "snacks", "finger food"],
        "soups": ["soups", "soup", "stew"],
        "salads": ["salads", "salad"],
        "seafood": ["seafood", "fish", "salmon", "shrimp"],
        "chicken": ["chicken", "poultry"],
        "beef": ["beef", "steak"],
        "pork": ["pork", "ham", "bacon"],
    }
    
    categories = []
    path_text = " ".join(parts).lower()
    
    for category, keywords in cuisine_keywords.items():
        if any(keyword in path_text for keyword in keywords):
            categories.append(category)
    
    # If no specific categories found, use the first part as category
    if not categories:
        categories.append(parts[0] if parts else "uncategorized")
    
    return categories

def analyze_dataset():
    """Analyze the Kaggle recipes dataset for cuisine distribution"""
    print("🔄 Loading dataset...")
    
    try:
        df = pd.read_csv(CSV_PATH)
        print(f"✅ Loaded {len(df)} recipes from dataset")
    except FileNotFoundError:
        print(f"❌ Dataset not found at {CSV_PATH}")
        return
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        return
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    
    print("\n📊 Analyzing cuisine paths...")
    
    # Clean cuisine paths
    df['cleaned_cuisine_path'] = df['cuisine_path'].apply(clean_cuisine_path)
    
    # Extract categories
    df['cuisine_categories'] = df['cleaned_cuisine_path'].apply(extract_cuisine_categories)
    
    # Analysis 1: Raw cuisine path distribution
    cuisine_path_counts = df['cleaned_cuisine_path'].value_counts()
    print(f"\n📈 Top 20 raw cuisine paths:")
    print(cuisine_path_counts.head(20))
    
    # Analysis 2: Category distribution
    all_categories = []
    for categories in df['cuisine_categories']:
        all_categories.extend(categories)
    
    category_counts = Counter(all_categories)
    print(f"\n📈 Cuisine category distribution:")
    for category, count in category_counts.most_common(20):
        print(f"  {category}: {count}")
    
    # Analysis 3: Recipe distribution per proposed collection
    collection_mapping = {
        "italian-mediterranean": ["italian", "mediterranean", "french"],
        "asian-pacific": ["asian", "indian"],
        "american-comfort": ["american", "mexican"],
        "healthy-light": ["healthy", "salads", "seafood"],
        "baking-desserts": ["desserts"],
        "breakfast-brunch": ["breakfast"],
        "soups-stews": ["soups"],
        "appetizers-snacks": ["appetizers"],
        "meat-mains": ["chicken", "beef", "pork"],
        "uncategorized": ["uncategorized"]
    }
    
    # Map recipes to proposed collections
    recipe_collections = defaultdict(list)
    collection_stats = defaultdict(int)
    
    for idx, categories in enumerate(df['cuisine_categories']):
        recipe_assigned = False
        recipe_name = df.iloc[idx]['recipe_name']
        
        for collection, collection_categories in collection_mapping.items():
            if any(cat in categories for cat in collection_categories):
                recipe_collections[collection].append({
                    'name': recipe_name,
                    'categories': categories,
                    'original_path': df.iloc[idx]['cuisine_path']
                })
                collection_stats[collection] += 1
                recipe_assigned = True
                break
        
        if not recipe_assigned:
            recipe_collections['uncategorized'].append({
                'name': recipe_name,
                'categories': categories,
                'original_path': df.iloc[idx]['cuisine_path']
            })
            collection_stats['uncategorized'] += 1
    
    print(f"\n📊 Proposed collection distribution:")
    total_recipes = sum(collection_stats.values())
    for collection, count in sorted(collection_stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_recipes) * 100
        print(f"  {collection}: {count} recipes ({percentage:.1f}%)")
    
    # Save detailed analysis - convert numpy types to native Python types
    analysis_results = {
        "total_recipes": int(len(df)),
        "raw_cuisine_paths": {k: int(v) for k, v in dict(cuisine_path_counts.head(50)).items()},
        "category_distribution": {k: int(v) for k, v in dict(category_counts.most_common(30)).items()},
        "proposed_collections": {k: int(v) for k, v in dict(collection_stats).items()},
        "collection_samples": {
            collection: recipes[:5]  # First 5 recipes as samples
            for collection, recipes in recipe_collections.items()
        }
    }
    
    output_file = f"{OUTPUT_DIR}/cuisine_analysis.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed analysis saved to {output_file}")
    
    # Generate collection mapping file
    mapping_file = f"{OUTPUT_DIR}/collection_mapping.json"
    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(collection_mapping, f, indent=2)
    
    print(f"💾 Collection mapping saved to {mapping_file}")
    
    # Sample some recipes for manual inspection
    sample_file = f"{OUTPUT_DIR}/sample_recipes.json"
    sample_recipes = []
    for collection, recipes in recipe_collections.items():
        if recipes:
            sample_recipes.extend([
                {
                    "collection": collection,
                    "recipe": recipe
                }
                for recipe in recipes[:3]  # Top 3 from each collection
            ])
    
    with open(sample_file, 'w', encoding='utf-8') as f:
        json.dump(sample_recipes, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Sample recipes saved to {sample_file}")
    
    return analysis_results

if __name__ == "__main__":
    results = analyze_dataset()
    if results:
        print("\n✅ Analysis complete! Check the output files for detailed results.")
        print(f"📁 Results saved in: {OUTPUT_DIR}/")