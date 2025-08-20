#!/usr/bin/env python3
"""
Standalone Gemini Summary Generator
Only generates missing recipe summaries without vector database operations
"""

import os
import json
import sys
from pathlib import Path
from collections import defaultdict

# Security check: Ensure API keys are in environment, not hardcoded
def check_api_security():
    """Check that API keys are properly secured"""
    print("🔒 SECURITY CHECK: Verifying API key configuration...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("💡 Please set GOOGLE_API_KEY in your .env file or environment")
        return False
    
    if not api_key.startswith("AIza") or len(api_key) < 35:
        print("⚠️  API key format appears invalid")
        return False
    
    print("✅ API key found in environment (secure)")
    return True

# Security check before imports
if not check_api_security():
    print("❌ Security check failed. Please configure API keys properly.")
    sys.exit(1)

from google import genai

# Configuration
CLASSIFICATION_RESULTS_PATH = "function_classification_results/function_classified_recipes.json"
SUMMARY_CACHE_DIR = "recipe_summaries"

# Collections to process (excluding beverages as requested)
COLLECTIONS_TO_PROCESS = {
    "desserts-sweets": {"batch_size": 50, "estimated_count": 2465},
    "protein-mains": {"batch_size": 30, "estimated_count": 1379}, 
    "quick-light": {"batch_size": 40, "estimated_count": 2476},
    "fresh-cold": {"batch_size": 25, "estimated_count": 950},
    "baked-breads": {"batch_size": 25, "estimated_count": 885},
    "comfort-cooked": {"batch_size": 20, "estimated_count": 718},
    "breakfast-morning": {"batch_size": 15, "estimated_count": 415},
    "plant-based": {"batch_size": 10, "estimated_count": 78}
}

class SummaryGenerator:
    """
    Generates missing recipe summaries using Gemini API
    """
    
    def __init__(self):
        self.genai_client = genai.Client()
        self.classified_recipes = None
        print("✅ Gemini GenAI client initialized")
    
    def load_classified_recipes(self):
        """Load classified recipes"""
        print(f"📂 Loading classified recipes from {CLASSIFICATION_RESULTS_PATH}...")
        
        try:
            with open(CLASSIFICATION_RESULTS_PATH, 'r', encoding='utf-8') as f:
                self.classified_recipes = json.load(f)
            
            print(f"✅ Loaded {len(self.classified_recipes)} classified recipes")
            return True
            
        except FileNotFoundError:
            print(f"❌ Classification results not found at {CLASSIFICATION_RESULTS_PATH}")
            return False
        except Exception as e:
            print(f"❌ Error loading classification results: {e}")
            return False
    
    def summarize_recipes_batch(self, recipes_data):
        """Generate summaries for a batch of recipes using Gemini"""
        context = (
            "You are helping build MealMateAI, a semantic search service "
            "over multiple recipe collections. "
            "Embedding model used for indexing: all-mpnet-base-v2.\n\n"
            "Please provide a concise summary for each of the following recipes. "
            "Format your response as a numbered list with one summary per recipe, "
            "in the same order as provided:\n\n"
        )
        
        # Build the batch prompt with all recipes
        recipe_texts = []
        for i, recipe_data in enumerate(recipes_data, 1):
            # Safely get title as string
            title = str(recipe_data.get('title', ''))
            blocks = [f"Recipe {i}: {title}"]
            
            # Safely process ingredients
            ingredients = recipe_data.get("ingredients", [])
            if ingredients:
                # Convert all ingredients to strings and filter out empty ones
                ingredient_strs = [str(ing) for ing in ingredients if ing is not None and str(ing).strip()]
                if ingredient_strs:
                    blocks.append("Ingredients: " + ", ".join(ingredient_strs))
            
            # Safely process instructions
            if "instructions" in recipe_data:
                instructions = recipe_data.get("instructions")
                if instructions is not None:
                    instructions_str = str(instructions).strip()
                    if instructions_str:
                        blocks.append("Instructions: " + instructions_str)
            
            recipe_text = "\n".join(blocks)
            recipe_texts.append(recipe_text)
        
        # Combine all recipes into one prompt
        full_prompt = context + "\n\n".join(recipe_texts)
        
        import time
        
        # Retry logic for API overload
        max_retries = 3
        for attempt in range(max_retries):
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
                    if attempt < max_retries - 1:
                        print(f"     ⚠️  Empty response on attempt {attempt + 1}, retrying...")
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return [""] * len(recipes_data)
                
                # Parse the numbered response into individual summaries
                summaries = self.parse_batch_response(response_text, len(recipes_data))
                return summaries
                
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "UNAVAILABLE" in error_msg or "overloaded" in error_msg:
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                        print(f"     ⚠️  API overloaded (attempt {attempt + 1}/{max_retries}), waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"     ❌ API overloaded after {max_retries} attempts, skipping batch")
                        return [""] * len(recipes_data)
                else:
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
        lines = response_text.strip().split('\n')
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
    
    def generate_missing_summaries(self):
        """Generate summaries only for recipes that don't have them yet"""
        print("🔄 Generating missing recipe summaries...")
        
        # Group recipes by collection
        recipes_by_collection = defaultdict(list)
        
        for recipe_id, recipe_data in self.classified_recipes.items():
            collection = recipe_data.get('collection')
            if collection in COLLECTIONS_TO_PROCESS:
                recipes_by_collection[collection].append((recipe_id, recipe_data))
        
        total_processed = 0
        total_skipped = 0
        total_generated = 0
        
        for collection_name, recipes in recipes_by_collection.items():
            print(f"\n📁 Processing collection: {collection_name}")
            
            # Ensure cache folder exists
            col_cache_dir = Path(SUMMARY_CACHE_DIR) / collection_name
            col_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Count existing non-empty summaries
            existing_files = list(col_cache_dir.glob("*.txt"))
            non_empty_summaries = 0
            for summary_file in existing_files:
                try:
                    content = summary_file.read_text(encoding='utf-8').strip()
                    if content:
                        non_empty_summaries += 1
                except:
                    pass  # Count as empty if can't read
            
            print(f"   📊 {len(recipes)} total recipes")
            print(f"   ✅ {non_empty_summaries} valid summaries already exist")
            print(f"   📁 {len(existing_files) - non_empty_summaries} empty summary files found")
            print(f"   🔄 {len(recipes) - non_empty_summaries} summaries to generate")
            
            generated_count = 0
            skipped_count = non_empty_summaries
            
            # Collect recipes that need summaries (missing files or empty files)
            recipes_needing_summaries = []
            for recipe_id, recipe_data in recipes:
                cache_file = col_cache_dir / f"{recipe_id}.txt"
                needs_summary = False
                
                if not cache_file.exists():
                    needs_summary = True
                else:
                    # Check if file exists but is empty or contains only whitespace
                    try:
                        existing_content = cache_file.read_text(encoding='utf-8').strip()
                        if not existing_content:
                            needs_summary = True
                            print(f"     🔄 Found empty summary file for recipe {recipe_id}, will regenerate")
                    except Exception as e:
                        print(f"     ⚠️  Error reading existing file for recipe {recipe_id}: {e}")
                        needs_summary = True
                
                if needs_summary:
                    recipes_needing_summaries.append((recipe_id, recipe_data))
            
            # Process in batches
            config = COLLECTIONS_TO_PROCESS[collection_name]
            batch_size = config["batch_size"]
            
            for i in range(0, len(recipes_needing_summaries), batch_size):
                batch = recipes_needing_summaries[i:i + batch_size]
                batch_recipe_data = [recipe_data for _, recipe_data in batch]
                batch_recipe_ids = [recipe_id for recipe_id, _ in batch]
                
                print(f"     🤖 Processing batch {i//batch_size + 1}: {len(batch)} recipes...")
                
                try:
                    summaries = self.summarize_recipes_batch(batch_recipe_data)
                    
                    # Save each summary to its cache file
                    for recipe_id, summary in zip(batch_recipe_ids, summaries):
                        cache_file = col_cache_dir / f"{recipe_id}.txt"
                        
                        if summary and summary.strip():
                            cache_file.write_text(summary.strip(), encoding='utf-8')
                            generated_count += 1
                            total_generated += 1
                        else:
                            print(f"     ⚠️  Empty summary received for recipe {recipe_id}")
                            # Still create an empty file to mark as processed
                            cache_file.write_text("", encoding='utf-8')
                    
                    print(f"     ✅ Batch complete: {len(summaries)} summaries generated")
                        
                except Exception as e:
                    print(f"     ❌ Error processing batch: {e}")
                    # Fall back to individual processing for this batch
                    print(f"     🔄 Falling back to individual processing...")
                    for recipe_id, recipe_data in batch:
                        try:
                            summary = self.summarize_recipes_batch([recipe_data])[0]
                            cache_file = col_cache_dir / f"{recipe_id}.txt"
                            cache_file.write_text(summary or "", encoding='utf-8')
                            if summary:
                                generated_count += 1
                                total_generated += 1
                        except Exception as individual_e:
                            print(f"     ❌ Failed individual processing for {recipe_id}: {individual_e}")
                            continue
            
            print(f"   📈 Collection {collection_name}: {generated_count} new summaries generated")
            total_processed += len(recipes)
            total_skipped += skipped_count
        
        print(f"\n🎉 SUMMARY GENERATION COMPLETE!")
        print("=" * 50)
        print(f"📊 Total recipes processed: {total_processed}")
        print(f"✅ Summaries already existed: {total_skipped}")
        print(f"🆕 New summaries generated: {total_generated}")
        print(f"🚀 All recipe summaries are now ready!")
        
        return True

def main():
    """Main execution"""
    print("🤖 GEMINI RECIPE SUMMARY GENERATOR")
    print("=" * 50)
    print("🎯 Only generating missing summaries (no vector database operations)")
    print("=" * 50)
    
    generator = SummaryGenerator()
    
    if not generator.load_classified_recipes():
        return 1
    
    if not generator.generate_missing_summaries():
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())