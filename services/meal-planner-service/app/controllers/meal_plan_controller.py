from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import schemas
from app.services.meal_plan_service import MealPlanService

router = APIRouter()
meal_plan_service = MealPlanService()

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
        meal_plans = await meal_plan_service.get_user_meal_plans(db, user_id)
        return meal_plans
    except Exception as e:
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