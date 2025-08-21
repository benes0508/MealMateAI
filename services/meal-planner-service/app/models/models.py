from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, ARRAY, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    plan_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    days = Column(Integer)
    meals_per_day = Column(Integer)
    
    # JSON string with recipe_ids for each day and meal
    plan_data = Column(Text)
    
    # JSON string with LLM response containing the meal plan explanation
    plan_explanation = Column(Text)
    
    # Chat conversation integration fields (optional - for future enhancement)
    # These columns may not exist on all deployments, so they're handled gracefully
    conversation_data = Column(Text, nullable=True)  # JSON string of full chat history
    conversation_title = Column(String(500), nullable=True)  # Auto-generated chat title
    original_prompt = Column(Text, nullable=True)  # User's initial request for future RAG analysis
    
    # Relationship with MealPlanRecipes
    recipes = relationship("MealPlanRecipe", back_populates="meal_plan")

class MealPlanRecipe(Base):
    __tablename__ = "meal_plan_recipes"

    id = Column(Integer, primary_key=True, index=True)
    meal_plan_id = Column(Integer, ForeignKey("meal_plans.id"))
    recipe_id = Column(Integer)  # ID from recipe-service
    day = Column(Integer)  # Day number in the meal plan
    meal_type = Column(String(50))  # breakfast, lunch, dinner, snack
    
    # Relationship with MealPlan
    meal_plan = relationship("MealPlan", back_populates="recipes")

class UserPreference(Base):
    """
    Cache of user preferences fetched from user-service
    """
    __tablename__ = "user_preferences_cache"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    dietary_restrictions = Column(Text)  # JSON string of dietary restrictions
    allergies = Column(Text)  # JSON string of allergies
    cuisine_preferences = Column(Text)  # JSON string of cuisine preferences
    disliked_ingredients = Column(Text)  # JSON string of disliked ingredients
    updated_at = Column(DateTime, default=datetime.utcnow)