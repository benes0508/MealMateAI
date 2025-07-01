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
            
            try:
                # Clean the response - remove any markdown formatting
                cleaned_result = result.strip()
                if cleaned_result.startswith("```json"):
                    cleaned_result = cleaned_result.replace("```json", "").replace("```", "").strip()
                
                parsed_result = json.loads(cleaned_result)
                queries = parsed_result.get("queries", [])
                
                # Validate and clean queries - ensure single words only
                validated_queries = self._validate_and_clean_queries(queries)
                
                logger.info(f"Generated {len(queries)} raw queries, validated to {len(validated_queries)} queries")
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
        # Simple keyword extraction as fallback
        common_ingredients = ["apple", "chicken", "beef", "pasta", "rice", "vegetarian", "vegan", "italian", "mexican", "asian"]
        prompt_lower = user_prompt.lower()
        
        found_queries = []
        for ingredient in common_ingredients:
            if ingredient in prompt_lower:
                found_queries.append(ingredient)
        
        # If no common ingredients found, use generic terms
        if not found_queries:
            if "vegetarian" in prompt_lower or "vegan" in prompt_lower:
                found_queries.append("vegetarian")
            if "healthy" in prompt_lower:
                found_queries.append("salad")
            if not found_queries:
                found_queries.append("chicken")  # Generic fallback
        
        return found_queries[:3]

    def generate_rag_meal_plan(self, user_prompt: str, retrieved_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate meal plan using retrieved recipes and Gemini"""
        try:
            formatted_recipes = json.dumps(retrieved_recipes, indent=2)
            prompt = self.prompt_templates["meal_plan_generation"].format(
                user_prompt=user_prompt,
                retrieved_recipes=formatted_recipes
            )
            
            response = self.model.generate_content(prompt)
            result = response.text
            
            try:
                meal_plan_data = json.loads(result)
                logger.info("Successfully generated RAG meal plan")
                return meal_plan_data
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from RAG meal plan generation response")
                return self._create_fallback_meal_plan(retrieved_recipes)
                
        except Exception as e:
            logger.error(f"Error generating RAG meal plan: {e}")
            return self._create_fallback_meal_plan(retrieved_recipes)

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

    def _create_fallback_meal_plan(self, retrieved_recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a simple fallback meal plan if AI generation fails"""
        if not retrieved_recipes:
            return {
                "meal_plan": [],
                "explanation": "No recipes available to create a meal plan."
            }
        
        # Simple 3-day plan with available recipes
        meal_plan = []
        recipe_index = 0
        
        for day in range(1, 4):  # 3 days
            meals = []
            for meal_type in ["breakfast", "lunch", "dinner"]:
                if recipe_index < len(retrieved_recipes):
                    recipe = retrieved_recipes[recipe_index]
                    meals.append({
                        "meal_type": meal_type,
                        "recipe_id": recipe.get("id") or recipe.get("recipe_id"),
                        "recipe_name": recipe.get("name") or recipe.get("recipe_name", "Unknown Recipe")
                    })
                    recipe_index += 1
            
            meal_plan.append({
                "day": day,
                "meals": meals
            })
        
        return {
            "meal_plan": meal_plan,
            "explanation": "This is a basic meal plan created from available recipes. AI generation was not available."
        }