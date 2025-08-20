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

    def update_meal_plan_recipe(self, db: Session, recipe_id: int, day: int, meal_type: str):
        """Update a meal plan recipe's day and/or meal type"""
        db_recipe = db.query(MealPlanRecipe).filter(MealPlanRecipe.id == recipe_id).first()
        if db_recipe:
            db_recipe.day = day
            db_recipe.meal_type = meal_type
            db.commit()
            db.refresh(db_recipe)
            return db_recipe
        return None

    def swap_meal_plan_days(self, db: Session, meal_plan_id: int, day1: int, day2: int):
        """Swap two days in a meal plan"""
        # Get all recipes for day1
        day1_recipes = db.query(MealPlanRecipe).filter(
            MealPlanRecipe.meal_plan_id == meal_plan_id,
            MealPlanRecipe.day == day1
        ).all()
        
        # Get all recipes for day2
        day2_recipes = db.query(MealPlanRecipe).filter(
            MealPlanRecipe.meal_plan_id == meal_plan_id,
            MealPlanRecipe.day == day2
        ).all()
        
        # Update day1 recipes to use a temporary day number
        temp_day = 100  # Temporary day number that won't conflict
        for recipe in day1_recipes:
            recipe.day = temp_day
            
        db.commit()
        
        # Update day2 recipes to day1
        for recipe in day2_recipes:
            recipe.day = day1
            
        db.commit()
        
        # Update temp day recipes to day2
        for recipe in day1_recipes:
            recipe.day = day2
            
        db.commit()
        return True

    def move_meal(self, db: Session, meal_plan_id: int, recipe_id: int, to_day: int, to_meal_type: str, from_day: int = None, from_meal_type: str = None):
        """Move a meal to a different day or meal type"""
        # First, try to find the meal record by recipe_id within the meal plan
        # If we have source day and meal type, use them for more precise matching
        query = db.query(MealPlanRecipe).filter(
            MealPlanRecipe.meal_plan_id == meal_plan_id,
            MealPlanRecipe.recipe_id == recipe_id
        )
        
        # If we have source location information, use it to find the exact record
        if from_day is not None and from_meal_type is not None:
            query = query.filter(
                MealPlanRecipe.day == from_day,
                MealPlanRecipe.meal_type == from_meal_type
            )
        
        db_recipe = query.first()
        
        if db_recipe:
            # Check if there's already a meal at the destination
            existing_meal = db.query(MealPlanRecipe).filter(
                MealPlanRecipe.meal_plan_id == meal_plan_id,
                MealPlanRecipe.day == to_day,
                MealPlanRecipe.meal_type == to_meal_type
            ).first()
            
            if existing_meal:
                # If there's already a meal, swap them
                temp_day = db_recipe.day
                temp_meal_type = db_recipe.meal_type
                
                db_recipe.day = to_day
                db_recipe.meal_type = to_meal_type
                
                existing_meal.day = temp_day
                existing_meal.meal_type = temp_meal_type
            else:
                # Otherwise, just move the meal
                db_recipe.day = to_day
                db_recipe.meal_type = to_meal_type
                
            db.commit()
            return True
        return False

    def update_meal_plan_data(self, db: Session, meal_plan_id: int, new_plan_data: str):
        """Update the meal plan data JSON"""
        db_meal_plan = db.query(MealPlan).filter(MealPlan.id == meal_plan_id).first()
        if db_meal_plan:
            db_meal_plan.plan_data = new_plan_data
            db_meal_plan.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_meal_plan)
            return db_meal_plan
        return None

    def clear_meal_plan_recipes(self, db: Session, meal_plan_id: int):
        """Clear all recipes from a meal plan"""
        db.query(MealPlanRecipe).filter(MealPlanRecipe.meal_plan_id == meal_plan_id).delete()
        db.commit()

    def update_meal_plan(self, db: Session, meal_plan_id: int, plan_name: str = None, plan_data: str = None, plan_explanation: str = None):
        """Update meal plan metadata"""
        db_meal_plan = db.query(MealPlan).filter(MealPlan.id == meal_plan_id).first()
        if db_meal_plan:
            if plan_name:
                db_meal_plan.plan_name = plan_name
            if plan_data:
                db_meal_plan.plan_data = plan_data
            if plan_explanation:
                db_meal_plan.plan_explanation = plan_explanation
            db_meal_plan.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_meal_plan)
            return db_meal_plan
        return None