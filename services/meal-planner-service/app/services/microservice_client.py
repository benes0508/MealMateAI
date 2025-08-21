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
                response = await client.get(f"{self.recipe_service_url}/recipes/{recipe_id}")
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
        Search recipes using the recipe-service vector search (basic)
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

    async def get_ai_recommendations(self, conversation_history: List[Dict[str, str]], max_results: int = 20, user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get AI-powered recipe recommendations using the Recipe Service RAG system
        
        Args:
            conversation_history: List of conversation messages in format [{"role": "user", "content": "..."}]
            max_results: Maximum number of recipe recommendations to return
            user_preferences: Optional user preferences (dietary restrictions, allergies, etc.)
            
        Returns:
            Dictionary containing recommendations and analysis from the RAG system
        """
        try:
            # Prepare the request payload for the Recipe Service RAG endpoint
            request_payload = {
                "conversation_history": conversation_history,
                "max_results": max_results
            }
            
            # Add user preferences if provided
            if user_preferences:
                request_payload["user_preferences"] = user_preferences
            
            async with httpx.AsyncClient(timeout=30.0) as client:  # Longer timeout for AI processing
                response = await client.post(
                    f"{self.recipe_service_url}/recommendations",
                    json=request_payload,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while getting AI recommendations: {e}")
            return {"recommendations": [], "status": "error", "total_results": 0}
        except Exception as e:
            logger.error(f"Unexpected error during AI recommendations: {e}")
            return {"recommendations": [], "status": "error", "total_results": 0}

    async def search_recipes_by_collection(self, collection_name: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search recipes within a specific collection using Recipe Service
        
        Args:
            collection_name: Name of the recipe collection (e.g., 'desserts-sweets', 'protein-mains')
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of recipe dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.recipe_service_url}/collections/{collection_name}/search",
                    json={"query": query, "max_results": limit},
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                data = response.json()
                return data.get("results", [])
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while searching collection '{collection_name}' with query '{query}': {e}")
            return []