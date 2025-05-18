from sqlalchemy.orm import Session
import json
from app.models.models import MealPlan, MealPlanRecipe, UserPreference
from datetime import datetime

class MealPlanRepository:
    def create_meal_plan(self, db: Session, user_id: int, plan_name: str, days: int, meals_per_day: int, 
                          plan_data: dict, plan_explanation: str):
        """Create a new meal plan in the database"""
        db_meal_plan = MealPlan(
            user_id=user_id,
            plan_name=plan_name,
            days=days,
            meals_per_day=meals_per_day,
            plan_data=json.dumps(plan_data),
            plan_explanation=plan_explanation
        )
        db.add(db_meal_plan)
        db.commit()
        db.refresh(db_meal_plan)
        return db_meal_plan

    def add_recipe_to_meal_plan(self, db: Session, meal_plan_id: int, recipe_id: int, day: int, meal_type: str):
        """Add a recipe to a meal plan"""
        db_recipe = MealPlanRecipe(
            meal_plan_id=meal_plan_id,
            recipe_id=recipe_id,
            day=day,
            meal_type=meal_type
        )
        db.add(db_recipe)
        db.commit()
        db.refresh(db_recipe)
        return db_recipe

    def get_meal_plan(self, db: Session, meal_plan_id: int):
        """Get a meal plan by ID"""
        return db.query(MealPlan).filter(MealPlan.id == meal_plan_id).first()

    def get_meal_plan_recipes(self, db: Session, meal_plan_id: int):
        """Get all recipes for a meal plan"""
        return db.query(MealPlanRecipe).filter(MealPlanRecipe.meal_plan_id == meal_plan_id).all()

    def get_user_meal_plans(self, db: Session, user_id: int, skip: int = 0, limit: int = 100):
        """Get all meal plans for a user"""
        return db.query(MealPlan).filter(MealPlan.user_id == user_id).offset(skip).limit(limit).all()

    def delete_meal_plan(self, db: Session, meal_plan_id: int):
        """Delete a meal plan"""
        # First delete associated recipes
        db.query(MealPlanRecipe).filter(MealPlanRecipe.meal_plan_id == meal_plan_id).delete()
        # Then delete the meal plan
        db.query(MealPlan).filter(MealPlan.id == meal_plan_id).delete()
        db.commit()

    def cache_user_preferences(self, db: Session, user_id: int, preferences: dict):
        """Cache user preferences"""
        # Check if preference exists
        db_pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        
        if db_pref:
            # Update existing preference
            db_pref.dietary_restrictions = json.dumps(preferences.get("dietary_restrictions", []))
            db_pref.allergies = json.dumps(preferences.get("allergies", []))
            db_pref.cuisine_preferences = json.dumps(preferences.get("cuisine_preferences", []))
            db_pref.disliked_ingredients = json.dumps(preferences.get("disliked_ingredients", []))
            db_pref.updated_at = datetime.utcnow()
        else:
            # Create new preference
            db_pref = UserPreference(
                user_id=user_id,
                dietary_restrictions=json.dumps(preferences.get("dietary_restrictions", [])),
                allergies=json.dumps(preferences.get("allergies", [])),
                cuisine_preferences=json.dumps(preferences.get("cuisine_preferences", [])),
                disliked_ingredients=json.dumps(preferences.get("disliked_ingredients", []))
            )
            db.add(db_pref)
            
        db.commit()
        db.refresh(db_pref)
        return db_pref

    def get_cached_user_preferences(self, db: Session, user_id: int):
        """Get cached user preferences"""
        db_pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if not db_pref:
            return None
            
        return {
            "dietary_restrictions": json.loads(db_pref.dietary_restrictions) if db_pref.dietary_restrictions else [],
            "allergies": json.loads(db_pref.allergies) if db_pref.allergies else [],
            "cuisine_preferences": json.loads(db_pref.cuisine_preferences) if db_pref.cuisine_preferences else [],
            "disliked_ingredients": json.loads(db_pref.disliked_ingredients) if db_pref.disliked_ingredients else []
        }