"""
Vector Search Service for Qdrant operations
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import time

# Set environment variables before imports
os.environ['TRANSFORMERS_NO_TF'] = '1'

try:
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest
except ImportError as e:
    # Will be logged later when logger is available
    print(f"Import error: {e}")
    raise

from models import CollectionConfig, AVAILABLE_COLLECTIONS, RecipeRecommendation

class VectorSearchService:
    """
    Service for performing semantic search operations against Qdrant collections
    """
    
    def __init__(self, qdrant_url: str = None):
        # Use environment variable if available, fallback to localhost
        if qdrant_url is None:
            qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant_url = qdrant_url
        self.client = None
        self.model = None
        self.classified_recipes = None
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Qdrant client and embedding model"""
        if self._initialized:
            return True
            
        try:
            # Initialize Qdrant client
            self.client = QdrantClient(url=self.qdrant_url)
            
            # Test connection
            collections = self.client.get_collections()
            print(f"Connected to Qdrant with {len(collections.collections)} collections")
            
            # Initialize embedding model
            self.model = SentenceTransformer("all-mpnet-base-v2")
            print("Embedding model loaded successfully")
            
            # Load classified recipes metadata
            await self._load_classified_recipes()
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize VectorSearchService: {e}")
            return False
    
    async def _load_classified_recipes(self):
        """Load classified recipes metadata"""
        classification_path = Path("function_classification_results/function_classified_recipes.json")
        
        try:
            with open(classification_path, 'r', encoding='utf-8') as f:
                self.classified_recipes = json.load(f)
            print(f"Loaded metadata for {len(self.classified_recipes)} classified recipes")
        except Exception as e:
            print(f"Warning: Could not load classified recipes: {e}")
            self.classified_recipes = {}
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text query"""
        if not self.model:
            raise RuntimeError("Model not initialized")
        
        try:
            embedding = self.model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            raise RuntimeError(f"Error generating embedding: {e}")
    
    async def search_collection(
        self,
        collection_name: str,
        query: str,
        limit: int = 5
    ) -> List[RecipeRecommendation]:
        """Search within a specific collection"""
        if not self._initialized:
            await self.initialize()
        
        if collection_name not in AVAILABLE_COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Perform search
            search_results = self.client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # Convert to recommendations
            recommendations = []
            for result in search_results:
                try:
                    recommendation = self._create_recommendation(result, collection_name)
                    if recommendation:
                        recommendations.append(recommendation)
                except Exception as e:
                    print(f"Error processing search result: {e}")
                    continue
            
            return recommendations
            
        except Exception as e:
            print(f"Error searching collection {collection_name}: {e}")
            return []
    
    async def search_multiple_collections(
        self,
        queries_by_collection: Dict[str, List[str]],
        results_per_query: int = 3
    ) -> List[RecipeRecommendation]:
        """Search multiple collections with different queries"""
        if not self._initialized:
            await self.initialize()
        
        all_recommendations = []
        
        for collection_name, queries in queries_by_collection.items():
            if collection_name not in AVAILABLE_COLLECTIONS:
                print(f"Warning: Unknown collection {collection_name}, skipping")
                continue
            
            for query in queries:
                try:
                    recommendations = await self.search_collection(
                        collection_name=collection_name,
                        query=query,
                        limit=results_per_query
                    )
                    all_recommendations.extend(recommendations)
                    
                except Exception as e:
                    print(f"Error searching {collection_name} with query '{query}': {e}")
                    continue
        
        # Sort by similarity score and remove duplicates
        seen_ids = set()
        unique_recommendations = []
        
        for rec in sorted(all_recommendations, key=lambda x: x.similarity_score, reverse=True):
            if rec.recipe_id not in seen_ids:
                seen_ids.add(rec.recipe_id)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    async def search_all_collections(
        self,
        query: str,
        limit_per_collection: int = 2,
        total_limit: int = 10
    ) -> List[RecipeRecommendation]:
        """Search across all available collections"""
        queries_by_collection = {
            collection: [query] for collection in AVAILABLE_COLLECTIONS.keys()
        }
        
        recommendations = await self.search_multiple_collections(
            queries_by_collection,
            results_per_query=limit_per_collection
        )
        
        return recommendations[:total_limit]
    
    def _create_recommendation(
        self,
        search_result: Any,
        collection_name: str
    ) -> Optional[RecipeRecommendation]:
        """Convert Qdrant search result to RecipeRecommendation"""
        try:
            payload = search_result.payload
            score = float(search_result.score)
            
            # Extract basic information
            recipe_id = str(payload.get("recipe_id", ""))
            title = payload.get("title", "Unknown Recipe")
            summary = payload.get("summary", "")
            confidence = payload.get("confidence", 0)
            
            # Parse ingredients preview
            ingredients_str = payload.get("ingredients_preview", "")
            if ingredients_str:
                try:
                    # Handle both string and list formats
                    if isinstance(ingredients_str, str):
                        if ingredients_str.startswith('[') and ingredients_str.endswith(']'):
                            ingredients_preview = eval(ingredients_str)  # Safe for simple lists
                        else:
                            ingredients_preview = [ing.strip() for ing in ingredients_str.split(',')]
                    else:
                        ingredients_preview = list(ingredients_str)
                except:
                    ingredients_preview = [ingredients_str] if ingredients_str else []
            else:
                ingredients_preview = []
            
            # Get instructions preview
            instructions_preview = payload.get("instructions_preview", "")
            
            # Get additional metadata from classified recipes if available
            additional_metadata = {}
            if self.classified_recipes and recipe_id in self.classified_recipes:
                recipe_data = self.classified_recipes[recipe_id]
                additional_metadata = {
                    "original_data": {
                        "ingredients": recipe_data.get("ingredients", []),
                        "instructions": recipe_data.get("instructions", ""),
                        "title": recipe_data.get("title", title)
                    }
                }
            
            return RecipeRecommendation(
                recipe_id=recipe_id,
                title=title,
                collection=collection_name,
                similarity_score=score,
                summary=summary,
                ingredients_preview=ingredients_preview[:5],  # Limit to first 5 ingredients
                instructions_preview=instructions_preview[:200],  # Limit preview length
                confidence=confidence,
                metadata=additional_metadata
            )
            
        except Exception as e:
            print(f"Error creating recommendation from search result: {e}")
            return None
    
    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a specific collection"""
        if not self._initialized:
            await self.initialize()
        
        if collection_name not in AVAILABLE_COLLECTIONS:
            raise ValueError(f"Unknown collection: {collection_name}")
        
        try:
            # Get collection info from Qdrant
            collections_list = self.client.get_collections()
            existing_collections = [col.name for col in collections_list.collections]
            
            if collection_name not in existing_collections:
                return {
                    "name": collection_name,
                    "description": AVAILABLE_COLLECTIONS[collection_name].description,
                    "recipe_count": 0,
                    "status": "missing"
                }
            
            # Try to get approximate count using search
            try:
                dummy_vector = [0.0] * 768
                search_result = self.client.search(
                    collection_name=collection_name,
                    query_vector=dummy_vector,
                    limit=1,
                    with_payload=False,
                    with_vectors=False
                )
                status = "ready" if search_result else "empty"
            except:
                status = "ready"  # Assume ready if search works
            
            return {
                "name": collection_name,
                "description": AVAILABLE_COLLECTIONS[collection_name].description,
                "recipe_count": AVAILABLE_COLLECTIONS[collection_name].estimated_count,
                "status": status
            }
            
        except Exception as e:
            print(f"Error getting collection info for {collection_name}: {e}")
            return {
                "name": collection_name,
                "description": AVAILABLE_COLLECTIONS[collection_name].description,
                "recipe_count": 0,
                "status": f"error: {e}"
            }
    
    async def get_all_collections_info(self) -> List[Dict[str, Any]]:
        """Get information about all collections"""
        collections_info = []
        
        for collection_name in AVAILABLE_COLLECTIONS.keys():
            try:
                info = await self.get_collection_info(collection_name)
                collections_info.append(info)
            except Exception as e:
                print(f"Error getting info for collection {collection_name}: {e}")
                continue
        
        return collections_info
    
    async def get_recipe_details(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific recipe"""
        if not self.classified_recipes:
            return None
        
        if recipe_id not in self.classified_recipes:
            return None
        
        recipe_data = self.classified_recipes[recipe_id]
        
        return {
            "recipe_id": recipe_id,
            "title": recipe_data.get("title", ""),
            "collection": recipe_data.get("collection", ""),
            "summary": "",  # Would need to load from summary files
            "ingredients": recipe_data.get("ingredients", []),
            "instructions": recipe_data.get("instructions", ""),
            "confidence": recipe_data.get("confidence", 0),
            "metadata": recipe_data
        }