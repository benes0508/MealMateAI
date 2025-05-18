import pytest
from unittest.mock import AsyncMock, patch
import numpy as np
from sqlalchemy import text
from app.services.embeddings_service import EmbeddingsService


class TestEmbeddingsService:
    """Test suite for the EmbeddingsService class."""

    @pytest.fixture
    def mock_embedding_model(self):
        """Mock the GoogleGenerativeAIEmbeddings model."""
        with patch("app.services.embeddings_service.GoogleGenerativeAIEmbeddings") as mock:
            model_instance = mock.return_value
            model_instance.aembed_query = AsyncMock(return_value=[0.1] * 768)
            yield model_instance

    @pytest.fixture
    def embedding_service(self, mock_embedding_model):
        """Create an EmbeddingsService with mocked dependencies."""
        with patch("app.services.embeddings_service.genai.configure"):
            service = EmbeddingsService()
            service.embedding_model = mock_embedding_model
            return service

    @pytest.mark.asyncio
    async def test_generate_recipe_embedding(self, embedding_service):
        """Test generating an embedding vector for a recipe."""
        # Arrange
        recipe = {
            "id": 1,
            "name": "Avocado Toast",
            "ingredients": [
                {"name": "bread", "amount": 2, "unit": "slices"},
                {"name": "avocado", "amount": 1, "unit": ""}
            ],
            "cuisine_type": "American"
        }

        # Act
        embedding = await embedding_service.generate_recipe_embedding(recipe)

        # Assert
        assert embedding is not None
        assert len(embedding) == 768  # Default embedding dimension
        embedding_service.embedding_model.aembed_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_recipe_embedding(self, embedding_service, db_session):
        """Test storing an embedding for a recipe in the database."""
        # Arrange
        recipe = {
            "id": 1,
            "name": "Avocado Toast",
            "ingredients": [
                {"name": "bread", "amount": 2, "unit": "slices"},
                {"name": "avocado", "amount": 1, "unit": ""}
            ],
            "cuisine_type": "American"
        }
        
        # Mock the embedding generation to return a fixed vector
        embedding_service.generate_recipe_embedding = AsyncMock(return_value=[0.1] * 768)

        # Act
        success = await embedding_service.store_recipe_embedding(db_session, recipe)

        # Assert
        assert success is True
        embedding_service.generate_recipe_embedding.assert_called_once_with(recipe)
        
        # Check if embedding was stored in DB
        result = db_session.execute(
            text("SELECT * FROM recipe_embeddings WHERE recipe_id = :recipe_id"),
            {"recipe_id": recipe["id"]}
        ).fetchone()
        assert result is not None
        assert result.recipe_name == recipe["name"]

    @pytest.mark.asyncio
    async def test_batch_store_recipe_embeddings(self, embedding_service, db_session):
        """Test batch storing embeddings for multiple recipes."""
        # Arrange
        recipes = [
            {
                "id": 1,
                "name": "Avocado Toast",
                "ingredients": [{"name": "bread"}, {"name": "avocado"}],
                "cuisine_type": "American"
            },
            {
                "id": 2,
                "name": "Pasta",
                "ingredients": [{"name": "pasta"}, {"name": "sauce"}],
                "cuisine_type": "Italian"
            }
        ]
        
        # Mock the store_recipe_embedding method
        embedding_service.store_recipe_embedding = AsyncMock(return_value=True)

        # Act
        success = await embedding_service.batch_store_recipe_embeddings(db_session, recipes)

        # Assert
        assert success is True
        assert embedding_service.store_recipe_embedding.call_count == 2

    @pytest.mark.asyncio
    async def test_find_similar_recipes(self, embedding_service, db_session):
        """Test finding recipes similar to a query using vector similarity search."""
        # Arrange
        # Mock the database execution to return test results
        mock_results = [
            type('MockRow', (), {
                'recipe_id': 1,
                'recipe_name': 'Avocado Toast',
                'ingredients': 'bread, avocado',
                'cuisine_type': 'American',
                'similarity': 0.95
            }),
            type('MockRow', (), {
                'recipe_id': 2,
                'recipe_name': 'Vegetarian Pasta',
                'ingredients': 'pasta, sauce',
                'cuisine_type': 'Italian',
                'similarity': 0.85
            })
        ]
        
        db_session.execute = AsyncMock(return_value=mock_results)
        
        # Act
        results = await embedding_service.find_similar_recipes(db_session, "healthy breakfast")

        # Assert
        assert len(results) == 2
        assert results[0]["recipe_id"] == 1
        assert results[0]["recipe_name"] == "Avocado Toast"
        assert results[1]["recipe_id"] == 2
        embedding_service.embedding_model.aembed_query.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_recipes_for_preferences(self, embedding_service, db_session):
        """Test finding recipes matching user preferences."""
        # Arrange
        preferences = {
            "dietary_restrictions": ["vegetarian"],
            "allergies": ["peanuts"],
            "cuisine_preferences": ["Italian"],
            "disliked_ingredients": ["cilantro"]
        }
        
        # Mock find_similar_recipes to return test data
        mock_retrieved_recipes = [
            {
                "recipe_id": 1,
                "recipe_name": "Avocado Toast",
                "ingredients": "bread, avocado",
                "cuisine_type": "American",
                "similarity_score": 0.8
            },
            {
                "recipe_id": 2,
                "recipe_name": "Vegetarian Pasta",
                "ingredients": "pasta, tomato sauce, basil",
                "cuisine_type": "Italian",
                "similarity_score": 0.9
            },
            {
                "recipe_id": 3,
                "recipe_name": "Peanut Noodles",
                "ingredients": "noodles, peanuts, soy sauce",
                "cuisine_type": "Asian",
                "similarity_score": 0.7
            }
        ]
        
        embedding_service.find_similar_recipes = AsyncMock(return_value=mock_retrieved_recipes)
        
        # Act
        results = await embedding_service.find_recipes_for_preferences(db_session, preferences)
        
        # Assert
        assert len(results) == 2  # Should filter out the peanut noodles
        assert results[0]["recipe_id"] == 1
        assert results[1]["recipe_id"] == 2
        
        # Check if allergenic recipe was filtered out
        recipe_ids = [recipe["recipe_id"] for recipe in results]
        assert 3 not in recipe_ids  # Peanut Noodles should be filtered out due to allergy
        
        # Verify find_similar_recipes was called with correct parameters
        embedding_service.find_similar_recipes.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_recipes_for_preferences_empty_result(self, embedding_service, db_session):
        """Test finding recipes with preferences when no matching recipes are found."""
        # Arrange
        preferences = {
            "dietary_restrictions": ["vegan"],
            "allergies": [],
            "cuisine_preferences": [],
            "disliked_ingredients": []
        }
        
        # Mock find_similar_recipes to return empty list
        embedding_service.find_similar_recipes = AsyncMock(return_value=[])
        
        # Act
        results = await embedding_service.find_recipes_for_preferences(db_session, preferences)
        
        # Assert
        assert results == []
        embedding_service.find_similar_recipes.assert_called_once()