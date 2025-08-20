#!/usr/bin/env python3
"""
Function-Based Recipe Classifier for NewDataset13k
Classifies recipes based on ingredients and cooking methods, not cuisine
"""

import pandas as pd
import json
import re
from collections import defaultdict, Counter
from pathlib import Path

class FunctionBasedClassifier:
    """
    Classifies recipes into semantic function-based collections
    """
    
    def __init__(self, csv_path="NewDataset13k/Food Ingredients and Recipe Dataset with Image Name Mapping.csv"):
        self.csv_path = csv_path
        self.df = None
        self.setup_classification_rules()
    
    def setup_classification_rules(self):
        """Define classification rules based on ingredients and methods"""
        
        # Protein indicators (for protein-mains collection)
        self.protein_indicators = {
            'meat': ['beef', 'steak', 'ground beef', 'chuck', 'brisket', 'ribeye', 'sirloin'],
            'poultry': ['chicken', 'turkey', 'duck', 'breast', 'thigh', 'wing', 'drumstick'],
            'pork': ['pork', 'bacon', 'ham', 'sausage', 'prosciutto', 'pancetta', 'chorizo'],
            'seafood': ['fish', 'salmon', 'tuna', 'cod', 'halibut', 'shrimp', 'lobster', 'crab', 'scallops', 'mussels', 'clams', 'oysters'],
            'eggs': ['eggs', 'egg whites', 'egg yolks']
        }
        
        # Plant-based indicators
        self.plant_indicators = [
            'tofu', 'tempeh', 'seitan', 'lentils', 'chickpeas', 'black beans', 'kidney beans', 
            'quinoa', 'bulgur', 'farro', 'barley', 'mushrooms', 'eggplant', 'portobello',
            'nutritional yeast', 'tahini', 'cashews', 'almonds', 'walnuts'
        ]
        
        # Dessert indicators
        self.dessert_indicators = [
            'sugar', 'brown sugar', 'powdered sugar', 'confectioners', 'maple syrup', 'honey',
            'chocolate', 'cocoa', 'vanilla extract', 'frosting', 'icing', 'whipped cream',
            'heavy cream', 'mascarpone', 'cream cheese', 'butter', 'flour', 'baking powder',
            'baking soda', 'cake', 'cookie', 'pie', 'tart', 'brownie', 'muffin', 'cupcake'
        ]
        
        # Breakfast indicators
        self.breakfast_indicators = [
            'oats', 'oatmeal', 'granola', 'cereal', 'pancake', 'waffle', 'syrup', 'maple syrup',
            'bacon', 'sausage', 'eggs', 'egg whites', 'milk', 'yogurt', 'berries', 'banana',
            'coffee', 'espresso', 'breakfast', 'morning', 'brunch'
        ]
        
        # Beverage indicators
        self.beverage_indicators = [
            'vodka', 'gin', 'rum', 'whiskey', 'bourbon', 'tequila', 'wine', 'beer', 'cocktail',
            'juice', 'smoothie', 'shake', 'latte', 'cappuccino', 'tea', 'coffee', 'water',
            'ice cubes', 'simple syrup', 'mixer', 'drink', 'beverage'
        ]
        
        # Cooking method patterns (from instructions)
        self.cooking_methods = {
            'baked': ['bake', 'baking', 'oven', 'preheat', 'degrees', 'baking sheet', 'baking dish'],
            'grilled': ['grill', 'grilling', 'barbecue', 'bbq', 'charcoal', 'gas grill', 'grill pan'],
            'fried': ['fry', 'frying', 'deep fry', 'pan fry', 'sauté', 'oil', 'skillet', 'pan'],
            'raw': ['no cook', 'raw', 'fresh', 'uncooked', 'cold', 'chill', 'refrigerate'],
            'braised': ['braise', 'braising', 'simmer', 'slow cook', 'stew', 'dutch oven', 'pot'],
            'steamed': ['steam', 'steaming', 'steamer', 'steam basket'],
            'roasted': ['roast', 'roasting', 'roast in oven', 'roasting pan']
        }
        
        # Collection scoring weights
        self.collection_weights = {
            'protein-mains': {'protein_score': 3, 'main_dish_score': 2, 'cooking_method_score': 1},
            'plant-based': {'plant_score': 4, 'no_animal_products': 2},
            'desserts-sweets': {'dessert_score': 5, 'sweet_ingredients': 3},
            'fresh-cold': {'raw_method': 4, 'fresh_ingredients': 2, 'salad_indicators': 2},
            'comfort-cooked': {'braised_method': 3, 'comfort_ingredients': 2, 'warm_dish': 1},
            'breakfast-morning': {'breakfast_score': 4, 'morning_ingredients': 3},
            'quick-light': {'quick_method': 3, 'light_ingredients': 2, 'simple_prep': 1},
            'beverages': {'beverage_score': 5, 'liquid_ingredients': 3},
            'baked-breads': {'baked_method': 3, 'bread_ingredients': 4, 'flour_based': 2}
        }
    
    def load_dataset(self):
        """Load the NewDataset13k"""
        try:
            self.df = pd.read_csv(self.csv_path)
            print(f"✅ Loaded {len(self.df)} recipes from NewDataset13k")
            return True
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return False
    
    def parse_ingredients(self, ingredients_str):
        """Parse ingredients string into list"""
        try:
            if pd.isna(ingredients_str):
                return []
            
            # Handle string representation of list
            if ingredients_str.startswith('[') and ingredients_str.endswith(']'):
                ingredients_list = eval(ingredients_str)
            else:
                ingredients_list = [ingredients_str]
            
            # Clean and normalize ingredients
            cleaned_ingredients = []
            for ing in ingredients_list:
                if isinstance(ing, str):
                    # Remove measurements and clean text
                    cleaned = re.sub(r'\d+[\s\w]*(?:cup|tablespoon|teaspoon|ounce|pound|gram|ml|liter)s?', '', ing.lower())
                    cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
                    cleaned = ' '.join(cleaned.split())
                    cleaned_ingredients.append(cleaned)
            
            return cleaned_ingredients
        except:
            return []
    
    def analyze_protein_content(self, ingredients):
        """Analyze protein content in ingredients"""
        protein_score = 0
        protein_types = []
        
        ingredients_text = ' '.join(ingredients).lower()
        
        for protein_type, protein_list in self.protein_indicators.items():
            for protein in protein_list:
                if protein in ingredients_text:
                    protein_score += 1
                    protein_types.append(protein_type)
        
        return protein_score, protein_types
    
    def analyze_plant_content(self, ingredients):
        """Analyze plant-based content"""
        plant_score = 0
        ingredients_text = ' '.join(ingredients).lower()
        
        for plant_item in self.plant_indicators:
            if plant_item in ingredients_text:
                plant_score += 1
        
        return plant_score
    
    def analyze_dessert_content(self, ingredients):
        """Analyze dessert indicators"""
        dessert_score = 0
        ingredients_text = ' '.join(ingredients).lower()
        
        for dessert_item in self.dessert_indicators:
            if dessert_item in ingredients_text:
                dessert_score += 1
        
        return dessert_score
    
    def analyze_breakfast_content(self, ingredients):
        """Analyze breakfast indicators"""
        breakfast_score = 0
        ingredients_text = ' '.join(ingredients).lower()
        
        for breakfast_item in self.breakfast_indicators:
            if breakfast_item in ingredients_text:
                breakfast_score += 1
        
        return breakfast_score
    
    def analyze_beverage_content(self, ingredients):
        """Analyze beverage indicators"""
        beverage_score = 0
        ingredients_text = ' '.join(ingredients).lower()
        
        for beverage_item in self.beverage_indicators:
            if beverage_item in ingredients_text:
                beverage_score += 1
        
        return beverage_score
    
    def analyze_cooking_method(self, instructions):
        """Analyze cooking method from instructions"""
        if pd.isna(instructions):
            return 'unknown', 0
        
        instructions_text = str(instructions).lower()
        method_scores = {}
        
        for method, keywords in self.cooking_methods.items():
            score = 0
            for keyword in keywords:
                score += instructions_text.count(keyword)
            if score > 0:
                method_scores[method] = score
        
        if method_scores:
            best_method = max(method_scores.items(), key=lambda x: x[1])
            return best_method[0], best_method[1]
        else:
            return 'unknown', 0
    
    def classify_recipe(self, row):
        """Classify a single recipe into the best collection"""
        # Parse ingredients
        ingredients = self.parse_ingredients(row.get('Cleaned_Ingredients', ''))
        instructions = row.get('Instructions', '')
        title_raw = row.get('Title', '')
        title = str(title_raw).lower() if pd.notna(title_raw) else ''
        
        # Analyze different aspects
        protein_score, protein_types = self.analyze_protein_content(ingredients)
        plant_score = self.analyze_plant_content(ingredients)
        dessert_score = self.analyze_dessert_content(ingredients)
        breakfast_score = self.analyze_breakfast_content(ingredients)
        beverage_score = self.analyze_beverage_content(ingredients)
        cooking_method, method_score = self.analyze_cooking_method(instructions)
        
        # Score each collection
        collection_scores = {}
        
        # Beverages (highest priority - clear functional boundary)
        if beverage_score >= 2 or any(word in title for word in ['cocktail', 'drink', 'smoothie', 'juice', 'tea', 'coffee']):
            collection_scores['beverages'] = beverage_score * 5 + 10
        
        # Desserts (second highest priority - clear semantic cluster)
        if dessert_score >= 3 or any(word in title for word in ['cake', 'cookie', 'pie', 'dessert', 'sweet']):
            collection_scores['desserts-sweets'] = dessert_score * 3 + 5
        
        # Breakfast (clear time-based semantic cluster)
        if breakfast_score >= 2 or any(word in title for word in ['breakfast', 'morning', 'pancake', 'waffle']):
            collection_scores['breakfast-morning'] = breakfast_score * 3 + 3
        
        # Fresh/Cold (based on cooking method)
        if cooking_method == 'raw' or method_score == 0 or 'salad' in title:
            collection_scores['fresh-cold'] = method_score + 5
        
        # Protein mains (high protein content + cooking method)
        if protein_score >= 2:
            collection_scores['protein-mains'] = protein_score * 2 + method_score
        
        # Plant-based (high plant score + no/low animal products)
        if plant_score >= 2 and protein_score <= 1:
            collection_scores['plant-based'] = plant_score * 3
        
        # Comfort cooked (braised/slow cooking methods)
        if cooking_method in ['braised', 'roasted'] and method_score >= 2:
            collection_scores['comfort-cooked'] = method_score * 2 + 2
        
        # Baked goods (baking method + flour-based)
        if cooking_method == 'baked' and any(ing in ' '.join(ingredients) for ing in ['flour', 'bread', 'dough']):
            collection_scores['baked-breads'] = method_score * 2 + 3
        
        # Quick/Light (simple ingredients + quick methods)
        if len(ingredients) <= 8 or cooking_method == 'fried' or 'quick' in title:
            collection_scores['quick-light'] = 3
        
        # Default to protein-mains if no clear category
        if not collection_scores:
            collection_scores['protein-mains'] = 1
        
        # Return best collection
        best_collection = max(collection_scores.items(), key=lambda x: x[1])
        
        return best_collection[0], best_collection[1], {
            'protein_score': protein_score,
            'plant_score': plant_score,
            'dessert_score': dessert_score,
            'breakfast_score': breakfast_score,
            'beverage_score': beverage_score,
            'cooking_method': cooking_method,
            'method_score': method_score,
            'ingredients_count': len(ingredients)
        }
    
    def classify_all_recipes(self):
        """Classify all recipes in the dataset"""
        print("🔄 Classifying recipes based on ingredients and cooking methods...")
        
        classified_recipes = {}
        collection_stats = defaultdict(int)
        confidence_stats = defaultdict(list)
        
        for idx, row in self.df.iterrows():
            collection, confidence, analysis = self.classify_recipe(row)
            
            recipe_data = {
                'id': idx,
                'title': row.get('Title', ''),
                'collection': collection,
                'confidence': confidence,
                'analysis': analysis,
                'image_name': row.get('Image_Name', ''),
                'ingredients': self.parse_ingredients(row.get('Cleaned_Ingredients', '')),
                'instructions': row.get('Instructions', '')
            }
            
            classified_recipes[idx] = recipe_data
            collection_stats[collection] += 1
            confidence_stats[collection].append(confidence)
            
            if idx % 1000 == 0:
                print(f"  Processed {idx} recipes...")
        
        # Calculate average confidence
        avg_confidence = {}
        for collection, confidences in confidence_stats.items():
            avg_confidence[collection] = sum(confidences) / len(confidences) if confidences else 0
        
        print("✅ Classification complete!")
        return classified_recipes, collection_stats, avg_confidence
    
    def print_classification_summary(self, collection_stats, avg_confidence):
        """Print classification summary"""
        print("\n📊 FUNCTION-BASED CLASSIFICATION SUMMARY")
        print("=" * 60)
        
        total_recipes = sum(collection_stats.values())
        
        for collection in sorted(collection_stats.keys()):
            count = collection_stats[collection]
            percentage = (count / total_recipes) * 100
            confidence = avg_confidence.get(collection, 0)
            
            # Collection emoji mapping
            emojis = {
                'protein-mains': '🥩',
                'plant-based': '🥬', 
                'desserts-sweets': '🍰',
                'fresh-cold': '🥗',
                'comfort-cooked': '🍲',
                'breakfast-morning': '🥞',
                'quick-light': '🥙',
                'beverages': '🍹',
                'baked-breads': '🍞'
            }
            
            emoji = emojis.get(collection, '📁')
            print(f"{emoji} {collection.replace('-', ' ').title()}")
            print(f"   Count: {count} recipes ({percentage:.1f}%)")
            print(f"   Avg Confidence: {confidence:.1f}")
            print()
        
        print(f"📈 Total: {total_recipes} recipes classified")
    
    def save_results(self, classified_recipes, collection_stats, avg_confidence, output_dir="function_classification_results"):
        """Save classification results"""
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save full results
        results_file = f"{output_dir}/function_classified_recipes.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({str(k): v for k, v in classified_recipes.items()}, f, indent=2, default=str)
        
        # Save statistics
        stats_file = f"{output_dir}/function_classification_stats.json"
        stats_data = {
            'collection_counts': dict(collection_stats),
            'average_confidence': dict(avg_confidence),
            'total_recipes': sum(collection_stats.values()),
            'classification_method': 'ingredient_and_method_based'
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2)
        
        # Create collection-specific files
        collections_dir = Path(output_dir) / "collections"
        collections_dir.mkdir(exist_ok=True)
        
        collection_files = defaultdict(list)
        for recipe_data in classified_recipes.values():
            collection = recipe_data['collection']
            collection_files[collection].append(recipe_data)
        
        for collection, recipes in collection_files.items():
            collection_file = collections_dir / f"{collection}_recipes.json"
            with open(collection_file, 'w', encoding='utf-8') as f:
                json.dump(recipes, f, indent=2, default=str)
        
        print(f"💾 Results saved to {output_dir}/")
        return output_dir
    
    def run_classification(self):
        """Run the complete classification pipeline"""
        print("🚀 FUNCTION-BASED RECIPE CLASSIFICATION")
        print("=" * 60)
        
        if not self.load_dataset():
            return None
        
        classified_recipes, collection_stats, avg_confidence = self.classify_all_recipes()
        self.print_classification_summary(collection_stats, avg_confidence)
        output_dir = self.save_results(classified_recipes, collection_stats, avg_confidence)
        
        print(f"\n✅ Function-based classification complete!")
        print(f"🎯 Collections optimized for semantic similarity and user intent")
        
        return {
            'classified_recipes': classified_recipes,
            'collection_stats': collection_stats,
            'avg_confidence': avg_confidence,
            'output_dir': output_dir
        }

if __name__ == "__main__":
    classifier = FunctionBasedClassifier()
    results = classifier.run_classification()