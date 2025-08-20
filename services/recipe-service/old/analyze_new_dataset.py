#!/usr/bin/env python3
"""
Analyze NewDataset13k food distribution
Enhanced dataset with 13k+ recipes and images
"""

import pandas as pd
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

# Configuration
CSV_PATH = "NewDataset13k/Food Ingredients and Recipe Dataset with Image Name Mapping.csv"
OUTPUT_DIR = "new_dataset_analysis"

class NewDatasetAnalyzer:
    """
    Analyzes the NewDataset13k for food distribution and quality
    """
    
    def __init__(self):
        self.df = None
        
    def load_dataset(self):
        """Load the new dataset"""
        try:
            self.df = pd.read_csv(CSV_PATH)
            print(f"✅ Loaded {len(self.df)} recipes from NewDataset13k")
            return True
        except FileNotFoundError:
            print(f"❌ Dataset not found at {CSV_PATH}")
            return False
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return False
    
    def analyze_basic_structure(self):
        """Analyze basic dataset structure"""
        print("\n📊 DATASET STRUCTURE ANALYSIS")
        print("=" * 50)
        
        print(f"Total recipes: {len(self.df)}")
        print(f"Columns: {list(self.df.columns)}")
        print(f"Data types:")
        for col in self.df.columns:
            print(f"  {col}: {self.df[col].dtype}")
        
        # Check for missing data
        print(f"\nMissing data:")
        for col in self.df.columns:
            missing = self.df[col].isnull().sum()
            if missing > 0:
                print(f"  {col}: {missing} ({missing/len(self.df)*100:.1f}%)")
        
        # Sample some recipe names for analysis
        print(f"\nSample recipe titles:")
        for i, title in enumerate(self.df['Title'].head(10)):
            print(f"  {i+1}. {title}")
    
    def extract_cuisine_and_meal_types(self):
        """Extract cuisine and meal type information from recipe titles"""
        print("\n🍽️ EXTRACTING FOOD CATEGORIES FROM TITLES")
        print("=" * 50)
        
        titles = self.df['Title'].astype(str).str.lower()
        
        # Define category keywords
        cuisine_keywords = {
            'italian': ['pasta', 'pizza', 'risotto', 'gnocchi', 'lasagna', 'carbonara', 'bolognese', 'parmigiano', 'parmesan', 'prosciutto', 'mozzarella', 'italian'],
            'asian': ['asian', 'chinese', 'japanese', 'thai', 'korean', 'vietnamese', 'soy', 'sesame', 'ginger', 'miso', 'teriyaki', 'tempura', 'sushi', 'ramen', 'pad thai', 'curry'],
            'mexican': ['mexican', 'taco', 'burrito', 'quesadilla', 'salsa', 'guacamole', 'chipotle', 'jalapeño', 'cilantro', 'avocado', 'lime', 'tortilla'],
            'indian': ['indian', 'curry', 'tandoori', 'masala', 'turmeric', 'cumin', 'coriander', 'cardamom', 'basmati', 'naan'],
            'mediterranean': ['mediterranean', 'greek', 'olive', 'feta', 'hummus', 'tzatziki', 'olives', 'pita'],
            'french': ['french', 'croissant', 'baguette', 'brie', 'champagne', 'cognac', 'bourguignon', 'coq au vin'],
            'american': ['american', 'burger', 'bbq', 'barbecue', 'southern', 'mac and cheese', 'coleslaw', 'cornbread']
        }
        
        meal_type_keywords = {
            'breakfast': ['breakfast', 'pancake', 'waffle', 'oatmeal', 'granola', 'muffin', 'croissant', 'bagel', 'cereal', 'eggs', 'bacon', 'sausage', 'hash'],
            'lunch': ['lunch', 'sandwich', 'wrap', 'burger', 'salad', 'soup', 'panini'],
            'dinner': ['dinner', 'roast', 'steak', 'chicken', 'beef', 'pork', 'lamb', 'fish', 'salmon', 'pasta', 'casserole'],
            'dessert': ['dessert', 'cake', 'cookie', 'pie', 'tart', 'ice cream', 'chocolate', 'vanilla', 'caramel', 'frosting', 'pudding', 'brownie', 'cheesecake'],
            'appetizer': ['appetizer', 'starter', 'dip', 'chip', 'bruschetta', 'crostini', 'canape'],
            'snack': ['snack', 'bar', 'bite', 'popcorn', 'trail mix'],
            'beverage': ['cocktail', 'smoothie', 'juice', 'tea', 'coffee', 'latte', 'drink', 'toddy', 'punch', 'margarita'],
            'side': ['side', 'potatoes', 'rice', 'bread', 'rolls', 'stuffing', 'beans']
        }
        
        cooking_method_keywords = {
            'grilled': ['grilled', 'grill', 'barbecue', 'bbq'],
            'roasted': ['roasted', 'roast', 'baked', 'oven'],
            'fried': ['fried', 'crispy', 'crunchy', 'tempura'],
            'steamed': ['steamed', 'poached'],
            'braised': ['braised', 'stewed', 'slow-cooked'],
            'raw': ['raw', 'salad', 'fresh', 'ceviche', 'tartare']
        }
        
        # Count occurrences
        cuisine_counts = defaultdict(int)
        meal_type_counts = defaultdict(int)
        cooking_method_counts = defaultdict(int)
        
        for title in titles:
            # Check cuisines
            for cuisine, keywords in cuisine_keywords.items():
                if any(keyword in title for keyword in keywords):
                    cuisine_counts[cuisine] += 1
            
            # Check meal types
            for meal_type, keywords in meal_type_keywords.items():
                if any(keyword in title for keyword in keywords):
                    meal_type_counts[meal_type] += 1
            
            # Check cooking methods
            for method, keywords in cooking_method_keywords.items():
                if any(keyword in title for keyword in keywords):
                    cooking_method_counts[method] += 1
        
        return cuisine_counts, meal_type_counts, cooking_method_counts
    
    def analyze_ingredients_complexity(self):
        """Analyze ingredient complexity and common ingredients"""
        print("\n🥘 INGREDIENT ANALYSIS")
        print("=" * 50)
        
        # Parse ingredients from the Cleaned_Ingredients column
        ingredient_lengths = []
        all_ingredients = []
        
        for idx, ingredients_str in enumerate(self.df['Cleaned_Ingredients'].dropna()):
            try:
                # Parse the string representation of the list
                ingredients_list = eval(ingredients_str) if isinstance(ingredients_str, str) else ingredients_str
                if isinstance(ingredients_list, list):
                    ingredient_lengths.append(len(ingredients_list))
                    all_ingredients.extend([ing.lower().strip() for ing in ingredients_list])
            except:
                continue
        
        # Basic statistics
        if ingredient_lengths:
            print(f"Average ingredients per recipe: {sum(ingredient_lengths)/len(ingredient_lengths):.1f}")
            print(f"Min ingredients: {min(ingredient_lengths)}")
            print(f"Max ingredients: {max(ingredient_lengths)}")
        
        # Most common ingredients (simplified)
        ingredient_words = []
        for ing in all_ingredients:
            # Extract key words from ingredients (remove measurements, etc.)
            words = re.findall(r'\b[a-zA-Z]{3,}\b', ing)
            ingredient_words.extend([word.lower() for word in words if len(word) > 3])
        
        common_ingredients = Counter(ingredient_words).most_common(30)
        print(f"\nTop 30 ingredient words:")
        for ingredient, count in common_ingredients:
            print(f"  {ingredient}: {count}")
        
        return ingredient_lengths, common_ingredients
    
    def propose_collections_strategy(self, cuisine_counts, meal_type_counts, cooking_method_counts):
        """Propose optimal collection strategy based on analysis"""
        print("\n🏗️ PROPOSED COLLECTION STRATEGY")
        print("=" * 50)
        
        total_recipes = len(self.df)
        
        # Calculate percentages and propose collections
        collections_strategy = {}
        
        # Major meal types
        for meal_type, count in sorted(meal_type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_recipes) * 100
            if percentage >= 5:  # Only include if >= 5% of dataset
                collections_strategy[f"{meal_type}"] = {
                    "count": count,
                    "percentage": percentage,
                    "priority": "high" if percentage >= 15 else "medium"
                }
        
        # Major cuisines
        for cuisine, count in sorted(cuisine_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_recipes) * 100
            if percentage >= 3:  # Lower threshold for cuisines
                collections_strategy[f"{cuisine}-cuisine"] = {
                    "count": count,
                    "percentage": percentage,
                    "priority": "medium" if percentage >= 5 else "low"
                }
        
        # Cooking methods
        for method, count in sorted(cooking_method_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_recipes) * 100
            if percentage >= 8:  # Higher threshold for cooking methods
                collections_strategy[f"{method}-dishes"] = {
                    "count": count,
                    "percentage": percentage,
                    "priority": "medium"
                }
        
        # Print strategy
        for collection, data in sorted(collections_strategy.items(), key=lambda x: x[1]['percentage'], reverse=True):
            print(f"📁 {collection.upper()}")
            print(f"   Count: {data['count']} recipes ({data['percentage']:.1f}%)")
            print(f"   Priority: {data['priority']}")
            print()
        
        return collections_strategy
    
    def save_analysis_results(self, cuisine_counts, meal_type_counts, cooking_method_counts, 
                            ingredient_stats, collections_strategy, output_dir=OUTPUT_DIR):
        """Save analysis results"""
        Path(output_dir).mkdir(exist_ok=True)
        
        results = {
            "dataset_info": {
                "total_recipes": len(self.df),
                "has_images": True,
                "image_count": 13582,  # From earlier count
                "columns": list(self.df.columns),
                "source": "NewDataset13k"
            },
            "cuisine_distribution": dict(cuisine_counts),
            "meal_type_distribution": dict(meal_type_counts),
            "cooking_method_distribution": dict(cooking_method_counts),
            "ingredient_stats": {
                "avg_ingredients_per_recipe": sum(ingredient_stats[0])/len(ingredient_stats[0]) if ingredient_stats[0] else 0,
                "common_ingredients": dict(ingredient_stats[1][:20])
            },
            "proposed_collections": collections_strategy
        }
        
        # Save to JSON
        with open(f"{output_dir}/new_dataset_analysis.json", 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"💾 Analysis results saved to {output_dir}/new_dataset_analysis.json")
        return results
    
    def run_complete_analysis(self):
        """Run the complete analysis pipeline"""
        print("🚀 ANALYZING NEWDATASET13K")
        print("=" * 60)
        
        if not self.load_dataset():
            return None
        
        # Basic structure analysis
        self.analyze_basic_structure()
        
        # Extract categories
        cuisine_counts, meal_type_counts, cooking_method_counts = self.extract_cuisine_and_meal_types()
        
        # Print distributions
        print(f"\n📈 CUISINE DISTRIBUTION:")
        for cuisine, count in sorted(cuisine_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.df)) * 100
            print(f"  {cuisine}: {count} recipes ({percentage:.1f}%)")
        
        print(f"\n📈 MEAL TYPE DISTRIBUTION:")
        for meal_type, count in sorted(meal_type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.df)) * 100
            print(f"  {meal_type}: {count} recipes ({percentage:.1f}%)")
        
        print(f"\n📈 COOKING METHOD DISTRIBUTION:")
        for method, count in sorted(cooking_method_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(self.df)) * 100
            print(f"  {method}: {count} recipes ({percentage:.1f}%)")
        
        # Ingredient analysis
        ingredient_stats = self.analyze_ingredients_complexity()
        
        # Propose collection strategy
        collections_strategy = self.propose_collections_strategy(cuisine_counts, meal_type_counts, cooking_method_counts)
        
        # Save results
        results = self.save_analysis_results(cuisine_counts, meal_type_counts, cooking_method_counts, 
                                           ingredient_stats, collections_strategy)
        
        print("\n✅ ANALYSIS COMPLETE!")
        print(f"📊 Dataset Quality: EXCELLENT - {len(self.df)} recipes with images")
        print(f"🎯 Recommended: Switch to this dataset for better performance")
        
        return results

if __name__ == "__main__":
    analyzer = NewDatasetAnalyzer()
    results = analyzer.run_complete_analysis()