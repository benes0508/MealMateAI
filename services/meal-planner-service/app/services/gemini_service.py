import os
import json
import logging
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate

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
        self.model_name = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro") 
        
        # Initialize the LLM
        self.llm = ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )

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
            
            # Create the prompt template
            prompt_template = self._create_meal_plan_prompt_template()
            
            # Create the LLM chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt_template
            )
            
            # Run the chain to get the meal plan
            result = chain.run({
                "recipe_context": json.dumps(recipe_context, indent=2),
                "dietary_restrictions": ", ".join(dietary_restrictions) if dietary_restrictions else "None",
                "allergies": ", ".join(allergies) if allergies else "None",
                "cuisine_preferences": ", ".join(cuisine_preferences) if cuisine_preferences else "None",
                "disliked_ingredients": ", ".join(disliked_ingredients) if disliked_ingredients else "None",
                "days": days,
                "meals_per_day": meals_per_day,
                "include_snacks": "yes" if include_snacks else "no",
                "additional_preferences": additional_preferences if additional_preferences else "None",
            })
            
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
            
            # Create the prompt template
            prompt_template = self._create_grocery_list_prompt_template()
            
            # Create the LLM chain
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt_template
            )
            
            # Run the chain to get the grocery list
            result = chain.run({
                "ingredients": json.dumps(all_ingredients, indent=2)
            })
            
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
    
    def _create_meal_plan_prompt_template(self) -> PromptTemplate:
        """Create prompt template for meal plan generation"""
        template = """
        You are a meal planning assistant that creates healthy and balanced meal plans based on user preferences and available recipes.
        
        Create a {days}-day meal plan with {meals_per_day} meals per day, optimized for the user's preferences.
        
        USER PREFERENCES:
        Dietary Restrictions: {dietary_restrictions}
        Allergies: {allergies}
        Preferred cuisines: {cuisine_preferences}
        Disliked ingredients: {disliked_ingredients}
        Include snacks: {include_snacks}
        Additional preferences: {additional_preferences}
        
        RETRIEVED RECIPES (these are retrieved based on relevance to user preferences):
        {recipe_context}
        
        INSTRUCTIONS:
        1. Create a meal plan for {days} days, with {meals_per_day} meals per day
        2. Only select recipes from the RETRIEVED RECIPES list 
        3. Consider the user's dietary restrictions, allergies, and preferences
        4. Ensure a good variety of meal types
        5. Aim for nutritional balance across the week
        6. Include a brief explanation of why this meal plan was chosen
        
        Return your response as a JSON object with the following structure:
        {{
            "meal_plan": [
                {{
                    "day": 1,
                    "meals": [
                        {{
                            "meal_type": "breakfast|lunch|dinner|snack",
                            "recipe_id": 123,
                            "recipe_name": "Recipe Name"
                        }},
                        // more meals...
                    ]
                }},
                // more days...
            ],
            "explanation": "A brief explanation of the meal plan"
        }}
        
        Make sure to output valid JSON.
        """
        
        return PromptTemplate(
            template=template,
            input_variables=[
                "recipe_context", 
                "dietary_restrictions", 
                "allergies", 
                "cuisine_preferences", 
                "disliked_ingredients", 
                "days", 
                "meals_per_day", 
                "include_snacks", 
                "additional_preferences"
            ]
        )
    
    def _create_grocery_list_prompt_template(self) -> PromptTemplate:
        """Create prompt template for grocery list generation"""
        template = """
        You are a helpful assistant that creates optimized grocery lists from recipe ingredients.
        
        Based on the following ingredients from recipes, create an optimized grocery list:
        
        INGREDIENTS:
        {ingredients}
        
        INSTRUCTIONS:
        1. Combine identical or similar ingredients
        2. Group items by grocery store categories (produce, dairy, meat, etc.)
        3. Standardize units where possible
        4. Include quantities needed
        
        Return the grocery list as a JSON object with the following structure:
        {{
            "grocery_list": [
                {{
                    "category": "Produce",
                    "items": [
                        {{
                            "name": "Ingredient name",
                            "amount": "Quantity needed"
                        }},
                        // more items...
                    ]
                }},
                // more categories...
            ]
        }}
        
        Make sure to output valid JSON.
        """
        
        return PromptTemplate(
            template=template,
            input_variables=["ingredients"]
        )
        
    def _create_fallback_meal_plan(self, retrieved_recipes: List[Dict[str, Any]], days: int, meals_per_day: int) -> Dict[str, Any]:
        """Creates a fallback meal plan if the API call fails"""
        
        # Simple assignment of recipes to days and meal types
        meal_plan = []
        recipe_index = 0
        meal_types = ["breakfast", "lunch", "dinner"]
        
        for day in range(1, days + 1):
            meals = []
            for i in range(meals_per_day):
                meal_type = meal_types[i % len(meal_types)]
                recipe = retrieved_recipes[recipe_index % len(retrieved_recipes)]
                recipe_index += 1
                
                meals.append({
                    "meal_type": meal_type,
                    "recipe_id": recipe["recipe_id"],
                    "recipe_name": recipe["recipe_name"]
                })
            
            meal_plan.append({
                "day": day,
                "meals": meals
            })
        
        return {
            "meal_plan": meal_plan,
            "explanation": "This is a simple meal plan based on retrieved recipes. We weren't able to optimize it based on your preferences due to a technical issue."
        }
        
    def _create_fallback_grocery_list(self, ingredients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Creates a fallback grocery list if the API call fails"""
        
        # Simple grouping of ingredients
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