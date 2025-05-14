import os
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import AsyncMock, patch
import sys

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.main import app
from app.models.models import MealPlan, MealPlanRecipe, UserPreference


# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a clean database session for a test case.
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client using the test database session.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def mock_microservice_client():
    """
    Mock the MicroserviceClient to avoid actual HTTP requests during tests.
    """
    with patch("app.services.microservice_client.MicroserviceClient") as mock:
        client_instance = mock.return_value
        client_instance.get_recipes = AsyncMock()
        client_instance.get_recipe = AsyncMock()
        client_instance.get_user_preferences = AsyncMock()
        client_instance.get_user_allergies = AsyncMock()
        client_instance.get_user_diet_restrictions = AsyncMock()
        
        # Set up default return values
        client_instance.get_recipes.return_value = get_test_recipes()
        client_instance.get_recipe.return_value = get_test_recipes()[0]
        client_instance.get_user_preferences.return_value = {
            "cuisine_preferences": ["Italian", "Mexican"],
            "disliked_ingredients": ["cilantro"]
        }
        client_instance.get_user_allergies.return_value = {
            "allergies": ["peanuts", "shellfish"]
        }
        client_instance.get_user_diet_restrictions.return_value = {
            "dietary_restrictions": ["vegetarian"]
        }
        
        yield client_instance


@pytest.fixture(scope="function")
def mock_embeddings_service():
    """
    Mock the EmbeddingsService to avoid generating actual embeddings during tests.
    """
    with patch("app.services.embeddings_service.EmbeddingsService") as mock:
        service_instance = mock.return_value
        service_instance.generate_recipe_embedding = AsyncMock()
        service_instance.store_recipe_embedding = AsyncMock()
        service_instance.batch_store_recipe_embeddings = AsyncMock()
        service_instance.find_similar_recipes = AsyncMock()
        service_instance.find_recipes_for_preferences = AsyncMock()
        
        # Set up default return values
        service_instance.generate_recipe_embedding.return_value = [0.1] * 768
        service_instance.store_recipe_embedding.return_value = True
        service_instance.batch_store_recipe_embeddings.return_value = True
        service_instance.find_similar_recipes.return_value = get_test_retrieved_recipes()
        service_instance.find_recipes_for_preferences.return_value = get_test_retrieved_recipes()
        
        yield service_instance


@pytest.fixture(scope="function")
def mock_gemini_service():
    """
    Mock the GeminiService to avoid actual LLM API calls during tests.
    """
    with patch("app.services.gemini_service.GeminiService") as mock:
        service_instance = mock.return_value
        service_instance.generate_meal_plan = AsyncMock()
        service_instance.generate_grocery_list = AsyncMock()
        
        # Set up default return values
        service_instance.generate_meal_plan.return_value = get_test_meal_plan()
        service_instance.generate_grocery_list.return_value = get_test_grocery_list()
        
        yield service_instance


@pytest.fixture(scope="function")
def sample_meal_plan(db_session):
    """
    Create a sample meal plan in the test database.
    """
    meal_plan = MealPlan(
        user_id=1,
        plan_name="Test Meal Plan",
        days=7,
        meals_per_day=3,
        plan_data=json.dumps(get_test_meal_plan()["meal_plan"]),
        plan_explanation="This is a test meal plan"
    )
    db_session.add(meal_plan)
    db_session.commit()
    
    # Add recipes to the meal plan
    for day in range(1, 8):
        for meal_type in ["breakfast", "lunch", "dinner"]:
            recipe = MealPlanRecipe(
                meal_plan_id=meal_plan.id,
                recipe_id=day + (0 if meal_type == "breakfast" else 5 if meal_type == "lunch" else 10),
                day=day,
                meal_type=meal_type
            )
            db_session.add(recipe)
    
    db_session.commit()
    return meal_plan


@pytest.fixture(scope="function")
def sample_user_preference(db_session):
    """
    Create a sample user preference in the test database.
    """
    preference = UserPreference(
        user_id=1,
        dietary_restrictions=json.dumps(["vegetarian"]),
        allergies=json.dumps(["peanuts", "shellfish"]),
        cuisine_preferences=json.dumps(["Italian", "Mexican"]),
        disliked_ingredients=json.dumps(["cilantro"])
    )
    db_session.add(preference)
    db_session.commit()
    return preference


def get_test_recipes():
    """Helper function to get test recipe data"""
    return [
        {
            "id": 1,
            "name": "Avocado Toast",
            "ingredients": [
                {"name": "bread", "amount": 2, "unit": "slices"},
                {"name": "avocado", "amount": 1, "unit": ""},
                {"name": "salt", "amount": 0.25, "unit": "tsp"},
                {"name": "pepper", "amount": 0.25, "unit": "tsp"}
            ],
            "instructions": ["Toast bread", "Mash avocado", "Spread on toast", "Season with salt and pepper"],
            "cuisine_type": "American"
        },
        {
            "id": 2,
            "name": "Vegetarian Pasta",
            "ingredients": [
                {"name": "pasta", "amount": 8, "unit": "oz"},
                {"name": "tomato sauce", "amount": 1, "unit": "cup"},
                {"name": "olive oil", "amount": 1, "unit": "tbsp"},
                {"name": "basil", "amount": 2, "unit": "tbsp"}
            ],
            "instructions": ["Cook pasta", "Heat sauce", "Mix together", "Top with basil"],
            "cuisine_type": "Italian"
        }
    ]


def get_test_retrieved_recipes():
    """Helper function to get test retrieved recipe data"""
    return [
        {
            "recipe_id": 1,
            "recipe_name": "Avocado Toast",
            "ingredients": "bread, avocado, salt, pepper",
            "cuisine_type": "American",
            "similarity_score": 0.95
        },
        {
            "recipe_id": 2,
            "recipe_name": "Vegetarian Pasta",
            "ingredients": "pasta, tomato sauce, olive oil, basil",
            "cuisine_type": "Italian",
            "similarity_score": 0.87
        }
    ]


def get_test_meal_plan():
    """Helper function to get a test meal plan response"""
    return {
        "meal_plan": [
            {
                "day": 1,
                "meals": [
                    {
                        "meal_type": "breakfast",
                        "recipe_id": 1,
                        "recipe_name": "Avocado Toast"
                    },
                    {
                        "meal_type": "lunch",
                        "recipe_id": 2,
                        "recipe_name": "Vegetarian Pasta"
                    },
                    {
                        "meal_type": "dinner",
                        "recipe_id": 1,
                        "recipe_name": "Avocado Toast"
                    }
                ]
            }
        ],
        "explanation": "This meal plan provides a balanced vegetarian diet."
    }


def get_test_grocery_list():
    """Helper function to get a test grocery list response"""
    return {
        "grocery_list": [
            {
                "category": "Produce",
                "items": [
                    {
                        "name": "Avocado",
                        "amount": "1"
                    },
                    {
                        "name": "Basil",
                        "amount": "2 tbsp"
                    }
                ]
            },
            {
                "category": "Grains",
                "items": [
                    {
                        "name": "Bread",
                        "amount": "2 slices"
                    },
                    {
                        "name": "Pasta",
                        "amount": "8 oz"
                    }
                ]
            }
        ]
    }