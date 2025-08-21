from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import json

from app.repositories.meal_plan_repository import MealPlanRepository
from app.services.microservice_client import MicroserviceClient
from app.services.gemini_service import GeminiService
# from app.services.embeddings_service import EmbeddingsService
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
        # self.embeddings_service = EmbeddingsService()
    
    async def create_meal_plan(self, 
                           db: Session,
                           user_id: int,
                           days: int = 7,
                           meals_per_day: int = 3,
                           include_snacks: bool = False,
                           additional_preferences: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new meal plan for a user using RAG and Gemini
        
        Args:
            db: Database session
            user_id: User ID
            days: Number of days for the meal plan
            meals_per_day: Number of meals per day
            include_snacks: Whether to include snacks
            additional_preferences: Additional preferences specified by the user
            
        Returns:
            The created meal plan
        """
        try:
            # Step 1: Fetch user preferences from cache or user-service
            user_preferences = await self._get_user_preferences(db, user_id)
            
            # Step 2: Fetch recipes from recipe-service
            all_recipes = await self.microservice_client.get_recipes()
            if not all_recipes:
                logger.error("Failed to fetch recipes")
                raise ValueError("Failed to fetch recipes")
            
            # Step 3: Index recipes for vector search if not already done
            # await self.embeddings_service.batch_store_recipe_embeddings(db, all_recipes)
            
            # Step 4: Retrieve relevant recipes using RAG based on user preferences
            limit = min(30, len(all_recipes))  # Limit the number of retrieved recipes
            # Use all recipes as fallback since embeddings service is disabled
            retrieved_recipes = all_recipes[:limit]
            
            if not retrieved_recipes:
                logger.warning("No recipes found matching user preferences, using all recipes")
                # If no recipes match preferences, use the first 30 recipes
                retrieved_recipes = [
                    {
                        "recipe_id": recipe["id"],
                        "recipe_name": recipe["name"],
                        "ingredients": ", ".join([i["name"] for i in recipe.get("ingredients", [])]),
                        "cuisine_type": recipe.get("cuisine_type", "")
                    }
                    for recipe in all_recipes[:30]
                ]
            
            # Step 5: Generate meal plan using Gemini LLM
            meal_plan_result = self.gemini_service.generate_meal_plan(
                user_preferences=user_preferences,
                retrieved_recipes=retrieved_recipes,
                days=days,
                meals_per_day=meals_per_day,
                include_snacks=include_snacks,
                additional_preferences=additional_preferences
            )
            
            # Step 6: Save the meal plan to the database
            # Create a name for the meal plan based on days
            plan_name = f"{days}-Day Meal Plan"
            
            # Add additional context if available
            if additional_preferences:
                plan_name += f" ({additional_preferences.split()[0]}...)"
            
            # Create the meal plan in the database
            db_meal_plan = self.meal_plan_repository.create_meal_plan(
                db=db,
                user_id=user_id,
                plan_name=plan_name,
                days=days,
                meals_per_day=meals_per_day,
                plan_data=json.dumps(meal_plan_result["meal_plan"]),
                plan_explanation=meal_plan_result["explanation"]
            )
            
            # Step 7: Add recipes to the meal plan
            for day_plan in meal_plan_result["meal_plan"]:
                day = day_plan["day"]
                for meal in day_plan["meals"]:
                    self.meal_plan_repository.add_recipe_to_meal_plan(
                        db=db,
                        meal_plan_id=db_meal_plan.id,
                        recipe_id=meal["recipe_id"],
                        day=day,
                        meal_type=meal["meal_type"]
                    )
            
            # Return the created meal plan
            return {
                "id": db_meal_plan.id,
                "user_id": db_meal_plan.user_id,
                "plan_name": db_meal_plan.plan_name,
                "created_at": db_meal_plan.created_at,
                "days": db_meal_plan.days,
                "meals_per_day": db_meal_plan.meals_per_day,
                "plan_explanation": db_meal_plan.plan_explanation,
                "meal_plan": meal_plan_result["meal_plan"]
            }
            
        except Exception as e:
            logger.error(f"Error creating meal plan: {e}")
            raise
    
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
            
            # Get recipe details from recipe service for each recipe
            recipes_with_details = []
            for recipe in db_recipes:
                recipe_detail = await self.microservice_client.get_recipe(recipe.recipe_id)
                recipes_with_details.append({
                    "id": recipe.id,
                    "recipe_id": recipe.recipe_id,
                    "day": recipe.day,
                    "meal_type": recipe.meal_type,
                    "name": recipe_detail.get("name") if recipe_detail else f"Recipe {recipe.recipe_id}",
                    "title": recipe_detail.get("name") if recipe_detail else f"Recipe {recipe.recipe_id}",
                    "description": recipe_detail.get("description", ""),
                    "ingredients": [ing.get("name", str(ing)) if isinstance(ing, dict) else str(ing) for ing in recipe_detail.get("ingredients", [])] if recipe_detail else []
                })

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
                "recipes": recipes_with_details
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
        Process natural language text input to create a meal plan and save it to database
        
        Args:
            db: Database session
            user_id: User ID
            input_text: Natural language text input
            
        Returns:
            The created and saved meal plan
        """
        try:
            logger.debug(f"DEBUG: process_text_input service called with user_id={user_id}, input_text='{input_text}'")
            
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
            
            logger.debug(f"DEBUG: About to call create_rag_meal_plan with user_prompt='{input_text}'")
            
            # Create the meal plan using RAG workflow
            rag_response = await self.create_rag_meal_plan(
                db=db,
                user_id=user_id,
                user_prompt=input_text
            )
            
            logger.debug(f"DEBUG: create_rag_meal_plan returned: {rag_response}")
            
            # Get user preferences for conversation context
            try:
                user_preferences = await self._get_user_preferences(db, user_id)
            except Exception as e:
                logger.warning(f"Failed to get user preferences: {e}")
                user_preferences = {}
            
            # Extract plan name from explanation or create default
            plan_name = "AI Generated Meal Plan"
            if rag_response.get("explanation"):
                if "vegetarian" in input_text.lower():
                    plan_name = f"{days}-Day Vegetarian Meal Plan"
                elif "vegan" in input_text.lower():
                    plan_name = f"{days}-Day Vegan Meal Plan"
                else:
                    plan_name = f"{days}-Day Personalized Meal Plan"
            
            # Try to get user's meal plan history for context (optional)
            try:
                user_meal_plans = await self.get_user_meal_plans(db, user_id)
                meal_plan_history = [plan["id"] for plan in user_meal_plans[:3]]  # Last 3 meal plans
            except:
                meal_plan_history = []
            
            # Create conversation context for saving with meal plan (optional enhancement)
            try:
                conversation_context = self._create_conversation_context(
                    user_prompt=input_text,
                    rag_response=rag_response,
                    user_preferences=user_preferences or {},
                    meal_plan_history=meal_plan_history
                )
                conversation_title = self._generate_conversation_title(input_text)
                
                # Save the meal plan with conversation context
                db_meal_plan = self.meal_plan_repository.create_meal_plan(
                    db=db,
                    user_id=user_id,
                    plan_name=plan_name,
                    days=days,
                    meals_per_day=meals_per_day,
                    plan_data=json.dumps(rag_response.get("meal_plan", [])),
                    plan_explanation=rag_response.get("explanation", "Your personalized meal plan created by AI."),
                    conversation_data=json.dumps(conversation_context),
                    conversation_title=conversation_title,
                    original_prompt=input_text
                )
            except Exception as e:
                logger.warning(f"Failed to save conversation context (database may not support it): {e}")
                # Fallback to basic meal plan creation
                db_meal_plan = self.meal_plan_repository.create_meal_plan(
                    db=db,
                    user_id=user_id,
                    plan_name=plan_name,
                    days=days,
                    meals_per_day=meals_per_day,
                    plan_data=json.dumps(rag_response.get("meal_plan", [])),
                    plan_explanation=rag_response.get("explanation", "Your personalized meal plan created by AI.")
                )
            
            # Add recipes to the meal plan
            meal_plan_data = rag_response.get("meal_plan", [])
            for day_plan in meal_plan_data:
                day = day_plan.get("day", 1)
                for meal in day_plan.get("meals", []):
                    recipe_id = meal.get("recipe_id")
                    if recipe_id:
                        self.meal_plan_repository.add_recipe_to_meal_plan(
                            db=db,
                            meal_plan_id=db_meal_plan.id,
                            recipe_id=recipe_id,
                            day=day,
                            meal_type=meal.get("meal_type", "meal")
                        )
            
            # Return the saved meal plan
            result = {
                "id": db_meal_plan.id,  # Real database ID
                "days": db_meal_plan.days,
                "plan_name": db_meal_plan.plan_name,
                "plan_explanation": db_meal_plan.plan_explanation,
                "created_at": db_meal_plan.created_at.isoformat(),
                "user_id": db_meal_plan.user_id,
                "meals_per_day": db_meal_plan.meals_per_day,
                "recipes": self._convert_to_recipes_format(meal_plan_data),
                "meal_plan": rag_response,
                "conversation_id": f"saved-{db_meal_plan.id}",
                "status": "saved"
            }
            
            logger.debug(f"DEBUG: Final result being returned with database ID {db_meal_plan.id}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing text input: {e}")
            raise
    
    def _convert_to_recipes_format(self, meal_plan_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert meal plan format to recipes format expected by frontend"""
        recipes = []
        for day_plan in meal_plan_data:
            day = day_plan.get("day", 1)
            for meal in day_plan.get("meals", []):
                recipes.append({
                    "id": len(recipes) + 1,  # Sequential ID for frontend
                    "recipe_id": meal.get("recipe_id"),
                    "day": day,
                    "meal_type": meal.get("meal_type"),
                    "name": meal.get("recipe_name"),
                    "title": meal.get("recipe_name"),  # Some parts of frontend expect 'title'
                    "description": f"{meal.get('meal_type', '').title()} for day {day}"
                })
        return recipes
    
    async def generate_grocery_list(self, db: Session, meal_plan_id: int, force_regenerate: bool = False) -> Dict[str, Any]:
        """
        Generate or retrieve cached grocery list for a meal plan
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            force_regenerate: If True, regenerate even if cached version exists
            
        Returns:
            Grocery list for the meal plan
        """
        try:
            # Get the meal plan from the database
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                raise ValueError(f"Meal plan {meal_plan_id} not found")
            
            # Check if we have a cached grocery list and it's not a forced regeneration
            if not force_regenerate and db_meal_plan.grocery_list and db_meal_plan.grocery_list_generated_at:
                logger.info(f"Returning cached grocery list for meal plan {meal_plan_id}")
                try:
                    import json
                    cached_grocery_list = json.loads(db_meal_plan.grocery_list)
                    return cached_grocery_list
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Invalid cached grocery list data for meal plan {meal_plan_id}: {e}")
                    # Fall through to regenerate
            
            # Generate new grocery list
            logger.info(f"Generating new grocery list for meal plan {meal_plan_id}")
            
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
            
            # Cache the grocery list in the database
            await self._cache_grocery_list(db, meal_plan_id, grocery_list_result)
            
            return grocery_list_result
            
        except Exception as e:
            logger.error(f"Error generating grocery list: {e}")
            raise
    
    async def _cache_grocery_list(self, db: Session, meal_plan_id: int, grocery_list_data: Dict[str, Any]):
        """Cache grocery list data in the meal plan record"""
        try:
            import json
            from datetime import datetime
            
            # Get the meal plan
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if db_meal_plan:
                # Update with cached grocery list
                db_meal_plan.grocery_list = json.dumps(grocery_list_data)
                db_meal_plan.grocery_list_generated_at = datetime.utcnow()
                db.commit()
                logger.info(f"Cached grocery list for meal plan {meal_plan_id}")
        except Exception as e:
            logger.error(f"Failed to cache grocery list for meal plan {meal_plan_id}: {e}")
            # Don't raise - caching failure shouldn't break the main functionality
    
    async def _clear_grocery_list_cache(self, db: Session, meal_plan_id: int):
        """Clear cached grocery list when meal plan is modified"""
        try:
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if db_meal_plan and db_meal_plan.grocery_list:
                db_meal_plan.grocery_list = None
                db_meal_plan.grocery_list_generated_at = None
                db.commit()
                logger.info(f"Cleared grocery list cache for meal plan {meal_plan_id}")
        except Exception as e:
            logger.error(f"Failed to clear grocery list cache for meal plan {meal_plan_id}: {e}")
            # Don't raise - cache clearing failure shouldn't break the main functionality
    
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
    
    async def move_meal(self, db: Session, meal_plan_id: int, recipe_id: int, to_day: int, to_meal_type: str, from_day: int = None, from_meal_type: str = None) -> bool:
        """
        Move a meal to a different day or meal type
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            recipe_id: Recipe ID within the meal plan
            to_day: Destination day
            to_meal_type: Destination meal type
            from_day: Source day (optional for more precise matching)
            from_meal_type: Source meal type (optional for more precise matching)
            
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
            result = self.meal_plan_repository.move_meal(db, meal_plan_id, recipe_id, to_day, to_meal_type, from_day, from_meal_type)
            
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
                
                # Clear grocery list cache since meal plan changed
                await self._clear_grocery_list_cache(db, meal_plan_id)
                
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
                
                # Clear grocery list cache since meal plan changed
                await self._clear_grocery_list_cache(db, meal_plan_id)
                
                return True
            
            return result
        except Exception as e:
            logger.error(f"Error swapping days: {e}")
            return False
    
    async def reorder_days(self, db: Session, meal_plan_id: int, day_order: List[int]) -> bool:
        """
        Reorder days in a meal plan
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            day_order: New order of days by their original day numbers
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the meal plan exists
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                return False
            
            # Validate the day_order
            if len(day_order) != db_meal_plan.days:
                logger.error(f"Day order length ({len(day_order)}) doesn't match meal plan days ({db_meal_plan.days})")
                return False
            
            # Check that all days are present and valid
            expected_days = set(range(1, db_meal_plan.days + 1))
            provided_days = set(day_order)
            if expected_days != provided_days:
                logger.error(f"Invalid day order: {day_order}. Expected days: {expected_days}")
                return False
            
            # Reorder the days
            result = self.meal_plan_repository.reorder_meal_plan_days(db, meal_plan_id, day_order)
            
            # Clear grocery list cache since meal plan changed
            if result:
                await self._clear_grocery_list_cache(db, meal_plan_id)
            
            return result
        except Exception as e:
            logger.error(f"Error reordering days: {e}")
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
            # Add the rich preferences JSON field data
            preferences["cooking_preferences"] = user_prefs.get("preferences", {}).get("cooking_style", [])
            preferences["meal_timing"] = user_prefs.get("preferences", {}).get("meal_timing", {})
            preferences["portion_preferences"] = user_prefs.get("preferences", {}).get("portion_size", "medium")
            preferences["spice_tolerance"] = user_prefs.get("preferences", {}).get("spice_level", "medium")
            preferences["texture_preferences"] = user_prefs.get("preferences", {}).get("texture_likes", [])
        else:
            preferences["cuisine_preferences"] = []
            preferences["disliked_ingredients"] = []
            preferences["cooking_preferences"] = []
            preferences["meal_timing"] = {}
            preferences["portion_preferences"] = "medium"
            preferences["spice_tolerance"] = "medium"
            preferences["texture_preferences"] = []
        
        # Cache the preferences
        self.meal_plan_repository.cache_user_preferences(db, user_id, preferences)
        
        return preferences

    async def create_rag_meal_plan(self, db: Session, user_id: int, user_prompt: str) -> Dict[str, Any]:
        """Complete RAG workflow: Generate meal plan from user prompt using AI recommendations"""
        try:
            logger.info("="*80)
            logger.info("🧠 STARTING RAG MEAL PLAN THINKING PROCESS")
            logger.info("="*80)
            
            # Step 1: Get user preferences for enhanced AI recommendations
            logger.info("📋 STEP 1: Gathering User Context")
            user_preferences = await self._get_user_preferences(db, user_id)
            logger.info(f"👤 User ID: {user_id}")
            logger.info(f"💬 Original Prompt: '{user_prompt}'")
            logger.info(f"🎯 User Preferences Retrieved:")
            logger.info(f"   • Dietary Restrictions: {user_preferences.get('dietary_restrictions', [])}")
            logger.info(f"   • Allergies: {user_preferences.get('allergies', [])}")
            logger.info(f"   • Cuisine Preferences: {user_preferences.get('cuisine_preferences', [])}")
            logger.info(f"   • Cooking Style: {user_preferences.get('cooking_preferences', [])}")
            logger.info(f"   • Spice Tolerance: {user_preferences.get('spice_tolerance', 'unknown')}")
            logger.info(f"   • Portion Preference: {user_preferences.get('portion_preferences', 'unknown')}")
            
            # Step 2: Check for user's recent meal plans to add context
            logger.info("\n📚 STEP 2: Analyzing Meal Plan History")
            try:
                user_meal_plans = await self.get_user_meal_plans(db, user_id)
                meal_plan_history = [plan["id"] for plan in user_meal_plans[:3]]  # Last 3 meal plans
                logger.info(f"🗂️ Recent Meal Plans (last 3): {meal_plan_history}")
                if user_meal_plans:
                    for i, plan in enumerate(user_meal_plans[:3]):
                        logger.info(f"   Plan {i+1}: {plan.get('plan_name', 'Unknown')} (ID: {plan.get('id')})")
                else:
                    logger.info("   ⚪ No previous meal plans found - first time user")
            except Exception as e:
                logger.error(f"Error getting user meal plans: {e}")
                logger.info(f"🗂️ Recent Meal Plans (last 3): []")
                logger.info("   ⚪ No previous meal plans found - first time user")
                meal_plan_history = []
            
            # Step 3: Use AI-powered recipe recommendations instead of basic queries
            logger.info("\n🤖 STEP 3: AI-Powered Recipe Recommendations")
            logger.info(f"🔍 Searching for recipes with enhanced context...")
            retrieved_recipes = await self._search_recipes_with_ai_recommendations(
                user_prompt=user_prompt,
                user_preferences=user_preferences,
                max_results=50
            )
            
            if not retrieved_recipes:
                return {
                    "meal_plan": [],
                    "explanation": "No suitable recipes found for your request. Please try a different query.",
                    "ai_analysis": "No AI analysis available",
                    "recipes_found": 0
                }
            
            # Step 4: Generate meal plan using AI-retrieved recipes
            logger.info(f"\n🎭 STEP 4: Meal Plan Generation with {len(retrieved_recipes)} recipes")
            meal_plan = self.gemini_service.generate_rag_meal_plan(user_prompt, retrieved_recipes)
            
            # Add enhanced metadata
            logger.info(f"\n📊 STEP 5: Adding Enhanced Metadata")
            meal_plan["ai_enhanced"] = True
            meal_plan["recipes_found"] = len(retrieved_recipes)
            meal_plan["user_prompt"] = user_prompt
            meal_plan["user_preferences_applied"] = bool(user_preferences)
            
            # Add recipe quality metrics
            if retrieved_recipes:
                avg_similarity = sum(r.get("similarity_score", 0) for r in retrieved_recipes) / len(retrieved_recipes)
                meal_plan["avg_recipe_similarity"] = avg_similarity
                meal_plan["recipe_collections"] = list(set(r.get("cuisine_type", "") for r in retrieved_recipes if r.get("cuisine_type")))
                
                logger.info(f"📈 Quality Metrics:")
                logger.info(f"   • Average Recipe Similarity: {avg_similarity:.3f}")
                logger.info(f"   • Collections Used: {meal_plan['recipe_collections']}")
                logger.info(f"   • User Preferences Applied: {meal_plan['user_preferences_applied']}")
            
            logger.info("="*80)
            logger.info("🎉 RAG MEAL PLAN THINKING PROCESS COMPLETE")
            logger.info("="*80)
            logger.info(f"✅ Final Meal Plan Generated:")
            logger.info(f"   • Recipes Found: {meal_plan['recipes_found']}")
            logger.info(f"   • AI Enhanced: {meal_plan['ai_enhanced']}")
            logger.info(f"   • Processing Quality: {avg_similarity:.3f} average similarity")
            logger.info(f"   • Collections: {len(meal_plan['recipe_collections'])} different types")
            logger.info("="*80)
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced RAG meal plan creation: {e}")
            # Fallback to basic method
            try:
                logger.info("Falling back to basic meal plan generation")
                queries = self.gemini_service.generate_search_queries(user_prompt)
                fallback_recipes = await self._search_recipes_with_multiple_queries_fallback(user_prompt)
                
                if fallback_recipes:
                    meal_plan = self.gemini_service.generate_rag_meal_plan(user_prompt, fallback_recipes)
                    meal_plan["ai_enhanced"] = False
                    meal_plan["fallback_used"] = True
                    meal_plan["recipes_found"] = len(fallback_recipes)
                    return meal_plan
            except Exception as fallback_error:
                logger.error(f"Fallback meal plan creation also failed: {fallback_error}")
            
            return {
                "meal_plan": [],
                "explanation": f"An error occurred while generating your meal plan: {str(e)}",
                "ai_enhanced": False,
                "error": True,
                "recipes_found": 0
            }

    async def modify_rag_meal_plan(self, current_meal_plan: Dict[str, Any], user_feedback: str) -> Dict[str, Any]:
        """Step 4: Modify existing meal plan based on user feedback"""
        try:
            # Generate modification queries based on feedback
            modification_queries = self.gemini_service.generate_modification_queries(current_meal_plan, user_feedback)
            
            # Search for new recipes based on modification queries
            new_recipes = await self._search_recipes_with_multiple_queries(modification_queries)
            
            # Generate modified meal plan
            modified_plan = self.gemini_service.modify_meal_plan(current_meal_plan, user_feedback, new_recipes)
            
            # Add metadata
            modified_plan["modification_queries"] = modification_queries
            modified_plan["new_recipes_found"] = len(new_recipes)
            
            return modified_plan
            
        except Exception as e:
            logger.error(f"Error modifying RAG meal plan: {e}")
            return current_meal_plan

    def _convert_user_prompt_to_conversation(self, user_prompt: str) -> List[Dict[str, str]]:
        """Convert a user prompt to conversation format for RAG system"""
        return [
            {
                "role": "user", 
                "content": user_prompt
            }
        ]
    
    def _convert_recipe_recommendations_to_meal_plan_format(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert Recipe Service recommendations to meal plan format"""
        converted_recipes = []
        
        for rec in recommendations:
            # Handle both old format and new RAG format
            recipe_data = {
                "id": rec.get("recipe_id") or rec.get("id"),
                "recipe_id": rec.get("recipe_id") or rec.get("id"),
                "recipe_name": rec.get("title") or rec.get("name"),
                "ingredients": rec.get("ingredients_preview", []) or rec.get("ingredients", []),
                "cuisine_type": rec.get("collection", ""),
                "summary": rec.get("summary", ""),
                "similarity_score": rec.get("similarity_score", 0.0),
                "confidence": rec.get("confidence", 0.0)
            }
            converted_recipes.append(recipe_data)
        
        return converted_recipes

    async def _search_recipes_with_ai_recommendations(self, user_prompt: str, user_preferences: Optional[Dict[str, Any]] = None, max_results: int = 50) -> List[Dict[str, Any]]:
        """Search recipes using AI-powered recommendations from Recipe Service"""
        try:
            logger.info("🔄 Converting prompt to conversation format...")
            # Convert user prompt to conversation format
            conversation_history = self._convert_user_prompt_to_conversation(user_prompt)
            logger.info(f"💬 Conversation History Sent to Recipe Service:")
            import json
            logger.info(json.dumps(conversation_history, indent=4))
            
            logger.info(f"\n📤 Sending Request to Recipe Service RAG System:")
            logger.info(f"   • Max Results: {max_results}")
            logger.info(f"   • User Preferences Included: {bool(user_preferences)}")
            if user_preferences:
                logger.info(f"   • Preferences Data: {json.dumps(user_preferences, indent=6)}")
            
            # Get AI-powered recommendations
            logger.info(f"\n⚡ Calling Recipe Service /recommendations endpoint...")
            ai_response = await self.microservice_client.get_ai_recommendations(
                conversation_history=conversation_history,
                max_results=max_results,
                user_preferences=user_preferences
            )
            
            logger.info(f"📥 Recipe Service Response Status: {ai_response.get('status', 'unknown')}")
            logger.info(f"🔢 Total Results Returned: {ai_response.get('total_results', 0)}")
            
            if ai_response.get("status") == "success" and ai_response.get("recommendations"):
                recommendations = ai_response["recommendations"]
                logger.info(f"✅ SUCCESS: AI recommendations returned {len(recommendations)} recipes")
                
                # Log query analysis from Recipe Service
                if "query_analysis" in ai_response:
                    query_analysis = ai_response["query_analysis"]
                    logger.info(f"\n🔍 Recipe Service Query Analysis:")
                    logger.info(f"   • Detected Preferences: {query_analysis.get('detected_preferences', [])}")
                    logger.info(f"   • Detected Restrictions: {query_analysis.get('detected_restrictions', [])}")
                    logger.info(f"   • Meal Context: {query_analysis.get('meal_context', 'None')}")
                    logger.info(f"   • Collections Searched: {query_analysis.get('collections_searched', [])}")
                    logger.info(f"   • Processing Time: {query_analysis.get('processing_time_ms', 0)}ms")
                    
                    if "generated_queries" in query_analysis:
                        logger.info(f"\n🎯 Generated Queries by Collection:")
                        for collection, queries in query_analysis["generated_queries"].items():
                            logger.info(f"     {collection}: {queries}")
                
                # Log sample of retrieved recipes
                logger.info(f"\n📋 Sample Retrieved Recipes (top 5):")
                for i, recipe in enumerate(recommendations[:5]):
                    logger.info(f"   {i+1}. {recipe.get('title', 'Unknown')} (Collection: {recipe.get('collection', 'N/A')}, Score: {recipe.get('similarity_score', 0):.3f})")
                
                # Convert to meal plan format and add user preferences for context
                logger.info(f"\n🔄 Converting {len(recommendations)} recipes to meal plan format...")
                converted_recipes = self._convert_recipe_recommendations_to_meal_plan_format(recommendations)
                
                # Add user preferences to first recipe for context passing to Gemini
                if converted_recipes and user_preferences:
                    converted_recipes[0]["user_preferences"] = user_preferences
                    logger.info(f"✅ Added user preferences to recipe data for Gemini context")
                
                logger.info(f"✅ Recipe conversion complete: {len(converted_recipes)} recipes ready for meal plan generation")
                return converted_recipes
            else:
                logger.warning(f"❌ AI recommendations failed or returned no results: {ai_response.get('status')}")
                logger.info(f"🔄 Falling back to basic keyword search...")
                return await self._search_recipes_with_multiple_queries_fallback(user_prompt)
                
        except Exception as e:
            logger.error(f"Error getting AI recommendations: {e}")
            return await self._search_recipes_with_multiple_queries_fallback(user_prompt)

    async def _search_recipes_with_multiple_queries_fallback(self, user_prompt: str) -> List[Dict[str, Any]]:
        """Fallback method using multiple queries (original implementation)"""
        # Extract keywords from user prompt for basic search
        keywords = ["healthy", "vegetarian", "protein", "quick", "dessert", "chicken", "beef", "fish"]
        relevant_keywords = [word for word in keywords if word.lower() in user_prompt.lower()]
        
        if not relevant_keywords:
            relevant_keywords = ["chicken", "salad", "sandwich"]  # Default fallback
        
        all_recipes = []
        seen_recipe_ids = set()
        
        for query in relevant_keywords:
            logger.info(f"Fallback search with query: {query}")
            recipes = await self.microservice_client.search_recipes(query, limit=20)
            
            # Add unique recipes
            for recipe in recipes:
                recipe_id = recipe.get("id") or recipe.get("recipe_id")
                if recipe_id and recipe_id not in seen_recipe_ids:
                    # Convert to consistent format
                    recipe_data = {
                        "id": recipe_id,
                        "recipe_id": recipe_id,
                        "recipe_name": recipe.get("name", "Unknown Recipe"),
                        "ingredients": recipe.get("ingredients", []),
                        "cuisine_type": recipe.get("tags", [{}])[0] if recipe.get("tags") else "",
                        "summary": recipe.get("description", ""),
                        "similarity_score": 0.5,  # Default score for fallback
                        "confidence": 0.5
                    }
                    all_recipes.append(recipe_data)
                    seen_recipe_ids.add(recipe_id)
        
        logger.info(f"Fallback search found {len(all_recipes)} unique recipes")
        return all_recipes[:50]  # Limit results

    def _create_conversation_context(self, user_prompt: str, rag_response: Dict[str, Any], user_preferences: Dict[str, Any], meal_plan_history: List[int] = None) -> Dict[str, Any]:
        """Create structured conversation context for saving with meal plan"""
        from datetime import datetime
        
        # Create conversation messages
        messages = [
            {
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant", 
                "content": rag_response.get("explanation", "I've created a personalized meal plan for you."),
                "timestamp": datetime.now().isoformat(),
                "meal_plan_generated": True
            }
        ]
        
        # Create analysis context from RAG response
        analysis_context = {
            "ai_enhanced": rag_response.get("ai_enhanced", False),
            "recipes_found": rag_response.get("recipes_found", 0),
            "avg_recipe_similarity": rag_response.get("avg_recipe_similarity"),
            "recipe_collections": rag_response.get("recipe_collections", []),
            "fallback_used": rag_response.get("fallback_used", False)
        }
        
        return {
            "messages": messages,
            "user_preferences": user_preferences,
            "meal_plan_history": meal_plan_history or [],  # Previous meal plan IDs
            "analysis_context": analysis_context
        }

    def _generate_conversation_title(self, user_prompt: str) -> str:
        """Generate a descriptive title from user prompt"""
        # Simple title generation - could be enhanced with AI in the future
        prompt_lower = user_prompt.lower()
        
        # Extract key dietary terms
        dietary_terms = []
        if "vegetarian" in prompt_lower:
            dietary_terms.append("Vegetarian")
        if "vegan" in prompt_lower:
            dietary_terms.append("Vegan")
        if "healthy" in prompt_lower:
            dietary_terms.append("Healthy")
        if "protein" in prompt_lower:
            dietary_terms.append("High Protein")
        if "low carb" in prompt_lower:
            dietary_terms.append("Low Carb")
        
        # Extract time frame
        days = 7  # default
        if "3 day" in prompt_lower:
            days = 3
        elif "5 day" in prompt_lower:
            days = 5
        elif "week" in prompt_lower or "7 day" in prompt_lower:
            days = 7
        elif "14 day" in prompt_lower or "2 week" in prompt_lower:
            days = 14
            
        # Build title
        title_parts = []
        if dietary_terms:
            title_parts.extend(dietary_terms)
        title_parts.append(f"{days}-Day Meal Plan")
        
        return " ".join(title_parts)

    async def continue_meal_plan_conversation(self, db: Session, meal_plan_id: int, new_message: str) -> Dict[str, Any]:
        """Continue an existing meal plan conversation with a new message"""
        try:
            # Get the existing meal plan and conversation
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                raise ValueError(f"Meal plan {meal_plan_id} not found")
            
            # Load existing conversation context
            conversation_context = {}
            if db_meal_plan.conversation_data:
                conversation_context = json.loads(db_meal_plan.conversation_data)
            
            # Add new user message to conversation
            from datetime import datetime
            new_user_message = {
                "role": "user",
                "content": new_message,
                "timestamp": datetime.now().isoformat()
            }
            
            if "messages" not in conversation_context:
                conversation_context["messages"] = []
            conversation_context["messages"].append(new_user_message)
            
            # Get user preferences
            user_preferences = await self._get_user_preferences(db, db_meal_plan.user_id)
            
            # Create conversation history for RAG system
            conversation_history = self._format_conversation_for_rag(conversation_context["messages"])
            
            # Get AI recommendations using full conversation context
            retrieved_recipes = await self._search_recipes_with_ai_recommendations(
                user_prompt=new_message,
                user_preferences=user_preferences,
                max_results=50
            )
            
            # Generate new meal plan using conversation context
            meal_plan = self.gemini_service.generate_rag_meal_plan(new_message, retrieved_recipes)
            
            # Add assistant response to conversation
            assistant_message = {
                "role": "assistant",
                "content": meal_plan.get("explanation", "I've updated your meal plan based on your feedback."),
                "timestamp": datetime.now().isoformat(),
                "meal_plan_updated": True
            }
            conversation_context["messages"].append(assistant_message)
            
            # Update meal plan with new conversation and plan data
            updated_meal_plan = self.meal_plan_repository.create_meal_plan(
                db=db,
                user_id=db_meal_plan.user_id,
                plan_name=f"Updated {db_meal_plan.plan_name}",
                days=db_meal_plan.days,
                meals_per_day=db_meal_plan.meals_per_day,
                plan_data=json.dumps(meal_plan.get("meal_plan", [])),
                plan_explanation=meal_plan.get("explanation", "Updated meal plan"),
                conversation_data=json.dumps(conversation_context),
                conversation_title=db_meal_plan.conversation_title,
                original_prompt=db_meal_plan.original_prompt
            )
            
            # Add recipes to the new meal plan
            meal_plan_data = meal_plan.get("meal_plan", [])
            for day_plan in meal_plan_data:
                day = day_plan.get("day", 1)
                for meal in day_plan.get("meals", []):
                    recipe_id = meal.get("recipe_id")
                    if recipe_id:
                        self.meal_plan_repository.add_recipe_to_meal_plan(
                            db=db,
                            meal_plan_id=updated_meal_plan.id,
                            recipe_id=recipe_id,
                            day=day,
                            meal_type=meal.get("meal_type", "meal")
                        )
            
            # Return updated meal plan
            return {
                "id": updated_meal_plan.id,
                "days": updated_meal_plan.days,
                "plan_name": updated_meal_plan.plan_name,
                "plan_explanation": updated_meal_plan.plan_explanation,
                "created_at": updated_meal_plan.created_at.isoformat(),
                "user_id": updated_meal_plan.user_id,
                "meals_per_day": updated_meal_plan.meals_per_day,
                "recipes": self._convert_to_recipes_format(meal_plan_data),
                "meal_plan": meal_plan,
                "conversation_id": f"continued-{updated_meal_plan.id}",
                "status": "updated",
                "conversation_data": conversation_context
            }
            
        except Exception as e:
            logger.error(f"Error continuing meal plan conversation: {e}")
            raise

    def _format_conversation_for_rag(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation messages for RAG system"""
        formatted_messages = []
        for msg in messages[-10:]:  # Use last 10 messages for context
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        return formatted_messages

    async def _search_recipes_with_multiple_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Legacy method - now redirects to AI-powered search if available"""
        # Create a combined prompt from the queries
        user_prompt = " ".join(queries)
        return await self._search_recipes_with_ai_recommendations(user_prompt)

    async def edit_meal_plan_with_rag(self, db: Session, meal_plan_id: int, current_meal_plan: Dict[str, Any], user_feedback: str) -> Dict[str, Any]:
        """
        Edit an existing meal plan using RAG workflow and user feedback
        
        Args:
            db: Database session
            meal_plan_id: ID of the meal plan to edit
            current_meal_plan: Current meal plan data
            user_feedback: User's description of desired changes
            
        Returns:
            The updated meal plan
        """
        try:
            logger.info(f"Starting RAG-based edit for meal plan {meal_plan_id}")
            
            # Step 1: Generate modification queries based on user feedback
            modification_queries = self.gemini_service.generate_modification_queries(current_meal_plan, user_feedback)
            logger.info(f"Generated modification queries: {modification_queries}")
            
            # Step 2: Search for new recipes using modification queries
            new_recipes = await self._search_recipes_with_multiple_queries(modification_queries)
            logger.info(f"Found {len(new_recipes)} new recipes for modification")
            
            # Step 3: Generate the modified meal plan using Gemini
            modified_meal_plan_data = self.gemini_service.modify_meal_plan(current_meal_plan, user_feedback, new_recipes)
            
            # Step 4: Update the meal plan in the database
            # First, clear existing recipes for this meal plan
            self.meal_plan_repository.clear_meal_plan_recipes(db, meal_plan_id)
            
            # Update meal plan metadata if needed
            plan_name = current_meal_plan.get("plan_name", "Modified Meal Plan")
            if "modified" not in plan_name.lower():
                plan_name = f"Modified {plan_name}"
            
            # Update the meal plan record
            updated_meal_plan = self.meal_plan_repository.update_meal_plan(
                db=db,
                meal_plan_id=meal_plan_id,
                plan_name=plan_name,
                plan_data=json.dumps(modified_meal_plan_data.get("meal_plan", [])),
                plan_explanation=modified_meal_plan_data.get("explanation", "Modified meal plan based on your feedback.")
            )
            
            # Step 5: Add new recipes to the meal plan
            meal_plan_data = modified_meal_plan_data.get("meal_plan", [])
            for day_plan in meal_plan_data:
                day = day_plan.get("day", 1)
                for meal in day_plan.get("meals", []):
                    recipe_id = meal.get("recipe_id")
                    if recipe_id:
                        self.meal_plan_repository.add_recipe_to_meal_plan(
                            db=db,
                            meal_plan_id=meal_plan_id,
                            recipe_id=recipe_id,
                            day=day,
                            meal_type=meal.get("meal_type", "meal")
                        )
            
            # Step 6: Return the updated meal plan
            return await self.get_meal_plan(db, meal_plan_id)
            
        except Exception as e:
            logger.error(f"Error in edit_meal_plan_with_rag: {e}")
            raise
    
    async def replace_recipe(self, db: Session, meal_plan_id: int, old_recipe_id: int, new_recipe_id: int, day: int, meal_type: str) -> bool:
        """
        Replace a recipe in a meal plan with a new recipe
        
        Args:
            db: Database session
            meal_plan_id: Meal plan ID
            old_recipe_id: ID of the recipe to replace
            new_recipe_id: ID of the new recipe
            day: Day of the meal
            meal_type: Type of meal (breakfast, lunch, dinner)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the meal plan exists
            db_meal_plan = self.meal_plan_repository.get_meal_plan(db, meal_plan_id)
            if not db_meal_plan:
                logger.error(f"Meal plan {meal_plan_id} not found")
                return False
            
            # Get the specific meal plan recipe to replace
            db_recipes = self.meal_plan_repository.get_meal_plan_recipes(db, meal_plan_id)
            target_recipe = None
            
            for recipe in db_recipes:
                if recipe.recipe_id == old_recipe_id and recipe.day == day and recipe.meal_type == meal_type:
                    target_recipe = recipe
                    break
            
            if not target_recipe:
                logger.error(f"Recipe {old_recipe_id} not found in meal plan {meal_plan_id} for day {day}, meal {meal_type}")
                return False
            
            # Delete the old recipe from the meal plan
            from sqlalchemy import delete
            from app.models.models import MealPlanRecipe
            
            db.execute(
                delete(MealPlanRecipe).where(
                    MealPlanRecipe.id == target_recipe.id
                )
            )
            
            # Add the new recipe to the meal plan
            self.meal_plan_repository.add_recipe_to_meal_plan(db, meal_plan_id, new_recipe_id, day, meal_type)
            
            # Update the plan_data field with the new recipe structure
            # Get all recipes for the meal plan after the update
            updated_recipes = self.meal_plan_repository.get_meal_plan_recipes(db, meal_plan_id)
            
            # Get recipe details for the updated meal plan
            recipes_details = []
            for db_recipe in updated_recipes:
                recipe_detail = await self.microservice_client.get_recipe(db_recipe.recipe_id)
                if recipe_detail:
                    recipes_details.append({
                        **recipe_detail,
                        "day": db_recipe.day,
                        "meal_type": db_recipe.meal_type
                    })
            
            # Update the plan_data field
            updated_plan_data = json.dumps(recipes_details)
            self.meal_plan_repository.update_meal_plan_data(db, meal_plan_id, updated_plan_data)
            
            # Clear grocery list cache since meal plan changed
            await self._clear_grocery_list_cache(db, meal_plan_id)
            
            logger.info(f"Successfully replaced recipe {old_recipe_id} with {new_recipe_id} in meal plan {meal_plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error replacing recipe in meal plan: {e}")
            return False