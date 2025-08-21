import os
import json
import logging
from typing import Dict, List, Any, Optional
import google.generativeai as genai

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiService:
    """Service for interacting with Google's Gemini LLM to generate meal plans with RAG"""
    
    def __init__(self):
        # Get API key from environment variable
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not found in environment variables!")
        
        # Initialize Google Generative AI
        genai.configure(api_key=self.api_key)
        
        # Default model
        self.model_name = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash-exp")
        
        # Initialize the model
        self.model = genai.GenerativeModel(self.model_name)
        
        # Load prompt templates from files
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")
        self.prompt_templates = self._load_prompt_templates()

    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load all prompt templates from .txt files"""
        templates = {}
        template_files = {
            "query_generation": "query_generation.txt",
            "meal_plan_generation": "meal_plan_generation.txt", 
            "modification_queries": "modification_queries.txt",
            "plan_modification": "plan_modification.txt"
        }
        
        for key, filename in template_files.items():
            filepath = os.path.join(self.prompts_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    templates[key] = f.read().strip()
                logger.info(f"Loaded prompt template: {key}")
            except FileNotFoundError:
                logger.error(f"Prompt template file not found: {filepath}")
                templates[key] = ""
        
        return templates

    def generate_meal_plan(self, 
                         user_preferences: Dict[str, Any],
                         retrieved_recipes: List[Dict[str, Any]],
                         days: int = 7,
                         meals_per_day: int = 3,
                         include_snacks: bool = False,
                         additional_preferences: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a meal plan using Google's Gemini API with retrieved recipes
        
        Args:
            user_preferences: Dictionary containing user preferences (allergies, diet, etc.)
            retrieved_recipes: List of recipes retrieved using RAG
            days: Number of days to plan for
            meals_per_day: Number of meals per day
            include_snacks: Whether to include snacks
            additional_preferences: Any additional preferences specified by the user
            
        Returns:
            Dictionary containing the meal plan and explanation
        """
        try:
            # Extract user preferences
            dietary_restrictions = user_preferences.get("dietary_restrictions", [])
            allergies = user_preferences.get("allergies", [])
            cuisine_preferences = user_preferences.get("cuisine_preferences", [])
            disliked_ingredients = user_preferences.get("disliked_ingredients", [])
            
            # Prepare recipe context for the prompt
            recipe_context = []
            for recipe in retrieved_recipes:
                recipe_context.append({
                    "id": recipe["recipe_id"],
                    "name": recipe["recipe_name"],
                    "ingredients": recipe["ingredients"],
                    "cuisine_type": recipe["cuisine_type"],
                })
            
            # Create simple prompt for basic meal plan generation
            prompt = f"""
            You are a meal planning assistant. Create a {days}-day meal plan with {meals_per_day} meals per day.
            
            Available recipes: {json.dumps(recipe_context, indent=2)}
            Dietary restrictions: {", ".join(dietary_restrictions) if dietary_restrictions else "None"}
            Allergies: {", ".join(allergies) if allergies else "None"}
            Cuisine preferences: {", ".join(cuisine_preferences) if cuisine_preferences else "None"}
            Additional preferences: {additional_preferences if additional_preferences else "None"}
            
            Return JSON format:
            {{
                "meal_plan": [
                    {{
                        "day": 1,
                        "meals": [
                            {{"meal_type": "breakfast", "recipe_id": 123, "recipe_name": "Recipe Name"}}
                        ]
                    }}
                ],
                "explanation": "Brief explanation"
            }}
            """
            
            response = self.model.generate_content(prompt)
            result = response.text
            
            # Parse the JSON response
            try:
                meal_plan_data = json.loads(result)
                # Ensure the required fields exist in the response
                if "meal_plan" not in meal_plan_data or "explanation" not in meal_plan_data:
                    logger.error("Invalid response from Gemini API")
                    return self._create_fallback_meal_plan(retrieved_recipes, days, meals_per_day)
                
                return meal_plan_data
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from Gemini response")
                return self._create_fallback_meal_plan(retrieved_recipes, days, meals_per_day)
            
        except Exception as e:
            logger.error(f"Error generating meal plan with Gemini: {e}")
            return self._create_fallback_meal_plan(retrieved_recipes, days, meals_per_day)
    
    def generate_grocery_list(self, recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a grocery list from a list of recipes
        
        Args:
            recipes: List of recipes included in the meal plan
            
        Returns:
            Dictionary containing the grocery list with items organized by category
        """
        try:
            # Extract ingredients from the recipes
            all_ingredients = []
            for recipe in recipes:
                all_ingredients.extend(recipe.get("ingredients", []))
            
            # Create simple prompt for grocery list generation
            prompt = f"""
            Create an optimized grocery list from these recipe ingredients:
            {json.dumps(all_ingredients, indent=2)}
            
            Instructions:
            1. Combine identical or similar ingredients
            2. Group items by grocery store categories (produce, dairy, meat, etc.)
            3. Standardize units where possible
            4. Include quantities needed
            
            Return JSON format:
            {{
                "grocery_list": [
                    {{
                        "category": "Produce",
                        "items": [
                            {{"name": "Ingredient name", "amount": "Quantity needed"}}
                        ]
                    }}
                ]
            }}
            """
            
            response = self.model.generate_content(prompt)
            result = response.text
            
            # Parse the JSON response
            try:
                grocery_list_data = json.loads(result)
                # Ensure the required fields exist in the response
                if "grocery_list" not in grocery_list_data:
                    logger.error("Invalid response from Gemini API")
                    return {"grocery_list": self._create_fallback_grocery_list(all_ingredients)}
                
                return grocery_list_data
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from Gemini response")
                return {"grocery_list": self._create_fallback_grocery_list(all_ingredients)}
            
        except Exception as e:
            logger.error(f"Error generating grocery list with Gemini: {e}")
            return {"grocery_list": self._create_fallback_grocery_list(all_ingredients)}

    def _create_fallback_grocery_list(self, ingredients: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Creates a fallback grocery list if the API call fails"""
        items = []
        for ingredient in ingredients:
            name = ingredient.get("name", "Unknown ingredient")
            amount = ingredient.get("amount", "")
            unit = ingredient.get("unit", "")
            
            amount_str = f"{amount} {unit}".strip()
            
            items.append({
                "name": name,
                "amount": amount_str if amount_str else "as needed"
            })
        
        return [{
            "category": "All ingredients", 
            "items": items
        }]

    def generate_search_queries(self, user_prompt: str) -> List[str]:
        """Generate search queries for the vector database using Gemini"""
        try:
            prompt = self.prompt_templates["query_generation"].format(user_prompt=user_prompt)
            
            response = self.model.generate_content(prompt)
            result = response.text
            
            logger.debug(f"DEBUG: Raw query generation response: {result}")
            
            try:
                # Clean the response - remove markdown code blocks
                cleaned_result = result.strip()
                if cleaned_result.startswith("```json"):
                    cleaned_result = cleaned_result[7:]  # Remove ```json
                if cleaned_result.startswith("```"):
                    cleaned_result = cleaned_result[3:]   # Remove ```
                if cleaned_result.endswith("```"):
                    cleaned_result = cleaned_result[:-3]  # Remove trailing ```
                cleaned_result = cleaned_result.strip()
                
                logger.debug(f"DEBUG: Cleaned query response for JSON parsing: {cleaned_result}")
                
                parsed_result = json.loads(cleaned_result)
                queries = parsed_result.get("queries", [])
                
                # Validate and clean queries - ensure single words only
                validated_queries = self._validate_and_clean_queries(queries)
                
                logger.info(f"Generated {len(queries)} raw queries, validated to {len(validated_queries)} queries")
                
                # If no valid queries generated, use fallback
                if not validated_queries:
                    logger.warning("No valid queries generated, using fallback extraction")
                    return self._extract_fallback_queries(user_prompt)
                
                return validated_queries[:5]
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from query generation response: {e}")
                logger.error(f"Raw response was: {result}")
                return self._extract_fallback_queries(user_prompt)
                
        except Exception as e:
            logger.error(f"Error generating search queries: {e}")
            return self._extract_fallback_queries(user_prompt)

    def _validate_and_clean_queries(self, queries: List[str]) -> List[str]:
        """Validate queries to ensure they are single words only"""
        validated = []
        forbidden_words = {"recipes", "healthy", "breakfast", "lunch", "dinner", "meal", "plan", "food", "options", "dishes"}
        
        for query in queries:
            # Clean the query
            clean_query = query.strip().lower()
            
            # Skip empty queries
            if not clean_query:
                continue
                
            # Check if it's a single word (no spaces)
            if " " in clean_query:
                # Try to extract the main ingredient from multi-word queries
                words = clean_query.split()
                for word in words:
                    if word not in forbidden_words and len(word) > 2:
                        validated.append(word)
                        break
            else:
                # Single word - check if it's valid
                if clean_query not in forbidden_words and len(clean_query) > 2:
                    validated.append(clean_query)
        
        # Remove duplicates while preserving order
        seen = set()
        final_queries = []
        for query in validated:
            if query not in seen:
                seen.add(query)
                final_queries.append(query)
        
        return final_queries

    def _extract_fallback_queries(self, user_prompt: str) -> List[str]:
        """Extract simple fallback queries from user prompt"""
        # Simple keyword extraction as fallback - use terms that match our recipe database
        common_ingredients = ["chicken", "beef", "salad", "sandwich", "toast", "soup", "pasta", "burger", "pizza", "rice"]
        prompt_lower = user_prompt.lower()
        
        found_queries = []
        for ingredient in common_ingredients:
            if ingredient in prompt_lower:
                found_queries.append(ingredient)
        
        # If no common ingredients found, use context-aware generic terms that match our recipes
        if not found_queries:
            if "vegetarian" in prompt_lower or "vegan" in prompt_lower:
                # For vegetarian requests, search for plant-based recipes
                found_queries.extend(["salad", "toast", "avocado"])
            elif "healthy" in prompt_lower:
                found_queries.extend(["salad", "avocado", "chicken"])
            elif "protein" in prompt_lower:
                # For protein requests, include meat and eggs
                found_queries.extend(["chicken", "beef", "eggs"])
            elif "breakfast" in prompt_lower:
                found_queries.extend(["toast", "pancake", "cereal"])
            elif "lunch" in prompt_lower or "dinner" in prompt_lower:
                found_queries.extend(["chicken", "sandwich", "salad"])
            else:
                # Generic fallback that matches our recipes
                found_queries.extend(["chicken", "salad", "sandwich"])
        
        return found_queries[:3]

    def generate_rag_meal_plan(self, user_prompt: str, retrieved_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate meal plan using AI-enhanced retrieved recipes and Gemini"""
        try:
            logger.info("\n🎭 STEP 4: Gemini Meal Plan Generation")
            logger.info(f"📝 Input Data Analysis:")
            logger.info(f"   • User Prompt: '{user_prompt}'")
            logger.info(f"   • Retrieved Recipes Count: {len(retrieved_recipes)}")
            
            # Check if we have AI-enhanced recipes with similarity scores and collections
            has_ai_scores = any(recipe.get("similarity_score") is not None for recipe in retrieved_recipes)
            logger.info(f"   • AI-Enhanced Recipes: {has_ai_scores}")
            
            if has_ai_scores:
                logger.info("🤖 Using AI-enhanced meal plan generation with similarity scores")
                return self._generate_ai_enhanced_meal_plan(user_prompt, retrieved_recipes)
            else:
                logger.info("📝 Using basic meal plan generation (no AI scores)")
                return self._generate_basic_meal_plan(user_prompt, retrieved_recipes)
                
        except Exception as e:
            logger.error(f"Error generating RAG meal plan: {e}")
            return self._create_fallback_meal_plan(retrieved_recipes, 7, 3)

    def _generate_ai_enhanced_meal_plan(self, user_prompt: str, retrieved_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate meal plan leveraging AI recommendation scores and collections"""
        try:
            logger.info("📊 Analyzing recipe collections and user context...")
            
            # Organize recipes by collection for better meal type assignment
            collections = {}
            for recipe in retrieved_recipes:
                collection = recipe.get("cuisine_type", "general")
                if collection not in collections:
                    collections[collection] = []
                collections[collection].append(recipe)
            
            logger.info(f"📂 Recipe Collections Organized:")
            for collection, recipes in collections.items():
                avg_score = sum(r.get("similarity_score", 0) for r in recipes) / len(recipes) if recipes else 0
                logger.info(f"   • {collection}: {len(recipes)} recipes (avg score: {avg_score:.3f})")
            
            # Get user preferences from retrieved recipes metadata if available
            user_context = ""
            has_user_prefs = retrieved_recipes and retrieved_recipes[0].get("user_preferences")
            logger.info(f"👤 User Preferences Available in Recipe Data: {bool(has_user_prefs)}")
            
            if has_user_prefs:
                prefs = retrieved_recipes[0]["user_preferences"]
                logger.info(f"🔍 Extracting User Context for Prompt:")
                logger.info(f"   • Dietary Restrictions: {prefs.get('dietary_restrictions', [])}")
                logger.info(f"   • Allergies: {prefs.get('allergies', [])}")
                logger.info(f"   • Cuisine Preferences: {prefs.get('cuisine_preferences', [])}")
                logger.info(f"   • Cooking Style: {prefs.get('cooking_preferences', [])}")
                logger.info(f"   • Spice Tolerance: {prefs.get('spice_tolerance', 'medium')}")
                
                user_context = f"""
            USER PROFILE CONTEXT:
            - Dietary Restrictions: {', '.join(prefs.get('dietary_restrictions', []))}
            - Allergies: {', '.join(prefs.get('allergies', []))}
            - Cuisine Preferences: {', '.join(prefs.get('cuisine_preferences', []))}
            - Cooking Style: {', '.join(prefs.get('cooking_preferences', []))}
            - Spice Tolerance: {prefs.get('spice_tolerance', 'medium')}
            - Portion Preference: {prefs.get('portion_preferences', 'medium')}
            - Disliked Ingredients: {', '.join(prefs.get('disliked_ingredients', []))}
            """

            # Enhanced prompt with AI data
            logger.info("✍️ Constructing Enhanced Prompt for Gemini...")
            enhanced_prompt = f"""
            Create a personalized meal plan based on this request: {user_prompt}
            {user_context}
            
            AVAILABLE AI-RECOMMENDED RECIPES (organized by collection with similarity scores):
            {json.dumps(collections, indent=2)}
            
            INSTRUCTIONS:
            1. Prioritize recipes with higher similarity_score (closer to 1.0) as they better match user intent
            2. Use recipe collections for smart meal type assignment:
               - breakfast-morning: breakfast meals
               - desserts-sweets: desserts or sweet snacks  
               - protein-mains: lunch/dinner main courses
               - quick-light: light meals, snacks, quick options
               - fresh-cold: salads, cold preparations
               - baked-breads: baked goods, bread-based meals
               - comfort-cooked: hearty dinner meals
               - plant-based: vegetarian/vegan options
            3. Ensure variety across different collections and meal types
            4. Balance nutrition by including different types of recipes
            5. Create 7 days with 3 meals per day unless user specifies otherwise
            6. Include similarity scores in the output for transparency
            
            Return JSON format:
            {{
                "meal_plan": [
                    {{
                        "day": 1,
                        "meals": [
                            {{
                                "meal_type": "breakfast",
                                "recipe_id": 123,
                                "recipe_name": "Recipe Name",
                                "collection": "breakfast-morning",
                                "similarity_score": 0.85
                            }}
                        ]
                    }}
                ],
                "explanation": "Detailed explanation of meal plan choices, highlighting how AI recommendations were used to match your preferences"
            }}
            
            CRITICAL: Output ONLY the JSON object. No markdown, no extra text.
            """
            
            logger.info("="*80)
            logger.info("📤 EXACT PROMPT SENT TO GEMINI:")
            logger.info("="*80)
            logger.info(enhanced_prompt)
            logger.info("="*80)
            
            logger.info("⏳ Sending request to Gemini API...")
            response = self.model.generate_content(enhanced_prompt)
            result = response.text
            
            logger.info("="*80) 
            logger.info("📥 EXACT RESPONSE FROM GEMINI:")
            logger.info("="*80)
            logger.info(result)
            logger.info("="*80)
            
            logger.info("🔄 Parsing Gemini response...")
            parsed_result = self._parse_meal_plan_response(result, retrieved_recipes)
            logger.info(f"✅ Gemini response parsed successfully")
            
            return parsed_result
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced meal plan generation: {e}")
            return self._generate_basic_meal_plan(user_prompt, retrieved_recipes)

    def _generate_basic_meal_plan(self, user_prompt: str, retrieved_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback to basic meal plan generation using original template"""
        try:
            formatted_recipes = json.dumps(retrieved_recipes, indent=2)
            
            if self.prompt_templates.get("meal_plan_generation"):
                prompt = self.prompt_templates["meal_plan_generation"].format(
                    user_prompt=user_prompt,
                    retrieved_recipes=formatted_recipes
                )
            else:
                prompt = f"""
                Create a meal plan based on this request: {user_prompt}
                
                Available recipes: {formatted_recipes}
                
                Return JSON format:
                {{
                    "meal_plan": [
                        {{
                            "day": 1,
                            "meals": [
                                {{"meal_type": "breakfast", "recipe_id": 123, "recipe_name": "Recipe Name"}}
                            ]
                        }}
                    ],
                    "explanation": "Brief explanation"
                }}
                """
            
            response = self.model.generate_content(prompt)
            result = response.text
            
            return self._parse_meal_plan_response(result, retrieved_recipes)
            
        except Exception as e:
            logger.error(f"Error in basic meal plan generation: {e}")
            return self._create_fallback_meal_plan(retrieved_recipes, 7, 3)

    def _parse_meal_plan_response(self, result: str, retrieved_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse Gemini response and validate meal plan format"""
        try:
            logger.debug(f"DEBUG: Raw Gemini response: {result}")
            
            # Clean the response - remove markdown code blocks
            cleaned_result = result.strip()
            if cleaned_result.startswith("```json"):
                cleaned_result = cleaned_result[7:]  # Remove ```json
            if cleaned_result.startswith("```"):
                cleaned_result = cleaned_result[3:]   # Remove ```
            if cleaned_result.endswith("```"):
                cleaned_result = cleaned_result[:-3]  # Remove trailing ```
            cleaned_result = cleaned_result.strip()
            
            logger.debug(f"DEBUG: Cleaned response for JSON parsing: {cleaned_result}")
            
            meal_plan_data = json.loads(cleaned_result)
            
            # Validate that required fields exist
            if "meal_plan" not in meal_plan_data or "explanation" not in meal_plan_data:
                logger.error("Invalid response from Gemini API - missing required fields")
                return self._create_fallback_meal_plan(retrieved_recipes, 7, 3)
            
            # Validate that recipe IDs exist in retrieved recipes
            valid_recipe_ids = set(str(r.get("recipe_id") or r.get("id")) for r in retrieved_recipes)
            
            for day_plan in meal_plan_data["meal_plan"]:
                for meal in day_plan.get("meals", []):
                    recipe_id = str(meal.get("recipe_id", ""))
                    if recipe_id not in valid_recipe_ids:
                        logger.warning(f"Recipe ID {recipe_id} not found in retrieved recipes")
            
            logger.info("Successfully generated and validated RAG meal plan")
            return meal_plan_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from RAG meal plan generation response: {e}")
            logger.error(f"Raw response was: {result}")
            return self._create_fallback_meal_plan(retrieved_recipes, 7, 3)

    def generate_modification_queries(self, current_meal_plan: Dict[str, Any], user_feedback: str) -> List[str]:
        """Generate queries for meal plan modifications based on user feedback"""
        try:
            prompt = self.prompt_templates["modification_queries"].format(
                current_meal_plan=json.dumps(current_meal_plan, indent=2),
                user_feedback=user_feedback
            )
            
            response = self.model.generate_content(prompt)
            result = response.text
            
            try:
                parsed_result = json.loads(result)
                queries = parsed_result.get("queries", [])
                logger.info(f"Generated {len(queries)} modification queries")
                return queries[:5]
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from modification queries response")
                return [user_feedback]
                
        except Exception as e:
            logger.error(f"Error generating modification queries: {e}")
            return [user_feedback]

    def modify_meal_plan(self, current_meal_plan: Dict[str, Any], user_feedback: str, new_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Modify meal plan based on user feedback and new recipes"""
        try:
            prompt = self.prompt_templates["plan_modification"].format(
                current_meal_plan=json.dumps(current_meal_plan, indent=2),
                user_feedback=user_feedback,
                new_recipes=json.dumps(new_recipes, indent=2)
            )
            
            response = self.model.generate_content(prompt)
            result = response.text
            
            try:
                modified_plan = json.loads(result)
                logger.info("Successfully modified meal plan")
                return modified_plan
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from meal plan modification response")
                return current_meal_plan
                
        except Exception as e:
            logger.error(f"Error modifying meal plan: {e}")
            return current_meal_plan

    def _create_fallback_meal_plan(self, retrieved_recipes: List[Dict[str, Any]], days: int = 3, meals_per_day: int = 3) -> Dict[str, Any]:
        """Create a simple fallback meal plan if AI generation fails"""
        if not retrieved_recipes:
            return {
                "meal_plan": [],
                "explanation": "No recipes available to create a meal plan."
            }
        
        # Create meal plan for all days, using different recipes and being more varied
        meal_plan = []
        recipe_count = len(retrieved_recipes)
        
        # Create a more varied selection by spreading recipes across days and meal types
        import random
        random.seed(42)  # Use a fixed seed for consistent results
        
        for day in range(1, days + 1):
            meals = []
            meal_types = ["breakfast", "lunch", "dinner", "snack"][:meals_per_day]
            
            for i, meal_type in enumerate(meal_types):
                # Use a more varied approach - different recipes for different days and meal types
                if meal_type == "breakfast":
                    # Prefer certain recipes for breakfast (avocado toast, cereal, etc.)
                    breakfast_recipes = [r for r in retrieved_recipes if any(word in r.get("name", "").lower() 
                                       for word in ["toast", "cereal", "pancake", "breakfast", "bagel"])]
                    if breakfast_recipes:
                        recipe_index = (day - 1) % len(breakfast_recipes)
                        recipe = breakfast_recipes[recipe_index]
                    else:
                        recipe_index = (day - 1 + i) % recipe_count
                        recipe = retrieved_recipes[recipe_index]
                elif meal_type == "lunch":
                    # Prefer salads, sandwiches for lunch
                    lunch_recipes = [r for r in retrieved_recipes if any(word in r.get("name", "").lower() 
                                   for word in ["salad", "sandwich", "soup", "wrap", "burger"])]
                    if lunch_recipes:
                        recipe_index = (day - 1) % len(lunch_recipes)
                        recipe = lunch_recipes[recipe_index]
                    else:
                        recipe_index = (day - 1 + i + 5) % recipe_count  # Different offset
                        recipe = retrieved_recipes[recipe_index]
                elif meal_type == "dinner":
                    # Prefer hearty meals for dinner
                    dinner_recipes = [r for r in retrieved_recipes if any(word in r.get("name", "").lower() 
                                    for word in ["chicken", "beef", "pasta", "pizza", "curry", "steak", "chili"])]
                    if dinner_recipes:
                        recipe_index = (day - 1) % len(dinner_recipes)
                        recipe = dinner_recipes[recipe_index]
                    else:
                        recipe_index = (day - 1 + i + 10) % recipe_count  # Different offset
                        recipe = retrieved_recipes[recipe_index]
                else:
                    # For snacks, use remaining recipes
                    recipe_index = (day - 1 + i + 15) % recipe_count
                    recipe = retrieved_recipes[recipe_index]
                
                meals.append({
                    "meal_type": meal_type,
                    "recipe_id": recipe.get("id") or recipe.get("recipe_id"),
                    "recipe_name": recipe.get("name") or recipe.get("recipe_name", "Unknown Recipe")
                })
            
            meal_plan.append({
                "day": day,
                "meals": meals
            })
        
        return {
            "meal_plan": meal_plan,
            "explanation": "This meal plan was created using available recipes with variety across different meal types and days."
        }