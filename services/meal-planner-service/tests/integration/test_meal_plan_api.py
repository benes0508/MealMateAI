import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock
from app.main import app
from tests.conftest import get_test_meal_plan, get_test_grocery_list


class TestMealPlanAPI:
    """Integration tests for the meal plan API endpoints."""

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_create_meal_plan(self, mock_service, client):
        """Test creating a meal plan via API."""
        # Arrange
        mock_service.create_meal_plan.return_value = {
            "id": 1,
            "user_id": 1,
            "plan_name": "Test Plan",
            "created_at": "2025-05-14T12:00:00",
            "days": 7,
            "meals_per_day": 3,
            "plan_explanation": "This is a test plan",
            "meal_plan": get_test_meal_plan()["meal_plan"]
        }
        
        # Set up the request
        meal_plan_request = {
            "user_id": 1,
            "days": 7,
            "meals_per_day": 3,
            "include_snacks": True,
            "additional_preferences": "I want healthy meals under 500 calories"
        }
        
        # Act
        response = client.post("/api/meal-planner/", json=meal_plan_request)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["user_id"] == 1
        assert data["days"] == 7
        
        # Verify service method was called
        mock_service.create_meal_plan.assert_called_once()

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_get_meal_plan(self, mock_service, client):
        """Test retrieving a meal plan by ID."""
        # Arrange
        meal_plan_id = 1
        mock_service.get_meal_plan.return_value = {
            "id": meal_plan_id,
            "user_id": 1,
            "plan_name": "Test Plan",
            "created_at": "2025-05-14T12:00:00",
            "days": 7,
            "meals_per_day": 3,
            "plan_explanation": "This is a test plan",
            "meal_plan": get_test_meal_plan()["meal_plan"],
            "recipes": [
                {"recipe_id": 1, "day": 1, "meal_type": "breakfast"},
                {"recipe_id": 2, "day": 1, "meal_type": "lunch"}
            ]
        }
        
        # Act
        response = client.get(f"/api/meal-planner/{meal_plan_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == meal_plan_id
        assert "meal_plan" in data
        assert "recipes" in data
        
        # Verify service method was called
        mock_service.get_meal_plan.assert_called_once()

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_get_meal_plan_not_found(self, mock_service, client):
        """Test retrieving a non-existent meal plan."""
        # Arrange
        meal_plan_id = 999
        mock_service.get_meal_plan.side_effect = ValueError(f"Meal plan {meal_plan_id} not found")
        
        # Act
        response = client.get(f"/api/meal-planner/{meal_plan_id}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert f"Meal plan {meal_plan_id} not found" in data["detail"]

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_get_user_meal_plans(self, mock_service, client):
        """Test retrieving all meal plans for a user."""
        # Arrange
        user_id = 1
        mock_service.get_user_meal_plans.return_value = [
            {
                "id": 1,
                "user_id": user_id,
                "plan_name": "Weekly Plan",
                "created_at": "2025-05-14T12:00:00",
                "days": 7,
                "meals_per_day": 3
            },
            {
                "id": 2,
                "user_id": user_id,
                "plan_name": "Weekend Plan",
                "created_at": "2025-05-13T12:00:00",
                "days": 2,
                "meals_per_day": 3
            }
        ]
        
        # Act
        response = client.get(f"/api/meal-planner/user/{user_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["user_id"] == user_id
        assert data[1]["user_id"] == user_id
        
        # Verify service method was called
        mock_service.get_user_meal_plans.assert_called_once()

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_get_grocery_list(self, mock_service, client):
        """Test generating a grocery list for a meal plan."""
        # Arrange
        meal_plan_id = 1
        mock_service.generate_grocery_list.return_value = get_test_grocery_list()
        
        # Act
        response = client.get(f"/api/meal-planner/{meal_plan_id}/grocery-list")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "grocery_list" in data
        assert len(data["grocery_list"]) > 0
        
        # Verify service method was called
        mock_service.generate_grocery_list.assert_called_once()

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_delete_meal_plan(self, mock_service, client):
        """Test deleting a meal plan."""
        # Arrange
        meal_plan_id = 1
        mock_service.delete_meal_plan.return_value = True
        
        # Act
        response = client.delete(f"/api/meal-planner/{meal_plan_id}")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert f"Meal plan {meal_plan_id} deleted successfully" in data["message"]
        
        # Verify service method was called
        mock_service.delete_meal_plan.assert_called_once()

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_delete_meal_plan_not_found(self, mock_service, client):
        """Test deleting a non-existent meal plan."""
        # Arrange
        meal_plan_id = 999
        mock_service.delete_meal_plan.return_value = False
        
        # Act
        response = client.delete(f"/api/meal-planner/{meal_plan_id}")
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert f"Meal plan {meal_plan_id} not found" in data["detail"]

    @patch("app.controllers.meal_plan_controller.meal_plan_service")
    def test_process_text_input(self, mock_service, client):
        """Test processing natural language text input."""
        # Arrange
        user_id = 1
        input_text = "I want a 5-day meal plan with Mediterranean recipes"
        mock_service.process_text_input.return_value = {
            "id": 1,
            "user_id": user_id,
            "plan_name": "5-Day Meal Plan (Mediterranean)",
            "created_at": "2025-05-14T12:00:00",
            "days": 5,
            "meals_per_day": 3,
            "plan_explanation": "This is a Mediterranean meal plan",
            "meal_plan": get_test_meal_plan()["meal_plan"]
        }
        
        # Set up the request
        request_data = {"input_text": input_text}
        
        # Act
        response = client.post(f"/api/meal-planner/text-input?user_id={user_id}", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["user_id"] == user_id
        assert data["days"] == 5  # Should extract 5 days from the input text
        assert "Mediterranean" in data["plan_name"]
        
        # Verify service method was called
        mock_service.process_text_input.assert_called_once_with(
            db=pytest.mock.ANY,
            user_id=user_id,
            input_text=input_text
        )

    @patch("app.controllers.meal_plan_controller.EmbeddingsService")
    @patch("app.controllers.meal_plan_controller.MicroserviceClient")
    def test_index_recipes(self, mock_microservice_client, mock_embeddings_service, client):
        """Test the recipe indexing endpoint."""
        # Arrange
        mock_client_instance = mock_microservice_client.return_value
        mock_client_instance.get_recipes = AsyncMock(return_value=[
            {"id": 1, "name": "Recipe 1"},
            {"id": 2, "name": "Recipe 2"}
        ])
        
        mock_embeddings_instance = mock_embeddings_service.return_value
        mock_embeddings_instance.batch_store_recipe_embeddings = AsyncMock(return_value=True)
        
        # Act
        response = client.post("/api/meal-planner/index-recipes")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Successfully indexed" in data["message"]
        
        # Verify service methods were called
        mock_client_instance.get_recipes.assert_called_once()
        mock_embeddings_instance.batch_store_recipe_embeddings.assert_called_once()

    @patch("app.controllers.meal_plan_controller.EmbeddingsService")
    @patch("app.controllers.meal_plan_controller.MicroserviceClient")
    def test_index_recipes_empty(self, mock_microservice_client, mock_embeddings_service, client):
        """Test indexing when no recipes are found."""
        # Arrange
        mock_client_instance = mock_microservice_client.return_value
        mock_client_instance.get_recipes = AsyncMock(return_value=[])
        
        # Act
        response = client.post("/api/meal-planner/index-recipes")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "No recipes found to index" in data["message"]