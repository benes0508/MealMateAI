import json
import pytest
from app.repositories.meal_plan_repository import MealPlanRepository


class TestMealPlanRepository:
    """Test suite for the MealPlanRepository class."""

    def test_create_meal_plan(self, db_session):
        """Test creating a new meal plan."""
        # Arrange
        repo = MealPlanRepository()
        user_id = 1
        plan_name = "Test Plan"
        days = 7
        meals_per_day = 3
        plan_data = {"day": 1, "meals": [{"recipe_id": 1, "meal_type": "breakfast"}]}
        plan_explanation = "Test explanation"

        # Act
        meal_plan = repo.create_meal_plan(
            db=db_session,
            user_id=user_id,
            plan_name=plan_name,
            days=days,
            meals_per_day=meals_per_day,
            plan_data=json.dumps(plan_data),
            plan_explanation=plan_explanation
        )

        # Assert
        assert meal_plan is not None
        assert meal_plan.user_id == user_id
        assert meal_plan.plan_name == plan_name
        assert meal_plan.days == days
        assert meal_plan.meals_per_day == meals_per_day
        assert meal_plan.plan_explanation == plan_explanation

    def test_add_recipe_to_meal_plan(self, db_session, sample_meal_plan):
        """Test adding a recipe to an existing meal plan."""
        # Arrange
        repo = MealPlanRepository()
        meal_plan_id = sample_meal_plan.id
        recipe_id = 100
        day = 1
        meal_type = "snack"

        # Act
        recipe = repo.add_recipe_to_meal_plan(
            db=db_session,
            meal_plan_id=meal_plan_id,
            recipe_id=recipe_id,
            day=day,
            meal_type=meal_type
        )

        # Assert
        assert recipe is not None
        assert recipe.meal_plan_id == meal_plan_id
        assert recipe.recipe_id == recipe_id
        assert recipe.day == day
        assert recipe.meal_type == meal_type

    def test_get_meal_plan(self, db_session, sample_meal_plan):
        """Test getting a meal plan by ID."""
        # Arrange
        repo = MealPlanRepository()

        # Act
        meal_plan = repo.get_meal_plan(db_session, sample_meal_plan.id)

        # Assert
        assert meal_plan is not None
        assert meal_plan.id == sample_meal_plan.id
        assert meal_plan.user_id == sample_meal_plan.user_id
        assert meal_plan.plan_name == sample_meal_plan.plan_name

    def test_get_meal_plan_recipes(self, db_session, sample_meal_plan):
        """Test getting recipes for a meal plan."""
        # Arrange
        repo = MealPlanRepository()

        # Act
        recipes = repo.get_meal_plan_recipes(db_session, sample_meal_plan.id)

        # Assert
        assert recipes is not None
        assert len(recipes) == 21  # 7 days x 3 meals per day

    def test_get_user_meal_plans(self, db_session, sample_meal_plan):
        """Test getting meal plans for a user."""
        # Arrange
        repo = MealPlanRepository()

        # Act
        meal_plans = repo.get_user_meal_plans(db_session, sample_meal_plan.user_id)

        # Assert
        assert meal_plans is not None
        assert len(meal_plans) == 1
        assert meal_plans[0].id == sample_meal_plan.id

    def test_delete_meal_plan(self, db_session, sample_meal_plan):
        """Test deleting a meal plan."""
        # Arrange
        repo = MealPlanRepository()

        # Act
        repo.delete_meal_plan(db_session, sample_meal_plan.id)
        deleted_plan = repo.get_meal_plan(db_session, sample_meal_plan.id)

        # Assert
        assert deleted_plan is None

    def test_cache_user_preferences_create(self, db_session):
        """Test creating new user preferences cache."""
        # Arrange
        repo = MealPlanRepository()
        user_id = 999
        preferences = {
            "dietary_restrictions": ["vegan"],
            "allergies": ["nuts"],
            "cuisine_preferences": ["Indian"],
            "disliked_ingredients": ["onions"]
        }

        # Act
        result = repo.cache_user_preferences(db_session, user_id, preferences)

        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert json.loads(result.dietary_restrictions) == preferences["dietary_restrictions"]
        assert json.loads(result.allergies) == preferences["allergies"]
        assert json.loads(result.cuisine_preferences) == preferences["cuisine_preferences"]
        assert json.loads(result.disliked_ingredients) == preferences["disliked_ingredients"]

    def test_cache_user_preferences_update(self, db_session, sample_user_preference):
        """Test updating existing user preferences cache."""
        # Arrange
        repo = MealPlanRepository()
        user_id = sample_user_preference.user_id
        preferences = {
            "dietary_restrictions": ["vegan"],
            "allergies": ["nuts"],
            "cuisine_preferences": ["Indian"],
            "disliked_ingredients": ["onions"]
        }

        # Act
        result = repo.cache_user_preferences(db_session, user_id, preferences)

        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert json.loads(result.dietary_restrictions) == preferences["dietary_restrictions"]
        assert json.loads(result.allergies) == preferences["allergies"]
        assert json.loads(result.cuisine_preferences) == preferences["cuisine_preferences"]
        assert json.loads(result.disliked_ingredients) == preferences["disliked_ingredients"]

    def test_get_cached_user_preferences(self, db_session, sample_user_preference):
        """Test getting cached user preferences."""
        # Arrange
        repo = MealPlanRepository()

        # Act
        preferences = repo.get_cached_user_preferences(db_session, sample_user_preference.user_id)

        # Assert
        assert preferences is not None
        assert preferences["dietary_restrictions"] == ["vegetarian"]
        assert preferences["allergies"] == ["peanuts", "shellfish"]
        assert preferences["cuisine_preferences"] == ["Italian", "Mexican"]
        assert preferences["disliked_ingredients"] == ["cilantro"]

    def test_get_cached_user_preferences_not_found(self, db_session):
        """Test getting cached user preferences when not found."""
        # Arrange
        repo = MealPlanRepository()
        user_id = 999

        # Act
        preferences = repo.get_cached_user_preferences(db_session, user_id)

        # Assert
        assert preferences is None