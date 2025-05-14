import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from langchain.chains import LLMChain
from app.services.gemini_service import GeminiService
from tests.conftest import get_test_retrieved_recipes, get_test_meal_plan, get_test_grocery_list


class TestGeminiService:
    """Test suite for the GeminiService class."""

    @pytest.fixture
    def mock_llm(self):
        """Mock the ChatGoogleGenerativeAI LLM."""
        with patch("app.services.gemini_service.ChatGoogleGenerativeAI") as mock:
            mock_llm = mock.return_value
            yield mock_llm

    @pytest.fixture
    def mock_chain(self):
        """Mock the LLMChain."""
        with patch("app.services.gemini_service.LLMChain") as mock:
            mock_chain = mock.return_value
            mock_chain.run = MagicMock(return_value=json.dumps(get_test_meal_plan()))
            yield mock_chain

    @pytest.fixture
    def gemini_service(self, mock_llm, mock_chain):
        """Create a GeminiService with mocked dependencies."""
        with patch("app.services.gemini_service.genai.configure"):
            with patch("app.services.gemini_service.LLMChain", return_value=mock_chain):
                service = GeminiService()
                service.llm = mock_llm
                return service

    def test_generate_meal_plan(self, gemini_service, mock_chain):
        """Test generating a meal plan using Gemini LLM."""
        # Arrange
        user_preferences = {
            "dietary_restrictions": ["vegetarian"],
            "allergies": ["peanuts", "shellfish"],
            "cuisine_preferences": ["Italian", "Mexican"],
            "disliked_ingredients": ["cilantro"]
        }
        retrieved_recipes = get_test_retrieved_recipes()
        days = 7
        meals_per_day = 3
        include_snacks = False
        additional_preferences = "I want healthy meals"

        # Act
        result = gemini_service.generate_meal_plan(
            user_preferences=user_preferences,
            retrieved_recipes=retrieved_recipes,
            days=days,
            meals_per_day=meals_per_day,
            include_snacks=include_snacks,
            additional_preferences=additional_preferences
        )

        # Assert
        assert result is not None
        assert "meal_plan" in result
        assert "explanation" in result
        mock_chain.run.assert_called_once()
        
        # Verify the meal plan structure
        assert isinstance(result["meal_plan"], list)
        assert len(result["meal_plan"]) > 0
        day_plan = result["meal_plan"][0]
        assert "day" in day_plan
        assert "meals" in day_plan
        assert len(day_plan["meals"]) > 0
        meal = day_plan["meals"][0]
        assert "meal_type" in meal
        assert "recipe_id" in meal
        assert "recipe_name" in meal

    def test_generate_meal_plan_json_error(self, gemini_service, mock_chain):
        """Test generating a meal plan when JSON parsing fails."""
        # Arrange
        mock_chain.run.return_value = "This is not JSON"
        user_preferences = {
            "dietary_restrictions": ["vegetarian"],
            "allergies": []
        }
        retrieved_recipes = get_test_retrieved_recipes()

        # Patch the fallback method to return a known value
        gemini_service._create_fallback_meal_plan = MagicMock(return_value={
            "meal_plan": [{"day": 1, "meals": []}],
            "explanation": "Fallback plan"
        })

        # Act
        result = gemini_service.generate_meal_plan(
            user_preferences=user_preferences,
            retrieved_recipes=retrieved_recipes
        )

        # Assert
        assert result is not None
        assert "meal_plan" in result
        assert "explanation" in result
        gemini_service._create_fallback_meal_plan.assert_called_once()

    def test_generate_meal_plan_exception(self, gemini_service, mock_chain):
        """Test generating a meal plan when an exception occurs."""
        # Arrange
        mock_chain.run.side_effect = Exception("Test exception")
        user_preferences = {
            "dietary_restrictions": ["vegetarian"],
            "allergies": []
        }
        retrieved_recipes = get_test_retrieved_recipes()

        # Patch the fallback method to return a known value
        gemini_service._create_fallback_meal_plan = MagicMock(return_value={
            "meal_plan": [{"day": 1, "meals": []}],
            "explanation": "Fallback plan"
        })

        # Act
        result = gemini_service.generate_meal_plan(
            user_preferences=user_preferences,
            retrieved_recipes=retrieved_recipes
        )

        # Assert
        assert result is not None
        assert "meal_plan" in result
        assert "explanation" in result
        gemini_service._create_fallback_meal_plan.assert_called_once()

    def test_generate_grocery_list(self, gemini_service, mock_chain):
        """Test generating a grocery list using Gemini LLM."""
        # Arrange
        recipes = [
            {
                "id": 1,
                "name": "Avocado Toast",
                "ingredients": [
                    {"name": "bread", "amount": 2, "unit": "slices"},
                    {"name": "avocado", "amount": 1, "unit": ""}
                ]
            }
        ]
        
        # Set the mock_chain to return a grocery list
        mock_chain.run.return_value = json.dumps(get_test_grocery_list())

        # Act
        result = gemini_service.generate_grocery_list(recipes)

        # Assert
        assert result is not None
        assert "grocery_list" in result
        assert isinstance(result["grocery_list"], list)
        
        # Verify the grocery list structure
        assert len(result["grocery_list"]) > 0
        category = result["grocery_list"][0]
        assert "category" in category
        assert "items" in category
        assert len(category["items"]) > 0
        item = category["items"][0]
        assert "name" in item
        assert "amount" in item
        mock_chain.run.assert_called_once()

    def test_generate_grocery_list_json_error(self, gemini_service, mock_chain):
        """Test generating a grocery list when JSON parsing fails."""
        # Arrange
        mock_chain.run.return_value = "This is not JSON"
        recipes = [{"ingredients": [{"name": "bread"}]}]

        # Patch the fallback method to return a known value
        gemini_service._create_fallback_grocery_list = MagicMock(return_value=[{
            "category": "All",
            "items": [{"name": "bread", "amount": "as needed"}]
        }])

        # Act
        result = gemini_service.generate_grocery_list(recipes)

        # Assert
        assert result is not None
        assert "grocery_list" in result
        gemini_service._create_fallback_grocery_list.assert_called_once()

    def test_create_meal_plan_prompt_template(self, gemini_service):
        """Test creating the meal plan prompt template."""
        # Act
        template = gemini_service._create_meal_plan_prompt_template()

        # Assert
        assert template is not None
        # Check that all required input variables are included in the template
        required_variables = [
            "recipe_context", "dietary_restrictions", "allergies", 
            "cuisine_preferences", "disliked_ingredients", "days", 
            "meals_per_day", "include_snacks", "additional_preferences"
        ]
        for var in required_variables:
            assert var in template.input_variables

    def test_create_grocery_list_prompt_template(self, gemini_service):
        """Test creating the grocery list prompt template."""
        # Act
        template = gemini_service._create_grocery_list_prompt_template()

        # Assert
        assert template is not None
        assert "ingredients" in template.input_variables

    def test_create_fallback_meal_plan(self, gemini_service):
        """Test creating a fallback meal plan."""
        # Arrange
        retrieved_recipes = get_test_retrieved_recipes()
        days = 3
        meals_per_day = 2

        # Act
        result = gemini_service._create_fallback_meal_plan(retrieved_recipes, days, meals_per_day)

        # Assert
        assert result is not None
        assert "meal_plan" in result
        assert "explanation" in result
        assert len(result["meal_plan"]) == days
        for day_plan in result["meal_plan"]:
            assert len(day_plan["meals"]) == meals_per_day

    def test_create_fallback_grocery_list(self, gemini_service):
        """Test creating a fallback grocery list."""
        # Arrange
        ingredients = [
            {"name": "bread", "amount": 2, "unit": "slices"},
            {"name": "avocado", "amount": 1}
        ]

        # Act
        result = gemini_service._create_fallback_grocery_list(ingredients)

        # Assert
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert "category" in result[0]
        assert "items" in result[0]
        assert len(result[0]["items"]) == len(ingredients)