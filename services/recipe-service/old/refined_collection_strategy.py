#!/usr/bin/env python3
"""
Refined collection strategy based on actual data analysis
Focusing on recipe function rather than cuisine for better performance
"""

# Revised collection mapping based on actual data distribution
COLLECTION_STRATEGY = {
    "desserts-sweets": {
        "description": "All sweet treats, baked goods, and desserts",
        "keywords": ["desserts", "dessert", "sweet", "cake", "cookie", "pie", "tart", "pastry", "candy"],
        "expected_size": "~400 recipes (36.5%)",
        "search_optimization": "Optimized for ingredient-based search (chocolate, vanilla, fruit types)"
    },
    
    "sides-sauces": {
        "description": "Side dishes, sauces, condiments, and accompaniments", 
        "keywords": ["side dish", "sauces", "condiments", "dressing", "marinade", "jam", "jelly", "chutney"],
        "expected_size": "~111 recipes (10.2%)",
        "search_optimization": "Focus on main ingredient and dietary compatibility"
    },
    
    "salads-fresh": {
        "description": "Fresh salads, fruit salads, and raw preparations",
        "keywords": ["salad", "fresh", "raw", "fruit salad", "green", "spinach"],
        "expected_size": "~103 recipes (9.4%)",
        "search_optimization": "Seasonal ingredients and dietary restrictions focus"
    },
    
    "drinks-beverages": {
        "description": "All beverages, smoothies, juices, and liquid recipes",
        "keywords": ["drinks", "smoothie", "juice", "beverage", "cocktail", "tea", "coffee"],
        "expected_size": "~82 recipes (7.5%)",
        "search_optimization": "Flavor profiles and occasion-based search"
    },
    
    "appetizers-snacks": {
        "description": "Appetizers, finger foods, and snack recipes",
        "keywords": ["appetizers", "snacks", "finger", "dips", "spreads", "party"],
        "expected_size": "~70 recipes (6.4%)", 
        "search_optimization": "Serving size and occasion-based clustering"
    },
    
    "breads-baked": {
        "description": "Breads, muffins, and non-sweet baked goods",
        "keywords": ["bread", "muffin", "biscuit", "roll", "bagel", "pizza dough"],
        "expected_size": "~67 recipes (6.1%)",
        "search_optimization": "Baking method and grain type focus"
    },
    
    "meat-mains": {
        "description": "Main dishes featuring meat, poultry, or seafood",
        "keywords": ["chicken", "beef", "pork", "seafood", "fish", "meat", "poultry", "main dish"],
        "expected_size": "~92 recipes (8.4%)",
        "search_optimization": "Protein type and cooking method clustering"
    },
    
    "breakfast-brunch": {
        "description": "Morning meals and brunch items",
        "keywords": ["breakfast", "brunch", "pancake", "waffle", "eggs", "cereal", "oatmeal"],
        "expected_size": "~49 recipes (4.5%)",
        "search_optimization": "Time-of-day and dietary preference focus"
    },
    
    "soups-stews": {
        "description": "Liquid-based main dishes and comfort foods",
        "keywords": ["soup", "stew", "chili", "broth", "bisque", "chowder"],
        "expected_size": "~21 recipes (1.9%)",
        "search_optimization": "Comfort food and dietary restriction focus"
    },
    
    "international": {
        "description": "Recipes with clear international/ethnic origins",
        "keywords": ["mexican", "italian", "asian", "french", "indian", "mediterranean", "cuisine"],
        "expected_size": "~58 recipes (5.3%)",
        "search_optimization": "Authentic ingredients and regional preferences"
    }
}

