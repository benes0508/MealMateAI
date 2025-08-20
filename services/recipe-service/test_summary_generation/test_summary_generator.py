#!/usr/bin/env python3
"""
Test Summary Generator - Modified version for testing
"""

import os
import json
import sys
from pathlib import Path
from collections import defaultdict

# Add parent directory to path to import from generate_missing_summaries
sys.path.append(str(Path(__file__).parent.parent))
from generate_missing_summaries import check_api_security

# Security check before imports
if not check_api_security():
    print("❌ Security check failed. Please configure API keys properly.")
    sys.exit(1)

from google import genai

# Configuration for testing
CLASSIFICATION_RESULTS_PATH = "test_classified_recipes.json"
SUMMARY_CACHE_DIR = "test_recipe_summaries"

# Test collections (excluding beverages as requested in original)
TEST_COLLECTIONS_CONFIG = {
    "desserts-sweets": {"batch_size": 5, "estimated_count": 7},
    "protein-mains": {"batch_size": 5, "estimated_count": 5}, 
    "quick-light": {"batch_size": 5, "estimated_count": 5},
    "fresh-cold": {"batch_size": 5, "estimated_count": 6},
    "baked-breads": {"batch_size": 5, "estimated_count": 5},
    "comfort-cooked": {"batch_size": 5, "estimated_count": 5},
    "breakfast-morning": {"batch_size": 5, "estimated_count": 6},
    "plant-based": {"batch_size": 5, "estimated_count": 5}
}

