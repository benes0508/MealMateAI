from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import json

from app.repositories.meal_plan_repository import MealPlanRepository
from app.services.microservice_client import MicroserviceClient
from app.services.gemini_service import GeminiService
from app.services.embeddings_service import EmbeddingsService
from app.models.models import MealPlan, MealPlanRecipe

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MealPlanService:
    """Service for generating and managing meal plans using RAG and Gemini"""
    
    def __init__(self):
        self.meal_plan_repository = MealPlanRepository()
        self.microservice_client = MicroserviceClient()
        self.gemini_service = GeminiService()
        self.embeddings_service = EmbeddingsService()
    
    async def create_meal_plan(self,
                               db: Session,
                               user_id: int,
                               days: int = 7,
                               meals_per_day: int = 3,
                               include_snacks: bool = False,
                               additional_preferences: Optional[str] = None) -> Dict[str, Any]:
        """
        Simplified meal plan creation based on prompt, user-service, recipe-service and Gemini
        """
        # 1) Fetch user info
        user = await self.microservice_client.get_user(user_id)
        dietary_tags = user.get("dietary_tags", [])
        allergens = user.get("allergens", [])

        # 2) Fetch recipe suggestions
        recipes = await self.microservice_client.search_recipes(additional_preferences or "", dietary_tags)

        if not recipes:
            logger.error("No recipes returned from recipe-service")
            raise ValueError("No recipes available for the given preferences")

        # 3) Build prompts for Gemini
        system_prompt = (
            "You are a meal-planning assistant. Respect user dietary restrictions and allergens. "
            "If a recipe conflicts with allergies or tags, adjust it accordingly (e.g., remove cheese for kosher)."
        )
        user_prompt = (
            f"User dietary tags: {', '.join(dietary_tags)}\n"
            f"User allergens: {', '.join(allergens)}\n\n"
            f"User request: {additional_preferences}\n\n"
            f"Recipe candidates:\n{json.dumps(recipes, indent=2)}\n\n"
            f"Please propose a {days}-day meal plan with {meals_per_day} meals per day"
            + (" including snacks." if include_snacks else ".")
        )

        # 4) Call Gemini
        plan_text = self.call_gemini(system_prompt, user_prompt)

        # 5) Return plan and recipes used
        return {
            "user_id": user_id,
            "plan": plan_text,
            "recipes_used": recipes
        }
    
    async def get_meal_plan(self, db: Session, meal_plan_id: int) -> Dict[str, Any]:
        """
        Get a meal plan by ID
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            
        Returns:
            The requested meal plan
        """
        try:
            # Get the meal plan from the database
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                raise ValueError(f"Meal plan {meal_plan_id} not found")
            
            # Get the recipes for the meal plan
            db_recipes = self.meal_plan_repository.get_meal_plan_recipes(db, meal_plan_id)
            
            # Parse the plan data
            plan_data = json.loads(db_meal_plan.plan_data)
            
            # Return the meal plan
            return {
                "id": db_meal_plan.id,
                "user_id": db_meal_plan.user_id,
                "plan_name": db_meal_plan.plan_name,
                "created_at": db_meal_plan.created_at,
                "days": db_meal_plan.days,
                "meals_per_day": db_meal_plan.meals_per_day,
                "plan_explanation": db_meal_plan.plan_explanation,
                "meal_plan": plan_data,
                "recipes": [
                    {
                        "recipe_id": recipe.recipe_id,
                        "day": recipe.day,
                        "meal_type": recipe.meal_type
                    } for recipe in db_recipes
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting meal plan: {e}")
            raise
    
    async def get_user_meal_plans(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all meal plans for a user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List of meal plans for the user
        """
        try:
            # Get the meal plans from the database
            db_meal_plans = self.meal_plan_repository.get_user_meal_plans(db, user_id)
            
            # Return the meal plans with required fields for MealPlanResponse schema
            return [
                {
                    "id": plan.id,
                    "user_id": plan.user_id,
                    "plan_name": plan.plan_name,
                    "created_at": plan.created_at,
                    "days": plan.days,
                    "meals_per_day": plan.meals_per_day,
                    "plan_explanation": plan.plan_explanation or "",  # Add required field
                    "recipes": []  # Add empty recipes array to satisfy schema
                } for plan in db_meal_plans
            ]
            
        except Exception as e:
            logger.error(f"Error getting user meal plans: {e}")
            # Return an empty list instead of raising an error
            # This prevents 500 errors when a user has no meal plans
            return []
    
    async def process_text_input(self, db: Session, user_id: int, input_text: str) -> Dict[str, Any]:
        """
        Process natural language text input to create a meal plan
        
        Args:
            db: Database session
            user_id: User ID
            input_text: Natural language text input
            
        Returns:
            The created meal plan
        """
        try:
            # Default values
            days = 7
            meals_per_day = 3
            include_snacks = False
            
            # Parse the input text to extract preferences
            if "snack" in input_text.lower():
                include_snacks = True
            
            # Look for number of days
            if "days" in input_text.lower():
                input_parts = input_text.lower().split()
                for i, part in enumerate(input_parts):
                    if part == "days" and i > 0:
                        try:
                            days = int(input_parts[i-1])
                        except ValueError:
                            pass
            
            # Use the input text as additional preferences
            additional_preferences = input_text
            
            # Create the meal plan with RAG and Gemini
            meal_plan = await self.create_meal_plan(
                db=db,
                user_id=user_id,
                days=days,
                meals_per_day=meals_per_day,
                include_snacks=include_snacks,
                additional_preferences=additional_preferences
            )
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            raise
    
    async def generate_grocery_list(self, db: Session, meal_plan_id: int) -> Dict[str, Any]:
        """
        Generate a grocery list for a meal plan using Gemini
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            
        Returns:
            Grocery list for the meal plan
        """
        try:
            # Get the meal plan from the database
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                raise ValueError(f"Meal plan {meal_plan_id} not found")
            
            # Get the recipes for the meal plan
            db_recipes = self.meal_plan_repository.get_meal_plan_recipes(db, meal_plan_id)
            
            # Fetch recipe details from recipe-service
            recipes_details = []
            for db_recipe in db_recipes:
                recipe_detail = await self.microservice_client.get_recipe(db_recipe.recipe_id)
                if recipe_detail:
                    recipes_details.append(recipe_detail)
            
            # Generate the grocery list using Gemini
            grocery_list_result = self.gemini_service.generate_grocery_list(recipes_details)
            
            return grocery_list_result
            
        except Exception as e:
            logger.error(f"Error generating grocery list: {e}")
            raise
    
    async def delete_meal_plan(self, db: Session, meal_plan_id: int) -> bool:
        """
        Delete a meal plan
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get the meal plan from the database
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                return False
            
            # Delete the meal plan
            self.meal_plan_repository.delete_meal_plan(db, meal_plan_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting meal plan: {e}")
            return False
    
    async def move_meal(self, db: Session, meal_plan_id: int, recipe_id: int, to_day: int, to_meal_type: str) -> bool:
        """
        Move a meal to a different day or meal type
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            recipe_id: Recipe ID within the meal plan
            to_day: Destination day
            to_meal_type: Destination meal type
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the meal plan exists
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                return False
            
            # Move the meal
            result = self.meal_plan_repository.move_meal(db, meal_plan_id, recipe_id, to_day, to_meal_type)
            
            # If successful, update the plan_data field
            if result:
                # Get all recipes for the meal plan
                db_recipes = self.meal_plan_repository.get_meal_plan_recipes(db, meal_plan_id)
                
                # Re-organize the plan data
                updated_plan = []
                for day in range(1, db_meal_plan.days + 1):
                    day_recipes = [r for r in db_recipes if r.day == day]
                    day_meals = []
                    for recipe in day_recipes:
                        day_meals.append({
                            "recipe_id": recipe.recipe_id,
                            "meal_type": recipe.meal_type,
                            "day": recipe.day
                        })
                    
                    updated_plan.append({
                        "day": day,
                        "meals": day_meals
                    })
                
                # Update the meal plan data
                self.meal_plan_repository.update_meal_plan_data(db, meal_plan_id, json.dumps(updated_plan))
                return True
            
            return result
        except Exception as e:
            logger.error(f"Error moving meal: {e}")
            return False
    
    async def swap_days(self, db: Session, meal_plan_id: int, day1: int, day2: int) -> bool:
        """
        Swap two days in a meal plan
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            day1: First day
            day2: Second day
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the meal plan exists
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                return False
            
            # Check if the days are valid
            if day1 < 1 or day1 > db_meal_plan.days or day2 < 1 or day2 > db_meal_plan.days:
                logger.error(f"Invalid days: {day1}, {day2}")
                return False
            
            # Swap the days
            result = self.meal_plan_repository.swap_meal_plan_days(db, meal_plan_id, day1, day2)
            
            # If successful, update the plan_data field
            if result:
                # Get all recipes for the meal plan
                db_recipes = self.meal_plan_repository.get_meal_plan_recipes(db, meal_plan_id)
                
                # Re-organize the plan data
                updated_plan = []
                for day in range(1, db_meal_plan.days + 1):
                    day_recipes = [r for r in db_recipes if r.day == day]
                    day_meals = []
                    for recipe in day_recipes:
                        day_meals.append({
                            "recipe_id": recipe.recipe_id,
                            "meal_type": recipe.meal_type,
                            "day": recipe.day
                        })
                    
                    updated_plan.append({
                        "day": day,
                        "meals": day_meals
                    })
                
                # Update the meal plan data
                self.meal_plan_repository.update_meal_plan_data(db, meal_plan_id, json.dumps(updated_plan))
                return True
            
            return result
        except Exception as e:
            logger.error(f"Error swapping days: {e}")
            return False
    
    async def _get_user_preferences(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Get user preferences from cache or user-service
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            User preferences
        """
        # First check if we have cached preferences
        cached_preferences = self.meal_plan_repository.get_cached_user_preferences(db, user_id)
        
        if cached_preferences:
            return cached_preferences
        
        # If not, fetch from user-service and cache
        preferences = {}
        
        # Get allergies
        allergies = await self.microservice_client.get_user_allergies(user_id)
        if allergies:
            preferences["allergies"] = allergies.get("allergies", [])
        else:
            preferences["allergies"] = []
        
        # Get dietary restrictions
        diet_restrictions = await self.microservice_client.get_user_diet_restrictions(user_id)
        if diet_restrictions:
            preferences["dietary_restrictions"] = diet_restrictions.get("dietary_restrictions", [])
        else:
            preferences["dietary_restrictions"] = []
        
        # Get user preferences
        user_prefs = await self.microservice_client.get_user_preferences(user_id)
        if user_prefs:
            preferences["cuisine_preferences"] = user_prefs.get("cuisine_preferences", [])
            preferences["disliked_ingredients"] = user_prefs.get("disliked_ingredients", [])
        else:
            preferences["cuisine_preferences"] = []
            preferences["disliked_ingredients"] = []
        
        # Cache the preferences
        self.meal_plan_repository.cache_user_preferences(db, user_id, preferences)
        
        return preferences
    def call_gemini(self, system_prompt: str, user_prompt: str) -> str:
        """
        Proxy method to invoke GeminiService
        """
        return self.gemini_service.generate_content(system_prompt, user_prompt)