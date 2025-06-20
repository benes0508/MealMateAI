from fastapi import APIRouter, Depends, HTTPException, Query, Body, Header
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app.models import schemas
from app.services.meal_plan_service import MealPlanService

# Set up logging
logger = logging.getLogger("meal_plan_controller")
logger.setLevel(logging.DEBUG)

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
        
        # Return 404 if none found
        if not meal_plans:
            logger.info(f"No meal plans found for user {user_id}")
            raise HTTPException(status_code=404, detail="No meal plan found for user")
            
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
    db: Session = Depends(get_db)
):
    """
    Generate a grocery list for a meal plan
    """
    try:
        grocery_list = await meal_plan_service.generate_grocery_list(db, meal_plan_id)
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
            to_meal_type=move_request.to_meal_type
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