# Embedding optimization strategy per collection
EMBEDDING_STRATEGIES = {
    "desserts-sweets": {
        "focus_fields": ["recipe_name", "main_ingredients", "sweetness_level", "texture"],
        "exclude_fields": ["detailed_directions", "exact_measurements"],
        "enhance_with": ["dessert_type", "occasion", "dietary_tags"]
    },
    
    "sides-sauces": {
        "focus_fields": ["recipe_name", "base_ingredients", "flavor_profile"],
        "exclude_fields": ["lengthy_directions", "storage_instructions"],
        "enhance_with": ["pairing_suggestions", "dietary_compatibility"]
    },
    
    "salads-fresh": {
        "focus_fields": ["recipe_name", "fresh_ingredients", "dressing_type"],
        "exclude_fields": ["prep_timing", "storage_details"],
        "enhance_with": ["seasonal_tags", "nutritional_highlights"]
    },
    
    "drinks-beverages": {
        "focus_fields": ["recipe_name", "flavor_ingredients", "drink_type"],
        "exclude_fields": ["equipment_details", "serving_suggestions"],
        "enhance_with": ["occasion_tags", "alcoholic_nonalcoholic"]
    },
    
    "appetizers-snacks": {
        "focus_fields": ["recipe_name", "key_ingredients", "serving_style"],
        "exclude_fields": ["detailed_plating", "party_planning"],
        "enhance_with": ["party_size", "dietary_restrictions"]
    },
    
    "breads-baked": {
        "focus_fields": ["recipe_name", "flour_type", "baking_method"],
        "exclude_fields": ["exact_timing", "troubleshooting"],
        "enhance_with": ["bread_type", "texture_preferences"]
    },
    
    "meat-mains": {
        "focus_fields": ["recipe_name", "protein_type", "cooking_method", "seasonings"],
        "exclude_fields": ["temperature_details", "food_safety"],
        "enhance_with": ["protein_cut", "cooking_difficulty"]
    },
    
    "breakfast-brunch": {
        "focus_fields": ["recipe_name", "morning_ingredients", "meal_type"],
        "exclude_fields": ["nutritional_breakdown", "meal_prep"],
        "enhance_with": ["time_of_day", "weekend_weekday"]
    },
    
    "soups-stews": {
        "focus_fields": ["recipe_name", "broth_base", "main_ingredients", "comfort_level"],
        "exclude_fields": ["exact_simmering_times", "storage"],
        "enhance_with": ["season_preference", "heartiness_level"]
    },
    
    "international": {
        "focus_fields": ["recipe_name", "authentic_ingredients", "region", "cooking_technique"],
        "exclude_fields": ["cultural_background", "history"],
        "enhance_with": ["authenticity_level", "spice_tolerance"]
    }
}

# Query routing logic
QUERY_ROUTING_KEYWORDS = {
    "desserts-sweets": ["sweet", "dessert", "cake", "cookie", "chocolate", "sugar", "frosting", "bake"],
    "sides-sauces": ["sauce", "side", "dressing", "marinade", "condiment", "accompaniment"],
    "salads-fresh": ["salad", "fresh", "raw", "lettuce", "greens", "vinaigrette"],
    "drinks-beverages": ["drink", "smoothie", "juice", "beverage", "shake", "cocktail"],
    "appetizers-snacks": ["appetizer", "snack", "finger food", "party", "dip", "chips"],
    "breads-baked": ["bread", "muffin", "biscuit", "dough", "yeast", "flour"],
    "meat-mains": ["chicken", "beef", "pork", "fish", "meat", "protein", "main course"],
    "breakfast-brunch": ["breakfast", "brunch", "morning", "pancake", "eggs", "oatmeal"],
    "soups-stews": ["soup", "stew", "broth", "chili", "liquid", "warm"],
    "international": ["mexican", "italian", "asian", "indian", "french", "ethnic", "traditional"]
}

def get_collection_for_recipe(recipe_categories, recipe_name="", cuisine_path=""):
    """
    Determine the best collection for a recipe based on its characteristics
    """
    recipe_text = f"{recipe_name} {' '.join(recipe_categories)} {cuisine_path}".lower()
    
    # Score each collection based on keyword matches
    collection_scores = {}
    
    for collection, keywords in QUERY_ROUTING_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in recipe_text)
        if score > 0:
            collection_scores[collection] = score
    
    # Return the collection with the highest score, or "international" as fallback
    if collection_scores:
        return max(collection_scores.items(), key=lambda x: x[1])[0]
    else:
        return "international"  # fallback for uncategorized

def get_embedding_strategy(collection_name):
    """
    Get the embedding optimization strategy for a specific collection
    """
    return EMBEDDING_STRATEGIES.get(collection_name, EMBEDDING_STRATEGIES["international"])

# Performance expectations
PERFORMANCE_EXPECTATIONS = {
    "search_speed_improvement": "3-5x faster due to smaller collection sizes",
    "relevance_improvement": "Higher precision due to semantic clustering within categories",
    "scalability": "Easy to add new collections or rebalance existing ones",
    "memory_efficiency": "Better vector caching and loading patterns"
}

if __name__ == "__main__":
    print("🏗️  Refined Collection Strategy")
    print("=" * 50)
    
    total_estimated = 0
    for collection, config in COLLECTION_STRATEGY.items():
        size_str = config["expected_size"]
        # Extract number from size string for total calculation
        import re
        size_match = re.search(r'~(\d+)', size_str)
        if size_match:
            total_estimated += int(size_match.group(1))
        
        print(f"\n📁 {collection.upper()}")
        print(f"   Description: {config['description']}")
        print(f"   Expected size: {config['expected_size']}")
        print(f"   Keywords: {', '.join(config['keywords'][:5])}...")
    
    print(f"\n📊 Total estimated coverage: ~{total_estimated} recipes")
    print(f"📈 Expected performance improvements:")
    for key, value in PERFORMANCE_EXPECTATIONS.items():
        print(f"   • {key.replace('_', ' ').title()}: {value}")