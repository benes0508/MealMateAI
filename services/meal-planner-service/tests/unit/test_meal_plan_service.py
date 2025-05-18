import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.meal_plan_service import MealPlanService
from tests.conftest import get_test_recipes, get_test_retrieved_recipes, get_test_meal_plan, get_test_grocery_list


class TestMealPlanService:
    """Test suite for the MealPlanService class."""

    @pytest.fixture
    def meal_plan_service(self, mock_microservice_client, mock_embeddings_service, mock_gemini_service):
        """Create a MealPlanService with mocked dependencies."""
        with patch("app.services.meal_plan_service.MealPlanRepository") as mock_repo:
            repo_instance = mock_repo.return_value
            
            # Set up repository mock methods
            repo_instance.create_meal_plan = MagicMock()
            repo_instance.add_recipe_to_meal_plan = MagicMock()
            repo_instance.get_meal_plan = MagicMock()
            repo_instance.get_meal_plan_recipes = MagicMock()
            repo_instance.get_user_meal_plans = MagicMock()
            repo_instance.delete_meal_plan = MagicMock()
            repo_instance.get_cached_user_preferences = MagicMock()
            repo_instance.cache_user_preferences = MagicMock()
            
            # Create and return the service
            service = MealPlanService()
            service.meal_plan_repository = repo_instance
            service.microservice_client = mock_microservice_client
            service.gemini_service = mock_gemini_service
            service.embeddings_service = mock_embeddings_service
            return service

    @pytest.mark.asyncio
    async def test_create_meal_plan(self, meal_plan_service, db_session, sample_meal_plan):
        """Test creating a meal plan with RAG and Gemini."""
        # Arrange
        user_id = 1
        days = 7
        meals_per_day = 3
        
        # Configure mocks
        meal_plan_service.meal_plan_repository.get_cached_user_preferences.return_value = None
        meal_plan_service.meal_plan_repository.create_meal_plan.return_value = sample_meal_plan
        
        test_meal_plan_data = get_test_meal_plan()
        meal_plan_service.gemini_service.generate_meal_plan.return_value = test_meal_plan_data

        # Act
        result = await meal_plan_service.create_meal_plan(
            db=db_session,
            user_id=user_id,
            days=days,
            meals_per_day=meals_per_day
        )

        # Assert
        assert result is not None
        assert "id" in result
        assert "meal_plan" in result
        assert "plan_explanation" in result
        
        # Verify method calls
        meal_plan_service.microservice_client.get_recipes.assert_called_once()
        meal_plan_service.embeddings_service.batch_store_recipe_embeddings.assert_called_once()
        meal_plan_service.embeddings_service.find_recipes_for_preferences.assert_called_once()
        meal_plan_service.gemini_service.generate_meal_plan.assert_called_once()
        meal_plan_service.meal_plan_repository.create_meal_plan.assert_called_once()
        
        # Verify at least one recipe was added to the meal plan
        assert meal_plan_service.meal_plan_repository.add_recipe_to_meal_plan.call_count > 0

    @pytest.mark.asyncio
    async def test_create_meal_plan_with_cached_preferences(self, meal_plan_service, db_session, sample_meal_plan):
        """Test creating a meal plan with cached user preferences."""
        # Arrange
        user_id = 1
        cached_prefs = {
            "dietary_restrictions": ["vegetarian"],
            "allergies": ["peanuts"],
            "cuisine_preferences": ["Italian"],
            "disliked_ingredients": ["cilantro"]
        }
        
        # Configure mocks
        meal_plan_service.meal_plan_repository.get_cached_user_preferences.return_value = cached_prefs
        meal_plan_service.meal_plan_repository.create_meal_plan.return_value = sample_meal_plan
        
        # Act
        result = await meal_plan_service.create_meal_plan(db=db_session, user_id=user_id)
        
        # Assert
        assert result is not None
        
        # Verify the cached preferences were used
        meal_plan_service.meal_plan_repository.get_cached_user_preferences.assert_called_once_with(db_session, user_id)
        meal_plan_service.microservice_client.get_user_allergies.assert_not_called()
        meal_plan_service.microservice_client.get_user_diet_restrictions.assert_not_called()
        meal_plan_service.microservice_client.get_user_preferences.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_meal_plan_no_matching_recipes(self, meal_plan_service, db_session, sample_meal_plan):
        """Test creating a meal plan when no recipes match preferences."""
        # Arrange
        user_id = 1
        
        # Configure mocks
        meal_plan_service.meal_plan_repository.create_meal_plan.return_value = sample_meal_plan
        meal_plan_service.embeddings_service.find_recipes_for_preferences.return_value = []
        meal_plan_service.microservice_client.get_recipes.return_value = get_test_recipes()
        
        # Act
        result = await meal_plan_service.create_meal_plan(db=db_session, user_id=user_id)
        
        # Assert
        assert result is not None
        
        # Verify fallback to all recipes when none match preferences
        meal_plan_service.gemini_service.generate_meal_plan.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_meal_plan(self, meal_plan_service, db_session, sample_meal_plan):
        """Test getting a meal plan by ID."""
        # Arrange
        meal_plan_id = 1
        meal_plan_service.meal_plan_repository.get_meal_plan.return_value = sample_meal_plan
        meal_plan_service.meal_plan_repository.get_meal_plan_recipes.return_value = [
            MagicMock(recipe_id=1, day=1, meal_type="breakfast"),
            MagicMock(recipe_id=2, day=1, meal_type="lunch")
        ]
        
        # Act
        result = await meal_plan_service.get_meal_plan(db=db_session, meal_plan_id=meal_plan_id)
        
        # Assert
        assert result is not None
        assert "id" in result
        assert "meal_plan" in result
        assert "recipes" in result
        assert len(result["recipes"]) == 2
        
        # Verify method calls
        meal_plan_service.meal_plan_repository.get_meal_plan.assert_called_once_with(db_session, meal_plan_id)
        meal_plan_service.meal_plan_repository.get_meal_plan_recipes.assert_called_once_with(db_session, meal_plan_id)

    @pytest.mark.asyncio
    async def test_get_meal_plan_not_found(self, meal_plan_service, db_session):
        """Test getting a meal plan that doesn't exist."""
        # Arrange
        meal_plan_id = 999
        meal_plan_service.meal_plan_repository.get_meal_plan.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Meal plan {meal_plan_id} not found"):
            await meal_plan_service.get_meal_plan(db=db_session, meal_plan_id=meal_plan_id)

    @pytest.mark.asyncio
    async def test_get_user_meal_plans(self, meal_plan_service, db_session, sample_meal_plan):
        """Test getting all meal plans for a user."""
        # Arrange
        user_id = 1
        meal_plan_service.meal_plan_repository.get_user_meal_plans.return_value = [sample_meal_plan]
        
        # Act
        result = await meal_plan_service.get_user_meal_plans(db=db_session, user_id=user_id)
        
        # Assert
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert "id" in result[0]
        assert "plan_name" in result[0]
        
        # Verify method calls
        meal_plan_service.meal_plan_repository.get_user_meal_plans.assert_called_once_with(db_session, user_id)

    @pytest.mark.asyncio
    async def test_process_text_input(self, meal_plan_service, db_session):
        """Test processing natural language text input."""
        # Arrange
        user_id = 1
        input_text = "I want a 5-day vegetarian meal plan with Italian recipes"
        
        # Mock the create_meal_plan method
        meal_plan_service.create_meal_plan = AsyncMock(return_value={"id": 1, "plan_name": "Test Plan"})
        
        # Act
        result = await meal_plan_service.process_text_input(
            db=db_session,
            user_id=user_id,
            input_text=input_text
        )
        
        # Assert
        assert result is not None
        
        # Verify create_meal_plan was called with the correct parameters
        meal_plan_service.create_meal_plan.assert_called_once()
        call_args = meal_plan_service.create_meal_plan.call_args[1]
        assert call_args["user_id"] == user_id
        assert call_args["additional_preferences"] == input_text
        
        # Check if days parameter was extracted from text
        assert "days" in call_args
        assert call_args["days"] == 5  # Should extract 5 days from the input text

    @pytest.mark.asyncio
    async def test_process_text_input_with_snacks(self, meal_plan_service, db_session):
        """Test processing text input requesting snacks."""
        # Arrange
        user_id = 1
        input_text = "I want a meal plan with snacks included"
        
        # Mock the create_meal_plan method
        meal_plan_service.create_meal_plan = AsyncMock(return_value={"id": 1, "plan_name": "Test Plan"})
        
        # Act
        result = await meal_plan_service.process_text_input(
            db=db_session,
            user_id=user_id,
            input_text=input_text
        )
        
        # Assert
        assert result is not None
        
        # Verify create_meal_plan was called with include_snacks=True
        meal_plan_service.create_meal_plan.assert_called_once()
        call_args = meal_plan_service.create_meal_plan.call_args[1]
        assert call_args["include_snacks"] is True

    @pytest.mark.asyncio
    async def test_generate_grocery_list(self, meal_plan_service, db_session, sample_meal_plan):
        """Test generating a grocery list for a meal plan."""
        # Arrange
        meal_plan_id = 1
        
        # Configure mocks
        meal_plan_service.meal_plan_repository.get_meal_plan.return_value = sample_meal_plan
        meal_plan_service.meal_plan_repository.get_meal_plan_recipes.return_value = [
            MagicMock(recipe_id=1, day=1, meal_type="breakfast"),
            MagicMock(recipe_id=2, day=1, meal_type="lunch")
        ]
        meal_plan_service.microservice_client.get_recipe.side_effect = [
            get_test_recipes()[0],
            get_test_recipes()[1]
        ]
        meal_plan_service.gemini_service.generate_grocery_list.return_value = get_test_grocery_list()
        
        # Act
        result = await meal_plan_service.generate_grocery_list(db=db_session, meal_plan_id=meal_plan_id)
        
        # Assert
        assert result is not None
        assert "grocery_list" in result
        assert isinstance(result["grocery_list"], list)
        
        # Verify method calls
        meal_plan_service.meal_plan_repository.get_meal_plan.assert_called_once_with(db_session, meal_plan_id)
        meal_plan_service.meal_plan_repository.get_meal_plan_recipes.assert_called_once_with(db_session, meal_plan_id)
        assert meal_plan_service.microservice_client.get_recipe.call_count == 2
        meal_plan_service.gemini_service.generate_grocery_list.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_grocery_list_meal_plan_not_found(self, meal_plan_service, db_session):
        """Test generating a grocery list for a non-existent meal plan."""
        # Arrange
        meal_plan_id = 999
        meal_plan_service.meal_plan_repository.get_meal_plan.return_value = None
        
        # Act & Assert
        with pytest.raises(ValueError, match=f"Meal plan {meal_plan_id} not found"):
            await meal_plan_service.generate_grocery_list(db=db_session, meal_plan_id=meal_plan_id)

    @pytest.mark.asyncio
    async def test_delete_meal_plan(self, meal_plan_service, db_session, sample_meal_plan):
        """Test deleting a meal plan."""
        # Arrange
        meal_plan_id = 1
        meal_plan_service.meal_plan_repository.get_meal_plan.return_value = sample_meal_plan
        
        # Act
        result = await meal_plan_service.delete_meal_plan(db=db_session, meal_plan_id=meal_plan_id)
        
        # Assert
        assert result is True
        
        # Verify method calls
        meal_plan_service.meal_plan_repository.get_meal_plan.assert_called_once_with(db_session, meal_plan_id)
        meal_plan_service.meal_plan_repository.delete_meal_plan.assert_called_once_with(db_session, meal_plan_id)

    @pytest.mark.asyncio
    async def test_delete_meal_plan_not_found(self, meal_plan_service, db_session):
        """Test deleting a non-existent meal plan."""
        # Arrange
        meal_plan_id = 999
        meal_plan_service.meal_plan_repository.get_meal_plan.return_value = None
        
        # Act
        result = await meal_plan_service.delete_meal_plan(db=db_session, meal_plan_id=meal_plan_id)
        
        # Assert
        assert result is False
        meal_plan_service.meal_plan_repository.delete_meal_plan.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_preferences_no_cache(self, meal_plan_service, db_session):
        """Test getting user preferences with no cached data."""
        # Arrange
        user_id = 1
        meal_plan_service.meal_plan_repository.get_cached_user_preferences.return_value = None
        
        # Set up microservice client mock return values
        meal_plan_service.microservice_client.get_user_allergies.return_value = {
            "allergies": ["peanuts", "shellfish"]
        }
        meal_plan_service.microservice_client.get_user_diet_restrictions.return_value = {
            "dietary_restrictions": ["vegetarian"]
        }
        meal_plan_service.microservice_client.get_user_preferences.return_value = {
            "cuisine_preferences": ["Italian", "Mexican"],
            "disliked_ingredients": ["cilantro"]
        }
        
        # Act
        result = await meal_plan_service._get_user_preferences(db=db_session, user_id=user_id)
        
        # Assert
        assert result is not None
        assert "allergies" in result
        assert "dietary_restrictions" in result
        assert "cuisine_preferences" in result
        assert "disliked_ingredients" in result
        
        # Verify method calls
        meal_plan_service.microservice_client.get_user_allergies.assert_called_once_with(user_id)
        meal_plan_service.microservice_client.get_user_diet_restrictions.assert_called_once_with(user_id)
        meal_plan_service.microservice_client.get_user_preferences.assert_called_once_with(user_id)
        meal_plan_service.meal_plan_repository.cache_user_preferences.assert_called_once_with(db_session, user_id, result)