class TestSummaryGenerator:
    """
    Test version of the summary generator
    """
    
    def __init__(self):
        self.genai_client = genai.Client()
        self.classified_recipes = None
        print("✅ Gemini GenAI client initialized for testing")
    
    def load_classified_recipes(self):
        """Load test classified recipes"""
        print(f"📂 Loading test recipes from {CLASSIFICATION_RESULTS_PATH}...")
        
        try:
            with open(CLASSIFICATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
                self.classified_recipes = json.load(f)
            
            print(f"✅ Loaded {len(self.classified_recipes)} test recipes")
            return True
            
        except FileNotFoundError:
            print(f"❌ Test data not found at {CLASSIFICATION_RESULTS_PATH}")
            return False
        except Exception as e:
            print(f"❌ Error loading test data: {e}")
            return False
    
    def summarize_recipes_batch(self, recipes_data):
        """Generate summaries for a batch of recipes using Gemini"""
        context = (
            "You are helping build MealMateAI, a semantic search service "
            "over multiple recipe collections. "
            "Embedding model used for indexing: all-mpnet-base-v2.\\n\\n"
            "Please provide a concise summary for each of the following recipes. "
            "Format your response as a numbered list with one summary per recipe, "
            "in the same order as provided:\\n\\n"
        )
        
        # Build the batch prompt with all recipes
        recipe_texts = []
        for i, recipe_data in enumerate(recipes_data, 1):
            blocks = [f"Recipe {i}: {recipe_data.get('title', '')}"]
            ingredients = recipe_data.get("ingredients", [])
            if ingredients:
                # Limit ingredients to avoid token limits in test
                ingredient_text = ", ".join(ingredients[:10])
                if len(ingredients) > 10:
                    ingredient_text += "..."
                blocks.append("Ingredients: " + ingredient_text)
            if "instructions" in recipe_data:
                # Limit instructions length
                instructions = recipe_data.get("instructions", "")
                if len(instructions) > 500:
                    instructions = instructions[:500] + "..."
                blocks.append("Instructions: " + instructions)
            
            recipe_text = "\\n".join(blocks)
            recipe_texts.append(recipe_text)
        
        # Combine all recipes into one prompt
        full_prompt = context + "\\n\\n".join(recipe_texts)
        
        try:
            response = self.genai_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[full_prompt]
            )
            
            # Extract response text
            response_text = ""
            if hasattr(response, "text"):
                response_text = response.text
            else:
                candidates = getattr(response, "candidates", [])
                if candidates:
                    content = getattr(candidates[0], "content", None)
                    if content and hasattr(content, "text"):
                        response_text = content.text
            
            if not response_text:
                return [""] * len(recipes_data)
            
            # Parse the numbered response into individual summaries
            summaries = self.parse_batch_response(response_text, len(recipes_data))
            return summaries
            
        except Exception as e:
            print(f"     ❌ Batch API call failed: {e}")
            return [""] * len(recipes_data)
    
    def parse_batch_response(self, response_text, expected_count):
        """Parse numbered response into individual summaries"""
        summaries = []
        
        # Use regex to split by numbered items (1., 2., 3., etc.)
        import re
        
        # Find all numbered sections
        pattern = r'^(\d+)\.\s*(.*?)(?=^\d+\.|$)'
        matches = re.findall(pattern, response_text, re.MULTILINE | re.DOTALL)
        
        for number, content in matches:
            # Clean up the content
            cleaned_content = re.sub(r'\n+', ' ', content.strip())  # Replace multiple newlines with spaces
            cleaned_content = re.sub(r'\s+', ' ', cleaned_content)   # Replace multiple spaces with single space
            
            # Remove any markdown formatting like **bold**
            cleaned_content = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned_content)
            
            if cleaned_content:
                summaries.append(cleaned_content)
        
        # If regex approach didn't work well, try manual parsing
        if len(summaries) != expected_count:
            print(f"     🔧 Regex parsing got {len(summaries)} summaries, expected {expected_count}. Trying manual parsing...")
            summaries = self.manual_parse_response(response_text, expected_count)
        
        # Ensure we return exactly the expected number of summaries
        while len(summaries) < expected_count:
            summaries.append("")
        
        return summaries[:expected_count]
    
    def manual_parse_response(self, response_text, expected_count):
        """Fallback manual parsing method"""
        summaries = []
        lines = response_text.strip().split('\\n')
        current_summary = ""
        current_number = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if this line starts with a number pattern like "1." or "1: "
            import re
            number_match = re.match(r'^(\d+)[\.\:\)]\s*(.*)', line)
            
            if number_match:
                number = int(number_match.group(1))
                content = number_match.group(2)
                
                # Save previous summary if we have one
                if current_summary and current_number > 0:
                    # Clean up the summary
                    cleaned = re.sub(r'\s+', ' ', current_summary.strip())
                    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # Remove markdown
                    summaries.append(cleaned)
                
                # Start new summary
                current_number = number
                current_summary = content
            else:
                # Continue current summary
                if current_summary:
                    current_summary += " " + line
                elif line and not line.lower().startswith(('here', 'the following', 'summary')):
                    # Skip introductory text
                    current_summary = line
        
        # Add the last summary
        if current_summary and current_number > 0:
            cleaned = re.sub(r'\s+', ' ', current_summary.strip())
            cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
            summaries.append(cleaned)
        
        return summaries
    
    def generate_test_summaries(self):
        """Generate summaries for test dataset"""
        print("🔄 Generating test summaries...")
        
        # Prepare summary cache directory
        Path(SUMMARY_CACHE_DIR).mkdir(parents=True, exist_ok=True)
        
        # Group recipes by collection
        recipes_by_collection = defaultdict(list)
        
        for recipe_id, recipe_data in self.classified_recipes.items():
            collection = recipe_data.get('collection')
            if collection in TEST_COLLECTIONS_CONFIG:
                recipes_by_collection[collection].append((recipe_id, recipe_data))
        
        total_processed = 0
        total_generated = 0
        
        for collection_name, recipes in recipes_by_collection.items():
            print(f"\\n📁 Processing collection: {collection_name}")
            
            # Ensure cache folder exists
            col_cache_dir = Path(SUMMARY_CACHE_DIR) / collection_name
            col_cache_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"   📊 {len(recipes)} test recipes to process")
            
            # Process all recipes in this collection as one batch (small numbers for testing)
            batch_recipe_data = [recipe_data for _, recipe_data in recipes]
            batch_recipe_ids = [recipe_id for recipe_id, _ in recipes]
            
            print(f"     🤖 Processing batch: {len(recipes)} recipes...")
            
            try:
                summaries = self.summarize_recipes_batch(batch_recipe_data)
                
                # Save each summary to its cache file
                for recipe_id, summary in zip(batch_recipe_ids, summaries):
                    cache_file = col_cache_dir / f"{recipe_id}.txt"
                    
                    if summary and summary.strip():
                        cache_file.write_text(summary.strip(), encoding='utf-8')
                        total_generated += 1
                        print(f"     ✅ Summary saved for recipe {recipe_id}")
                    else:
                        print(f"     ⚠️  Empty summary for recipe {recipe_id}")
                        cache_file.write_text("", encoding='utf-8')
                
                print(f"     ✅ Batch complete: {len(summaries)} summaries processed")
                    
            except Exception as e:
                print(f"     ❌ Error processing batch: {e}")
                continue
            
            total_processed += len(recipes)
        
        print(f"\\n🎉 TEST SUMMARY GENERATION COMPLETE!")
        print("=" * 50)
        print(f"📊 Total recipes processed: {total_processed}")
        print(f"🆕 Summaries generated: {total_generated}")
        
        return True

def main():
    """Main test execution"""
    print("🧪 GEMINI BATCH SUMMARY GENERATION TEST")
    print("=" * 60)
    print("🎯 Testing batch processing with 50 sample recipes")
    print("=" * 60)
    
    generator = TestSummaryGenerator()
    
    if not generator.load_classified_recipes():
        return 1
    
    if not generator.generate_test_summaries():
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())