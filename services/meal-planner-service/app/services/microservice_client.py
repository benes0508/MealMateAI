import httpx
import os
from typing import Dict, List, Any, Optional
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MicroserviceClient:
    """Client for communicating with other microservices"""

    def __init__(self):
        # Get service URLs from environment variables or use default
        self.recipe_service_url = os.getenv("RECIPE_SERVICE_URL", "http://recipe-service:8001")
        self.user_service_url = os.getenv("USER_SERVICE_URL", "http://user-service:8000")
        self.timeout = 10.0  # seconds

    async def get_recipes(self) -> List[Dict[str, Any]]:
        """
        Get all recipes from the recipe-service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.recipe_service_url}/")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while getting recipes: {e}")
            return []

    async def get_recipe(self, recipe_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a specific recipe from the recipe-service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.recipe_service_url}/{recipe_id}")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while getting recipe {recipe_id}: {e}")
            return None

    async def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user preferences from the user-service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.user_service_url}/api/users/{user_id}/preferences")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while getting preferences for user {user_id}: {e}")
            return None

    async def get_user_allergies(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user allergies from the user-service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.user_service_url}/api/users/{user_id}/allergies")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while getting allergies for user {user_id}: {e}")
            return None

    async def get_user_diet_restrictions(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user dietary restrictions from the user-service
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.user_service_url}/api/users/{user_id}/dietary-restrictions")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while getting dietary restrictions for user {user_id}: {e}")
            return None

    async def search_recipes(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search recipes using the recipe-service vector search
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.recipe_service_url}/search",
                    params={"query": query, "limit": limit}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("recipes", [])
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while searching recipes with query '{query}': {e}")
            return []