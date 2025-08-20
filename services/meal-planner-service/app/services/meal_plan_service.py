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
            
            # Extract plan name from explanation or create default
            plan_name = "AI Generated Meal Plan"
            if rag_response.get("explanation"):
                if "vegetarian" in input_text.lower():
                    plan_name = f"{days}-Day Vegetarian Meal Plan"
                elif "vegan" in input_text.lower():
                    plan_name = f"{days}-Day Vegan Meal Plan"
                else:
                    plan_name = f"{days}-Day Personalized Meal Plan"
            
            # Save the meal plan to the database
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

    async def create_rag_meal_plan(self, db: Session, user_id: int, user_prompt: str) -> Dict[str, Any]:
        """Complete RAG workflow: Generate meal plan from user prompt"""
        try:
            # Step 2: Generate search queries
            queries = self.gemini_service.generate_search_queries(user_prompt)
            
            # Step 3: Search for recipes using multiple queries
            retrieved_recipes = await self._search_recipes_with_multiple_queries(queries)
            
            if not retrieved_recipes:
                return {
                    "meal_plan": [],
                    "explanation": "No suitable recipes found for your request. Please try a different query.",
                    "queries_used": queries,
                    "recipes_found": 0
                }
            
            # Step 3: Generate meal plan using retrieved recipes
            meal_plan = self.gemini_service.generate_rag_meal_plan(user_prompt, retrieved_recipes)
            
            # Add metadata
            meal_plan["queries_used"] = queries
            meal_plan["recipes_found"] = len(retrieved_recipes)
            meal_plan["user_prompt"] = user_prompt
            
            return meal_plan
            
        except Exception as e:
            logger.error(f"Error in RAG meal plan creation: {e}")
            return {
                "meal_plan": [],
                "explanation": f"An error occurred while generating your meal plan: {str(e)}",
                "queries_used": [],
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

    async def _search_recipes_with_multiple_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """Search recipes using multiple queries and combine results"""
        all_recipes = []
        seen_recipe_ids = set()
        
        for query in queries:
            logger.info(f"Searching recipes with query: {query}")
            recipes = await self.microservice_client.search_recipes(query, limit=20)
            
            # If no recipes found with this query, try fallback searches
            if not recipes and query in ["vegetarian", "vegan"]:
                logger.info(f"No recipes found for '{query}', trying vegetarian-friendly alternatives")
                fallback_queries = ["salad", "avocado", "toast"]
                for fallback_query in fallback_queries:
                    fallback_recipes = await self.microservice_client.search_recipes(fallback_query, limit=10)
                    recipes.extend(fallback_recipes)
            elif not recipes and query in ["protein"]:
                logger.info(f"No recipes found for '{query}', trying protein-rich alternatives")
                fallback_queries = ["chicken", "beef", "eggs"]
                for fallback_query in fallback_queries:
                    fallback_recipes = await self.microservice_client.search_recipes(fallback_query, limit=10)
                    recipes.extend(fallback_recipes)
            
            # Add unique recipes
            for recipe in recipes:
                recipe_id = recipe.get("id") or recipe.get("recipe_id")
                if recipe_id and recipe_id not in seen_recipe_ids:
                    all_recipes.append(recipe)
                    seen_recipe_ids.add(recipe_id)
        
        # If still no recipes found, try a broad search
        if not all_recipes:
            logger.warning("No recipes found with any queries, trying broad search")
            broad_queries = ["chicken", "salad", "sandwich"]
            for broad_query in broad_queries:
                broad_recipes = await self.microservice_client.search_recipes(broad_query, limit=10)
                for recipe in broad_recipes:
                    recipe_id = recipe.get("id") or recipe.get("recipe_id")
                    if recipe_id and recipe_id not in seen_recipe_ids:
                        all_recipes.append(recipe)
                        seen_recipe_ids.add(recipe_id)
        
        # Limit to 100 recipes total
        if len(all_recipes) > 100:
            all_recipes = all_recipes[:100]
        
        logger.info(f"Found {len(all_recipes)} unique recipes from {len(queries)} queries")
        return all_recipes

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