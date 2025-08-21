from fastapi import APIRouter, Depends, HTTPException, Query, Body, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import json
from datetime import datetime

from app.database import get_db
from app.models import schemas
from app.services.meal_plan_service import MealPlanService

# Set up logging
logger = logging.getLogger("meal_plan_controller")
logger.setLevel(logging.DEBUG)

# In-memory storage for RAG conversations (in production, use Redis or database)
rag_conversations = {}

router = APIRouter()
meal_plan_service = MealPlanService()

@router.get("/current", response_model=schemas.MealPlanResponse)
async def get_current_meal_plan(
    x_user_id: Optional[int] = Header(None, alias="X-User-ID"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Get the current active meal plan for the authenticated user
    """
    try:
        # Extract user ID from header
        user_id = x_user_id
        
        # Log request details
        logger.debug(f"Get current meal plan request received: user_id={user_id}")
        
        if not user_id:
            # If no user ID in header, return an error
            logger.error("Missing user ID in current meal plan request")
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get all meal plans for the user
        meal_plans = await meal_plan_service.get_user_meal_plans(db, user_id)
        
        # Return empty meal plan structure with 200 OK if none found
        if not meal_plans:
            logger.info(f"No meal plans found for user {user_id}")
            # Return an empty meal plan structure instead of 404
            return {
                "id": None,
                "user_id": user_id,
                "plan_name": "No Plan",
                "created_at": datetime.now().isoformat(),
                "days": 0,
                "meals_per_day": 0,
                "plan_explanation": "You don't have any meal plans yet. Generate your first plan to get started!",
                "recipes": []
            }
            
        # Sort meal plans by ID (assuming higher ID = more recent)
        # and take the first one (most recent)
        logger.debug(f"Found {len(meal_plans)} meal plans for user {user_id}")
        sorted_plans = sorted(meal_plans, key=lambda x: x["id"], reverse=True)
        most_recent_plan_id = sorted_plans[0]["id"]
        logger.debug(f"Most recent plan ID: {most_recent_plan_id}")
        
        # Get the full details of the most recent meal plan
        most_recent_plan = await meal_plan_service.get_meal_plan(db, most_recent_plan_id)
        return most_recent_plan
        
    except ValueError as e:
        logger.error(f"Value error in get_current_meal_plan: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"Error in get_current_meal_plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the meal plan: {str(e)}")

@router.post("/", response_model=schemas.MealPlanResponse)
async def create_meal_plan(
    meal_plan_request: schemas.MealPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new meal plan for a user based on their preferences
    """
    try:
        meal_plan = await meal_plan_service.create_meal_plan(
            db=db,
            user_id=meal_plan_request.user_id,
            days=meal_plan_request.days,
            meals_per_day=meal_plan_request.meals_per_day,
            include_snacks=meal_plan_request.include_snacks,
            additional_preferences=meal_plan_request.additional_preferences
        )
        return meal_plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the meal plan: {str(e)}")

@router.get("/{meal_plan_id}", response_model=schemas.MealPlanResponse)
async def get_meal_plan(
    meal_plan_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a meal plan by ID
    """
    try:
        meal_plan = await meal_plan_service.get_meal_plan(db, meal_plan_id)
        return meal_plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the meal plan: {str(e)}")

@router.get("/user/{user_id}", response_model=List[schemas.MealPlanResponse])
async def get_user_meal_plans(
    user_id: int,
    skip: int = Query(0, description="Number of items to skip"),
    limit: int = Query(100, description="Maximum number of items to return"),
    db: Session = Depends(get_db)
):
    """
    Get all meal plans for a user
    """
    try:
        # Log request info for debugging
        logger.debug(f"Getting meal plans for user {user_id}")
        
        meal_plans = await meal_plan_service.get_user_meal_plans(db, user_id)
        
        # If no meal plans found, return an empty list (not an error)
        if not meal_plans:
            logger.info(f"No meal plans found for user {user_id}, returning empty list")
        else:
            logger.debug(f"Found {len(meal_plans)} meal plans for user {user_id}")
            
        return meal_plans
    except Exception as e:
        logger.error(f"Error retrieving meal plans for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving meal plans: {str(e)}")

@router.get("/{meal_plan_id}/grocery-list", response_model=schemas.GroceryList)
async def get_grocery_list(
    meal_plan_id: int,
    force_regenerate: bool = False,
    db: Session = Depends(get_db)
):
    """
    Generate or retrieve cached grocery list for a meal plan
    
    Args:
        meal_plan_id: ID of the meal plan
        force_regenerate: If True, regenerate grocery list even if cached version exists
    """
    try:
        grocery_list = await meal_plan_service.generate_grocery_list(db, meal_plan_id, force_regenerate)
        return grocery_list
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while generating the grocery list: {str(e)}")

@router.delete("/{meal_plan_id}")
async def delete_meal_plan(
    meal_plan_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a meal plan
    """
    try:
        success = await meal_plan_service.delete_meal_plan(db, meal_plan_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Meal plan {meal_plan_id} not found")
        return {"message": f"Meal plan {meal_plan_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while deleting the meal plan: {str(e)}")

@router.post("/text-input", response_model=schemas.MealPlanResponse)
async def process_text_input(
    user_id: int = Query(..., description="User ID"),
    input_text: str = Body(..., embed=True, description="Natural language input text"),
    db: Session = Depends(get_db)
):
    """
    Process natural language text input to create a meal plan using RAG
    
    This endpoint allows users to describe their meal plan needs in natural language.
    The LLM with RAG will process the text to create a personalized meal plan.
    """
    try:
        # Process the input text using the service
        meal_plan = await meal_plan_service.process_text_input(
            db=db,
            user_id=user_id,
            input_text=input_text
        )
        
        return meal_plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while creating the meal plan: {str(e)}")

@router.post("/index-recipes")
async def index_all_recipes(db: Session = Depends(get_db)):
    """
    Fetch all recipes and index them in the vector database
    """
    try:
        from app.services.embeddings_service import EmbeddingsService
        from app.services.microservice_client import MicroserviceClient
        
        # Create services
        embeddings_service = EmbeddingsService()
        microservice_client = MicroserviceClient()
        
        # Fetch recipes
        recipes = await microservice_client.get_recipes()
        if not recipes:
            return {"message": "No recipes found to index"}
        
        # Index recipes
        success = await embeddings_service.batch_store_recipe_embeddings(db, recipes)
        
        if success:
            return {"message": f"Successfully indexed {len(recipes)} recipes"}
        else:
            raise HTTPException(status_code=500, detail="Failed to index recipes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while indexing recipes: {str(e)}")

@router.post("/{meal_plan_id}/move-meal", response_model=schemas.MealPlanModuleResponse)
async def move_meal(
    meal_plan_id: int,
    move_request: schemas.MoveMealRequest,
    db: Session = Depends(get_db)
):
    """
    Move a meal to a different day or meal type within a meal plan
    """
    try:
        logger.debug(f"Moving meal in plan {meal_plan_id}: recipe_id={move_request.recipe_id}, to_day={move_request.to_day}, to_meal_type={move_request.to_meal_type}")
        
        success = await meal_plan_service.move_meal(
            db=db,
            meal_plan_id=meal_plan_id,
            recipe_id=move_request.recipe_id,
            to_day=move_request.to_day,
            to_meal_type=move_request.to_meal_type,
            from_day=move_request.from_day,
            from_meal_type=move_request.from_meal_type
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to move meal. Meal plan or recipe not found.")
        
        return {"success": True, "message": "Meal moved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error moving meal: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while moving the meal: {str(e)}")

@router.post("/{meal_plan_id}/swap-days", response_model=schemas.MealPlanModuleResponse)
async def swap_days(
    meal_plan_id: int,
    swap_request: schemas.SwapDaysRequest,
    db: Session = Depends(get_db)
):
    """
    Swap two days in a meal plan
    """
    try:
        logger.debug(f"Swapping days in plan {meal_plan_id}: day1={swap_request.day1}, day2={swap_request.day2}")
        
        success = await meal_plan_service.swap_days(
            db=db,
            meal_plan_id=meal_plan_id,
            day1=swap_request.day1,
            day2=swap_request.day2
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to swap days. Meal plan or days not found.")
        
        return {"success": True, "message": "Days swapped successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error swapping days: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while swapping days: {str(e)}")

@router.post("/{meal_plan_id}/reorder-days", response_model=schemas.MealPlanModuleResponse)
async def reorder_days(
    meal_plan_id: int,
    reorder_request: schemas.ReorderDaysRequest,
    db: Session = Depends(get_db)
):
    """
    Reorder days in a meal plan
    """
    try:
        logger.debug(f"Reordering days in plan {meal_plan_id}: day_order={reorder_request.day_order}")
        
        success = await meal_plan_service.reorder_days(
            db=db, 
            meal_plan_id=meal_plan_id,
            day_order=reorder_request.day_order
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to reorder days. Meal plan not found or invalid day order.")
        
        return {"success": True, "message": "Days reordered successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error reordering days: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while reordering days: {str(e)}")

@router.post("/rag/generate", response_model=schemas.RAGMealPlanResponse)
async def generate_rag_meal_plan(
    request: schemas.RAGMealPlanRequest,
    db: Session = Depends(get_db)
):
    """
    Generate initial meal plan using RAG workflow 
    """
    try:
        meal_plan_data = await meal_plan_service.create_rag_meal_plan(
            db=db,
            user_id=request.user_id,
            user_prompt=request.user_prompt
        )
        
        # Generate conversation ID for this RAG session
        import uuid
        conversation_id = str(uuid.uuid4())
        
        # Extract meal plan from the returned data
        meal_plan = meal_plan_data.get("meal_plan", [])
        
        # Handle the case where meal_plan might be a list or dict
        if isinstance(meal_plan, list):
            # If it's a list, it's likely a list of recipes
            meal_plan_dict = {
                "recipes": meal_plan,
                "days": 7,  # default
                "meals_per_day": 3,  # default
                "plan_name": "Custom Meal Plan"
            }
        else:
            # If it's a dict, use it as is
            meal_plan_dict = meal_plan
        
        # Build proper response format that matches the schema
        response = {
            "meal_plan": meal_plan_data,
            "conversation_id": conversation_id,
            "status": "initial",
            "id": 0,  # Temporary ID since this is a preview
            "days": meal_plan_dict.get("days", 7),
            "plan_name": meal_plan_dict.get("plan_name", "Custom Meal Plan"),
            "plan_explanation": meal_plan_data.get("explanation", "Your personalized meal plan"),
            "created_at": datetime.now().isoformat(),
            "user_id": request.user_id,
            "meals_per_day": meal_plan_dict.get("meals_per_day", 3),
            "recipes": meal_plan_dict.get("recipes", [])
        }
        
        # Store the conversation for finalization
        rag_conversations[conversation_id] = {
            "user_id": request.user_id,
            "user_prompt": request.user_prompt,
            "meal_plan_data": meal_plan_data,
            "response": response,
            "created_at": datetime.now()
        }
        
        return response
    except Exception as e:
        logger.exception(f"Error generating RAG meal plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while generating the meal plan: {str(e)}")

@router.post("/rag/modify", response_model=schemas.RAGMealPlanResponse)  
async def modify_rag_meal_plan(
    request: schemas.RAGFeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Modify meal plan based on user feedback (Step 4)
    """
    try:
        # For now, we'll store the current meal plan in session/cache
        # In a production system, you'd want to store this in a database or cache
        # Here we'll use a simple in-memory approach for the demo
        
        # This is a simplified approach - in production you'd retrieve the current meal plan
        # from the conversation_id stored in database or cache
        logger.warning("RAG conversation persistence not implemented - using latest meal plan")
        
        # Get the user's most recent meal plan as a starting point
        user_meal_plans = await meal_plan_service.get_user_meal_plans(db, request.user_id)
        if not user_meal_plans:
            raise HTTPException(status_code=404, detail="No existing meal plan found to modify")
        
        # Use the most recent meal plan
        current_meal_plan = user_meal_plans[0] if user_meal_plans else {}
        
        modified_plan = await meal_plan_service.modify_rag_meal_plan(
            current_meal_plan=current_meal_plan,
            user_feedback=request.user_feedback
        )
        
        return {
            "meal_plan": modified_plan,
            "conversation_id": request.conversation_id,
            "status": "modified"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error modifying RAG meal plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while modifying the meal plan: {str(e)}")

@router.post("/rag/finalize", response_model=schemas.MealPlanResponse)
async def finalize_rag_meal_plan(
    request: schemas.RAGFinalizeRequest,
    db: Session = Depends(get_db)
):
    """
    Finalize RAG meal plan and save to database (Step 5)
    """
    try:
        logger.info(f"=== START FINALIZE RAG MEAL PLAN ===")
        logger.info(f"Request data: conversation_id={request.conversation_id}, user_id={request.user_id}")
        
        # Retrieve the conversation data
        if request.conversation_id not in rag_conversations:
            logger.error(f"Conversation {request.conversation_id} not found. Available conversations: {list(rag_conversations.keys())}")
            raise HTTPException(status_code=404, detail="Conversation not found or expired")
        
        conversation_data = rag_conversations[request.conversation_id]
        logger.info(f"Found conversation data with keys: {list(conversation_data.keys())}")
        
        # Verify user matches
        if conversation_data["user_id"] != request.user_id:
            logger.error(f"User mismatch: expected {conversation_data['user_id']}, got {request.user_id}")
            raise HTTPException(status_code=403, detail="User mismatch")
        
        # Get the pre-generated meal plan data
        meal_plan_data = conversation_data.get("meal_plan_data", {})
        response_data = conversation_data.get("response", {})
        
        logger.info(f"Meal plan data keys: {list(meal_plan_data.keys()) if meal_plan_data else 'None'}")
        logger.info(f"Response data keys: {list(response_data.keys()) if response_data else 'None'}")
        
        # Extract key information
        days = response_data.get("days", 7)
        meals_per_day = response_data.get("meals_per_day", 3)
        plan_name = response_data.get("plan_name", "AI Generated Meal Plan")
        plan_explanation = response_data.get("plan_explanation", meal_plan_data.get("explanation", "Your personalized meal plan"))
        
        logger.info(f"Creating meal plan: name='{plan_name}', days={days}, meals_per_day={meals_per_day}")
        logger.info(f"Plan explanation: {plan_explanation[:100]}..." if plan_explanation else "No explanation")
        
        # Get the meal plan array
        meal_plan_array = meal_plan_data.get("meal_plan", [])
        logger.info(f"Meal plan array type: {type(meal_plan_array)}, length: {len(meal_plan_array) if isinstance(meal_plan_array, list) else 'N/A'}")
        
        # Create the meal plan in the database (without optional fields that may not exist in DB)
        try:
            logger.info(f"Calling create_meal_plan with plan_data type: {type(meal_plan_array)}")
            db_meal_plan = meal_plan_service.meal_plan_repository.create_meal_plan(
                db=db,
                user_id=request.user_id,
                plan_name=plan_name,
                days=days,
                meals_per_day=meals_per_day,
                plan_data=meal_plan_array,  # Pass the array directly, repository will handle JSON conversion
                plan_explanation=plan_explanation
            )
            logger.info(f"Successfully created meal plan with ID: {db_meal_plan.id}")
        except Exception as e:
            logger.error(f"Failed to create meal plan in database: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Add recipes to the meal plan
        logger.info(f"Adding recipes to meal plan. Recipe data structure: {type(meal_plan_array)}")
        recipe_count = 0
        for idx, day_data in enumerate(meal_plan_array):
            logger.info(f"Processing day {idx}: type={type(day_data)}, keys={list(day_data.keys()) if isinstance(day_data, dict) else 'N/A'}")
            if isinstance(day_data, dict) and "meals" in day_data:
                for meal_idx, meal in enumerate(day_data["meals"]):
                    recipe_id = meal.get("recipe_id")
                    day = day_data.get("day", 1)
                    meal_type = meal.get("meal_type", "lunch")
                    logger.info(f"  Adding recipe {meal_idx}: recipe_id={recipe_id}, day={day}, meal_type={meal_type}")
                    try:
                        meal_plan_service.meal_plan_repository.add_recipe_to_meal_plan(
                            db=db,
                            meal_plan_id=db_meal_plan.id,
                            recipe_id=recipe_id,
                            day=day,
                            meal_type=meal_type
                        )
                        recipe_count += 1
                    except Exception as e:
                        logger.error(f"  Failed to add recipe: {str(e)}")
        
        logger.info(f"Added {recipe_count} recipes to meal plan")
        
        # Get the saved meal plan with all relationships
        logger.info(f"Fetching saved meal plan with ID {db_meal_plan.id}")
        saved_meal_plan = meal_plan_service.meal_plan_repository.get_meal_plan(db, db_meal_plan.id)
        
        if saved_meal_plan:
            logger.info(f"Retrieved saved meal plan: {type(saved_meal_plan)}")
            # Check if it's a model object and needs conversion
            if hasattr(saved_meal_plan, '__dict__'):
                logger.info(f"Converting meal plan model to dict")
                saved_meal_plan_dict = {
                    "id": saved_meal_plan.id,
                    "user_id": saved_meal_plan.user_id,
                    "plan_name": saved_meal_plan.plan_name,
                    "created_at": saved_meal_plan.created_at.isoformat() if saved_meal_plan.created_at else None,
                    "days": saved_meal_plan.days,
                    "meals_per_day": saved_meal_plan.meals_per_day,
                    "plan_explanation": saved_meal_plan.plan_explanation,
                    "recipes": []
                }
                logger.info(f"Converted meal plan to dict with ID {saved_meal_plan_dict['id']}")
            else:
                saved_meal_plan_dict = saved_meal_plan
        else:
            logger.error(f"Failed to retrieve saved meal plan with ID {db_meal_plan.id}")
            saved_meal_plan_dict = {
                "id": db_meal_plan.id,
                "user_id": db_meal_plan.user_id,
                "plan_name": db_meal_plan.plan_name,
                "created_at": db_meal_plan.created_at.isoformat() if db_meal_plan.created_at else None,
                "days": db_meal_plan.days,
                "meals_per_day": db_meal_plan.meals_per_day,
                "plan_explanation": db_meal_plan.plan_explanation,
                "recipes": []
            }
        
        # Clean up the conversation
        del rag_conversations[request.conversation_id]
        logger.info(f"Cleaned up conversation {request.conversation_id}")
        
        logger.info(f"=== SUCCESSFULLY FINALIZED MEAL PLAN {saved_meal_plan_dict['id']} ===")
        return saved_meal_plan_dict
        
    except HTTPException:
        logger.error(f"HTTP Exception in finalize_rag_meal_plan")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error finalizing RAG meal plan: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"An error occurred while finalizing the meal plan: {str(e)}")

@router.post("/{meal_plan_id}/continue-chat", response_model=schemas.MealPlanResponse)
async def continue_meal_plan_chat(
    meal_plan_id: int,
    request: schemas.ContinueChatRequest,
    db: Session = Depends(get_db)
):
    """
    Continue an existing meal plan conversation with a new message
    
    This allows users to modify or discuss their existing meal plans in a conversational manner.
    The full conversation history is maintained and used for context in generating updates.
    """
    try:
        logger.info(f"Continuing conversation for meal plan {meal_plan_id}")
        
        updated_meal_plan = await meal_plan_service.continue_meal_plan_conversation(
            db=db,
            meal_plan_id=meal_plan_id,
            new_message=request.new_message
        )
        
        return updated_meal_plan
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception(f"Error continuing meal plan conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while continuing the conversation: {str(e)}")

@router.get("/{meal_plan_id}/conversation")
async def get_meal_plan_conversation(
    meal_plan_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the conversation history for a meal plan
    
    Returns the full chat context that was used to create and modify the meal plan.
    Useful for the frontend to display conversation history or continue conversations.
    """
    try:
        conversation_data = meal_plan_service.meal_plan_repository.get_meal_plan_conversation(
            db=db,
            meal_plan_id=meal_plan_id
        )
        
        if not conversation_data:
            raise HTTPException(status_code=404, detail="Conversation data not found for this meal plan")
        
        return conversation_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving conversation for meal plan {meal_plan_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while retrieving the conversation: {str(e)}")

@router.post("/{meal_plan_id}/replace-recipe", response_model=schemas.MealPlanModuleResponse)
async def replace_recipe(
    meal_plan_id: int,
    replace_request: schemas.ReplaceRecipeRequest,
    db: Session = Depends(get_db)
):
    """
    Replace a recipe in a meal plan with a new recipe
    """
    try:
        logger.debug(f"Replacing recipe in plan {meal_plan_id}: old_recipe_id={replace_request.old_recipe_id}, new_recipe_id={replace_request.new_recipe_id}, day={replace_request.day}, meal_type={replace_request.meal_type}")
        
        success = await meal_plan_service.replace_recipe(
            db=db,
            meal_plan_id=meal_plan_id,
            old_recipe_id=replace_request.old_recipe_id,
            new_recipe_id=replace_request.new_recipe_id,
            day=replace_request.day,
            meal_type=replace_request.meal_type
        )
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to replace recipe. Meal plan or recipe not found.")
        
        return {"success": True, "message": "Recipe replaced successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error replacing recipe: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An error occurred while replacing the recipe: {str(e)}")