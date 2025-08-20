#!/usr/bin/env python3
"""
Automated Recipe Classifier
Classifies recipes into optimized collections based on content analysis
"""

import pandas as pd
import json
import re
from pathlib import Path
from collections import defaultdict
from refined_collection_strategy import QUERY_ROUTING_KEYWORDS, get_collection_for_recipe

class RecipeClassifier:
    """
    Classifies recipes into optimal collections for vector database organization
    """
    
    def __init__(self, csv_path="kaggleRecipes/recipes.csv"):
        self.csv_path = csv_path
        self.collection_keywords = QUERY_ROUTING_KEYWORDS
        
    def load_recipes(self):
        """Load recipes from CSV file"""
        try:
            df = pd.read_csv(self.csv_path)
            print(f"✅ Loaded {len(df)} recipes from {self.csv_path}")
            return df
        except FileNotFoundError:
            print(f"❌ Dataset not found at {self.csv_path}")
            return None
        except Exception as e:
            print(f"❌ Error loading dataset: {e}")
            return None
    
    def extract_recipe_features(self, row):
        """
        Extract key features from a recipe for classification
        """
        features = {
            'name': str(row.get('recipe_name', '')).lower(),
            'ingredients': str(row.get('ingredients', '')).lower(),
            'directions': str(row.get('directions', '')).lower(),
            'cuisine_path': str(row.get('cuisine_path', '')).lower(),
            'timing': str(row.get('timing', '')).lower(),
            'nutrition': str(row.get('nutrition', '')).lower()
        }
        
        # Create combined text for keyword matching
        features['combined_text'] = ' '.join([
            features['name'],
            features['ingredients'][:200],  # Limit to avoid noise
            features['cuisine_path'],
            features['timing']
        ])
        
        return features
    
    def classify_recipe_by_keywords(self, features):
        """
        Classify recipe based on keyword matching with scoring
        """
        combined_text = features['combined_text']
        collection_scores = defaultdict(int)
        
        # Score each collection based on keyword matches
        for collection, keywords in self.collection_keywords.items():
            for keyword in keywords:
                # Count occurrences of each keyword
                matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', combined_text))
                collection_scores[collection] += matches
        
        # Special rules for better classification
        
        # Dessert detection (high priority)
        dessert_indicators = ['sweet', 'sugar', 'dessert', 'cake', 'cookie', 'pie', 'chocolate', 'vanilla', 'frosting', 'icing']
        dessert_score = sum(1 for indicator in dessert_indicators if indicator in combined_text)
        if dessert_score > 0:
            collection_scores['desserts-sweets'] += dessert_score * 2  # Boost dessert score
        
        # Breakfast detection
        breakfast_indicators = ['breakfast', 'morning', 'pancake', 'waffle', 'eggs', 'oatmeal', 'cereal']
        breakfast_score = sum(1 for indicator in breakfast_indicators if indicator in combined_text)
        if breakfast_score > 0:
            collection_scores['breakfast-brunch'] += breakfast_score * 2
        
        # Meat main dish detection
        meat_indicators = ['chicken', 'beef', 'pork', 'fish', 'salmon', 'steak', 'meat', 'protein']
        meat_score = sum(1 for indicator in meat_indicators if indicator in combined_text)
        if meat_score > 0 and 'main' in combined_text:
            collection_scores['meat-mains'] += meat_score * 2
        
        # Soup detection
        soup_indicators = ['soup', 'stew', 'broth', 'chili', 'bisque', 'chowder']
        soup_score = sum(1 for indicator in soup_indicators if indicator in combined_text)
        if soup_score > 0:
            collection_scores['soups-stews'] += soup_score * 2
        
        # Return the collection with the highest score
        if collection_scores:
            best_collection = max(collection_scores.items(), key=lambda x: x[1])
            return best_collection[0], best_collection[1]
        else:
            return 'international', 0  # fallback
    
    def classify_recipe_advanced(self, features):
        """
        Advanced classification using multiple signals
        """
        # Start with keyword-based classification
        primary_collection, confidence = self.classify_recipe_by_keywords(features)
        
        # Additional classification logic based on patterns
        
        # Check for specific cuisine paths
        cuisine_path = features['cuisine_path']
        if 'dessert' in cuisine_path or 'sweet' in cuisine_path:
            return 'desserts-sweets', confidence + 10
        elif 'appetizer' in cuisine_path or 'snack' in cuisine_path:
            return 'appetizers-snacks', confidence + 5
        elif 'salad' in cuisine_path:
            return 'salads-fresh', confidence + 5
        elif 'bread' in cuisine_path or 'muffin' in cuisine_path:
            return 'breads-baked', confidence + 5
        elif 'drink' in cuisine_path or 'beverage' in cuisine_path:
            return 'drinks-beverages', confidence + 5
        elif 'sauce' in cuisine_path or 'side' in cuisine_path:
            return 'sides-sauces', confidence + 5
        
        # Check ingredients for additional context
        ingredients = features['ingredients']
        if any(sweet in ingredients for sweet in ['sugar', 'honey', 'maple syrup', 'chocolate']):
            if primary_collection == 'international':
                return 'desserts-sweets', confidence + 3
        
        # Check name patterns
        name = features['name']
        if any(drink_word in name for drink_word in ['smoothie', 'juice', 'cocktail', 'shake']):
            return 'drinks-beverages', confidence + 8
        
        return primary_collection, confidence
    
    def classify_all_recipes(self, df):
        """
        Classify all recipes in the dataframe
        """
        print("🔄 Classifying recipes...")
        
        classified_recipes = {}
        classification_stats = defaultdict(int)
        confidence_stats = defaultdict(list)
        
        for idx, row in df.iterrows():
            # Extract features
            features = self.extract_recipe_features(row)
            
            # Classify recipe
            collection, confidence = self.classify_recipe_advanced(features)
            
            # Store classification
            recipe_data = {
                'id': idx,
                'name': row.get('recipe_name', ''),
                'collection': collection,
                'confidence': confidence,
                'features': features,
                'original_data': {
                    'cuisine_path': row.get('cuisine_path', ''),
                    'ingredients': row.get('ingredients', ''),
                    'prep_time': row.get('prep_time', ''),
                    'cook_time': row.get('cook_time', ''),
                    'servings': row.get('servings', '')
                }
            }
            
            classified_recipes[idx] = recipe_data
            classification_stats[collection] += 1
            confidence_stats[collection].append(confidence)
        
        # Calculate average confidence per collection
        avg_confidence = {}
        for collection, confidences in confidence_stats.items():
            avg_confidence[collection] = sum(confidences) / len(confidences) if confidences else 0
        
        print("✅ Classification complete!")
        
        return classified_recipes, classification_stats, avg_confidence
    
    def save_classification_results(self, classified_recipes, classification_stats, avg_confidence, output_dir="classification_results"):
        """
        Save classification results to files
        """
        Path(output_dir).mkdir(exist_ok=True)
        
        # Save full classification results
        results_file = f"{output_dir}/classified_recipes.json"
        # Convert numpy types and handle serialization
        serializable_recipes = {}
        for recipe_id, recipe_data in classified_recipes.items():
            serializable_recipes[str(recipe_id)] = {
                **recipe_data,
                'confidence': int(recipe_data['confidence']) if recipe_data['confidence'] else 0
            }
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_recipes, f, indent=2, ensure_ascii=False)
        
        # Save statistics
        stats_file = f"{output_dir}/classification_stats.json"
        stats_data = {
            'collection_counts': {k: int(v) for k, v in classification_stats.items()},
            'average_confidence': {k: float(v) for k, v in avg_confidence.items()},
            'total_recipes': sum(classification_stats.values())
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, indent=2)
        
        # Create collection-specific files for vector DB loading
        collections_dir = Path(output_dir) / "collections"
        collections_dir.mkdir(exist_ok=True)
        
        collection_files = defaultdict(list)
        for recipe_data in classified_recipes.values():
            collection = recipe_data['collection']
            collection_files[collection].append(recipe_data)
        
        for collection, recipes in collection_files.items():
            collection_file = collections_dir / f"{collection}_recipes.json"
            with open(collection_file, 'w', encoding='utf-8') as f:
                json.dump(recipes, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Classification results saved to {output_dir}/")
        print(f"📁 Collection-specific files saved to {collections_dir}/")
        
        return output_dir
    
    def print_classification_summary(self, classification_stats, avg_confidence):
        """
        Print a summary of classification results
        """
        print("\n📊 CLASSIFICATION SUMMARY")
        print("=" * 50)
        
        total_recipes = sum(classification_stats.values())
        
        for collection in sorted(classification_stats.keys()):
            count = classification_stats[collection]
            percentage = (count / total_recipes) * 100
            confidence = avg_confidence.get(collection, 0)
            
            print(f"📁 {collection.replace('-', ' ').title()}")
            print(f"   Count: {count} recipes ({percentage:.1f}%)")
            print(f"   Avg Confidence: {confidence:.1f}")
            print()
        
        print(f"📈 Total: {total_recipes} recipes classified")
    
    def run_classification(self):
        """
        Run the complete classification pipeline
        """
        print("🚀 Starting Recipe Classification Pipeline")
        print("=" * 50)
        
        # Load recipes
        df = self.load_recipes()
        if df is None:
            return None
        
        # Classify recipes
        classified_recipes, classification_stats, avg_confidence = self.classify_all_recipes(df)
        
        # Print summary
        self.print_classification_summary(classification_stats, avg_confidence)
        
        # Save results
        output_dir = self.save_classification_results(classified_recipes, classification_stats, avg_confidence)
        
        return {
            'classified_recipes': classified_recipes,
            'classification_stats': classification_stats,
            'avg_confidence': avg_confidence,
            'output_dir': output_dir
        }

if __name__ == "__main__":
    classifier = RecipeClassifier()
    results = classifier.run_classification()
    
    if results:
        print("\n✅ Classification pipeline completed successfully!")
        print(f"📊 Results available in: {results['output_dir']}")
    else:
        print("\n❌ Classification pipeline failed!")