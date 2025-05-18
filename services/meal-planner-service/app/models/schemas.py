from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class MealPlanRequest(BaseModel):
    user_id: int
    days: int = Field(default=7, description="Number of days for the meal plan")
    meals_per_day: int = Field(default=3, description="Number of meals per day")
    include_snacks: bool = Field(default=False, description="Whether to include snacks in the meal plan")
    additional_preferences: Optional[str] = Field(default=None, description="Free-text additional preferences")

class RecipeBase(BaseModel):
    id: int
    name: str
    ingredients: List[Dict[str, Any]]
    instructions: List[str]
    cuisine_type: Optional[str] = None
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    calories: Optional[int] = None
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    
    class Config:
        orm_mode = True

class MealPlanRecipeResponse(BaseModel):
    recipe_id: int
    day: int
    meal_type: str
    
    class Config:
        orm_mode = True

class MealPlanResponse(BaseModel):
    id: int
    user_id: int
    plan_name: str
    created_at: datetime
    days: int
    meals_per_day: int
    plan_explanation: str
    recipes: List[MealPlanRecipeResponse]
    
    class Config:
        orm_mode = True

class UserPreference(BaseModel):
    dietary_restrictions: Optional[List[str]] = []
    allergies: Optional[List[str]] = []
    cuisine_preferences: Optional[List[str]] = []
    disliked_ingredients: Optional[List[str]] = []
    
    class Config:
        orm_mode = True

class GroceryListItem(BaseModel):
    name: str
    amount: str
    category: Optional[str] = None

class GroceryList(BaseModel):
    items: List[GroceryListItem]