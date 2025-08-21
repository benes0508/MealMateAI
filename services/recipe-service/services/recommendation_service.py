"""
MealMateAI Recommendation Service - RAG Architecture Orchestrator

This is the main orchestration service that implements the complete RAG 
(Retrieval-Augmented Generation) workflow for intelligent recipe recommendations.

ARCHITECTURE OVERVIEW:
=====================
This service acts as the central coordinator between:

1. **Query Generation Service**: Uses Google Gemini LLM for conversation analysis
2. **Vector Search Service**: Performs semantic search in Qdrant vector database  
3. **Data Processing**: Combines results and applies user preference filtering

RAG WORKFLOW IMPLEMENTATION:
============================

STEP 1 - CONVERSATION ANALYSIS:
- Receives user conversation history
- Extracts preferences (sweet, spicy, healthy, etc.)
- Identifies dietary restrictions (vegan, gluten-free, etc.)
- Determines meal context (breakfast, lunch, dinner, snack)

STEP 2 - SMART QUERY GENERATION:
- Generates targeted search queries for each recipe collection
- Examples:
  * desserts-sweets: ["chocolate desserts", "sweet treats"]
  * protein-mains: ["grilled chicken", "seafood dishes"] 
  * quick-light: ["healthy quick meals", "light lunch"]

STEP 3 - VECTOR RETRIEVAL:
- Performs semantic search across 8 specialized collections
- Uses 768-dimensional embeddings with cosine similarity
- Retrieves top matches from each collection

STEP 4 - RESULT AUGMENTATION:
- Combines results from all collections
- Applies user preference filtering
- Removes duplicates and low-quality matches
- Ranks by relevance and user preferences

STEP 5 - RESPONSE GENERATION:
- Assembles final recommendations with metadata
- Provides similarity scores and confidence ratings
- Returns structured response with query analysis

PERFORMANCE CHARACTERISTICS:
===========================
- **Latency**: 10-20 seconds for full RAG workflow
- **Quality**: High-relevance matches with 0.6+ similarity scores
- **Scalability**: Handles complex multi-turn conversations
- **Reliability**: Graceful fallback if AI components fail

SERVICE DEPENDENCIES:
====================
- VectorSearchService: Qdrant vector database operations
- QueryGenerationService: Google Gemini LLM integration
- Recipe Classification Data: 9,366 classified recipes
- SentenceTransformer Model: all-mpnet-base-v2 for embeddings

AUTHORS: MealMateAI Development Team
VERSION: 2.0.0 (RAG-Enhanced)
"""

import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from models import (
    ConversationMessage, RecommendationRequest, RecommendationResponse,
    RecipeRecommendation, QueryAnalysis, CollectionInfo, RecipeDetail
)
from services.vector_search_service import VectorSearchService
from services.query_generation_service import QueryGenerationService

class RecommendationService:
    """
    Main RAG Orchestrator Service
    
    This service coordinates the complete RAG (Retrieval-Augmented Generation) 
    workflow for intelligent recipe recommendations. It manages the interaction
    between AI services and provides the main API interface.
    
    KEY RESPONSIBILITIES:
    ====================
    1. Service Initialization: Sets up AI components and connections
    2. RAG Workflow: Orchestrates conversation analysis → query generation → vector search
    3. Result Processing: Combines and filters results from multiple sources
    4. Error Handling: Provides graceful fallbacks and error recovery
    5. Health Monitoring: Tracks service status and performance metrics
    
    USAGE PATTERNS:
    ===============
    
    # Initialize service (done once at startup)
    service = RecommendationService()
    await service.initialize()
    
    # AI-powered recommendations 
    response = await service.get_recommendations(request)
    
    # Direct search (faster, no AI analysis)
    results = await service.direct_search("chocolate cake", max_results=5)
    
    # Collection management
    collections = await service.get_collections_info()
    """
    
    def __init__(self):
        self.vector_service = VectorSearchService()
        self.query_service = QueryGenerationService()
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize all sub-services"""
        if self._initialized:
            return True
        
        try:
            # Initialize vector search service
            vector_init_success = await self.vector_service.initialize()
            if not vector_init_success:
                print("Warning: Vector search service failed to initialize")
                return False
            
            self._initialized = True
            return True
            
        except Exception as e:
            print(f"Failed to initialize RecommendationService: {e}")
            return False
    
    async def get_recommendations(
        self,
        request: RecommendationRequest
    ) -> RecommendationResponse:
        """Main method to get personalized recipe recommendations"""
        start_time = time.time()
        
        if not self._initialized:
            await self.initialize()
        
        try:
            # Step 1: Analyze conversation context
            print("🔍 Analyzing conversation context...")
            context_analysis = await self.query_service.analyze_conversation_context(
                request.conversation_history
            )
            
            # Step 2: Generate targeted queries for each collection
            print("🎯 Generating collection-specific queries...")
            collection_queries = await self.query_service.generate_collection_queries(
                request.conversation_history,
                context_analysis
            )
            
            # Check if we got Gemini-generated queries or fallback queries
            self._log_query_generation_status(collection_queries)
            
            # Step 3: Filter collections if specified
            if request.collections:
                # Only search specified collections
                filtered_queries = {
                    k: v for k, v in collection_queries.items() 
                    if k in request.collections
                }
                collection_queries = filtered_queries
            
            # Step 4: Execute vector searches
            print(f"🔍 Searching {len(collection_queries)} collections...")
            recommendations = await self.vector_service.search_multiple_collections(
                collection_queries,
                results_per_query=2  # 2 results per query to get good variety
            )
            
            # Step 5: Apply additional filtering based on user preferences
            if request.user_preferences:
                recommendations = self._apply_user_preferences_filter(
                    recommendations, 
                    request.user_preferences
                )
            
            # Step 6: Limit results
            final_recommendations = recommendations[:request.max_results]
            
            # Step 7: Build response
            processing_time = int((time.time() - start_time) * 1000)
            
            # Ensure meal_context is a string, not a list
            meal_context = context_analysis.get("meal_context")
            if isinstance(meal_context, list):
                meal_context = ", ".join(meal_context) if meal_context else None
            
            query_analysis = QueryAnalysis(
                detected_preferences=context_analysis.get("detected_preferences", []),
                detected_restrictions=context_analysis.get("detected_restrictions", []),
                meal_context=meal_context,
                generated_queries=collection_queries,
                collections_searched=list(collection_queries.keys()),
                processing_time_ms=processing_time
            )
            
            return RecommendationResponse(
                recommendations=final_recommendations,
                query_analysis=query_analysis,
                total_results=len(recommendations),
                status="success"
            )
            
        except Exception as e:
            print(f"Error getting recommendations: {e}")
            processing_time = int((time.time() - start_time) * 1000)
            
            return RecommendationResponse(
                recommendations=[],
                query_analysis=QueryAnalysis(
                    detected_preferences=[],
                    detected_restrictions=[],
                    meal_context=None,
                    generated_queries={},
                    collections_searched=[],
                    processing_time_ms=processing_time
                ),
                total_results=0,
                status=f"error: {str(e)}"
            )
    
    async def direct_search(
        self,
        query: str,
        collections: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[RecipeRecommendation]:
        """Perform a direct search without query generation"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if collections:
                # Search specific collections
                all_recommendations = []
                for collection in collections:
                    recs = await self.vector_service.search_collection(
                        collection, query, limit=max_results // len(collections)
                    )
                    all_recommendations.extend(recs)
                return sorted(all_recommendations, key=lambda x: x.similarity_score, reverse=True)[:max_results]
            else:
                # Search all collections
                return await self.vector_service.search_all_collections(
                    query, limit_per_collection=2, total_limit=max_results
                )
                
        except Exception as e:
            print(f"Error in direct search: {e}")
            return []
    
    async def search_collection(
        self,
        collection_name: str,
        query: str,
        max_results: int = 5
    ) -> List[RecipeRecommendation]:
        """Search within a specific collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self.vector_service.search_collection(
                collection_name, query, limit=max_results
            )
        except Exception as e:
            print(f"Error searching collection {collection_name}: {e}")
            return []
    
    async def get_collections_info(self) -> List[CollectionInfo]:
        """Get information about all available collections"""
        if not self._initialized:
            await self.initialize()
        
        try:
            collections_data = await self.vector_service.get_all_collections_info()
            
            collection_infos = []
            for data in collections_data:
                info = CollectionInfo(
                    name=data["name"],
                    description=data["description"],
                    recipe_count=data["recipe_count"],
                    status=data["status"],
                    last_updated=datetime.now()  # Would be better to track actual updates
                )
                collection_infos.append(info)
            
            return collection_infos
            
        except Exception as e:
            print(f"Error getting collections info: {e}")
            return []
    
    async def get_collection_info(self, collection_name: str) -> Optional[CollectionInfo]:
        """Get information about a specific collection"""
        if not self._initialized:
            await self.initialize()
        
        try:
            data = await self.vector_service.get_collection_info(collection_name)
            
            return CollectionInfo(
                name=data["name"],
                description=data["description"],
                recipe_count=data["recipe_count"],
                status=data["status"],
                last_updated=datetime.now()
            )
            
        except Exception as e:
            print(f"Error getting collection info for {collection_name}: {e}")
            return None
    
    async def get_recipe_details(self, recipe_id: str) -> Optional[RecipeDetail]:
        """Get detailed information about a specific recipe"""
        if not self._initialized:
            await self.initialize()
        
        try:
            data = await self.vector_service.get_recipe_details(recipe_id)
            if not data:
                return None
            
            return RecipeDetail(
                recipe_id=data["recipe_id"],
                title=data["title"],
                collection=data["collection"],
                summary=data["summary"],
                ingredients=data["ingredients"],
                instructions=data["instructions"],
                confidence=data["confidence"],
                metadata=data["metadata"],
                created_at=datetime.now()  # Would be better to use actual creation date
            )
            
        except Exception as e:
            print(f"Error getting recipe details for {recipe_id}: {e}")
            return None
    
    def _apply_user_preferences_filter(
        self,
        recommendations: List[RecipeRecommendation],
        preferences: Dict[str, Any]
    ) -> List[RecipeRecommendation]:
        """Apply additional filtering based on user preferences"""
        filtered_recommendations = []
        
        for rec in recommendations:
            # Check dietary restrictions
            if "dietary_restrictions" in preferences:
                restrictions = preferences["dietary_restrictions"]
                if isinstance(restrictions, list):
                    # Check if recipe metadata indicates compliance with restrictions
                    # This is a simplified check - in practice, you'd want more sophisticated logic
                    metadata = rec.metadata.get("original_data", {})
                    ingredients = metadata.get("ingredients", [])
                    
                    # Simple filtering logic (would need enhancement for production)
                    skip_recipe = False
                    for restriction in restrictions:
                        if restriction.lower() == "vegan":
                            # Check for non-vegan ingredients (simplified)
                            non_vegan = ["meat", "chicken", "beef", "pork", "fish", "eggs", "dairy", "milk", "cheese"]
                            if any(ing.lower() in str(ingredients).lower() for ing in non_vegan):
                                skip_recipe = True
                                break
                    
                    if skip_recipe:
                        continue
            
            # Check cuisine preferences
            if "preferred_cuisines" in preferences:
                cuisines = preferences["preferred_cuisines"]
                if isinstance(cuisines, list) and cuisines:
                    # Boost or filter based on cuisine preferences
                    # This is simplified - in practice you'd want better cuisine detection
                    pass
            
            # Check cooking time preferences
            if "max_cooking_time" in preferences:
                max_time = preferences["max_cooking_time"]
                # Would need cooking time data in metadata to implement this
                pass
            
            filtered_recommendations.append(rec)
        
        return filtered_recommendations
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of all services"""
        status = {
            "recommendation_service": "healthy",
            "vector_search_service": "unknown",
            "query_generation_service": "unknown",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if self._initialized:
                status["vector_search_service"] = "healthy" if self.vector_service._initialized else "unhealthy"
            
            status["query_generation_service"] = "healthy" if self.query_service.is_available() else "unavailable"
            
        except Exception as e:
            status["error"] = str(e)
            status["recommendation_service"] = "unhealthy"
        
        return status
    
    def _log_query_generation_status(self, collection_queries: Dict[str, List[str]]):
        """Analyze and log whether queries were generated by Gemini or are fallbacks"""
        
        # Default fallback queries to compare against
        default_queries = {
            "baked-breads": ["fresh bread recipes", "homemade pastries"],
            "quick-light": ["quick meal ideas", "light lunch recipes"],
            "protein-mains": ["main course dishes", "protein-rich meals"],
            "comfort-cooked": ["comfort food recipes", "hearty stews"],
            "desserts-sweets": ["sweet treats", "dessert recipes"],
            "breakfast-morning": ["breakfast ideas", "morning meals"],
            "plant-based": ["vegetarian recipes", "plant-based meals"],
            "fresh-cold": ["fresh salads", "cold dishes"]
        }
        
        gemini_collections = 0
        fallback_collections = 0
        customized_collections = []
        
        for collection, queries in collection_queries.items():
            if collection in default_queries:
                default_for_collection = default_queries[collection]
                if queries == default_for_collection:
                    fallback_collections += 1
                elif any(query in ["healthy quick meals", "nutritious light dishes", "healthy salads", "fresh vegetable dishes", "sweet desserts", "indulgent treats"] for query in queries):
                    # These are keyword-customized fallback queries
                    customized_collections.append(collection)
                    fallback_collections += 1
                else:
                    # These appear to be Gemini-generated
                    gemini_collections += 1
        
        total_collections = len(collection_queries)
        
        if gemini_collections > 0:
            print(f"✅ Using Gemini-generated queries ({gemini_collections}/{total_collections} collections)")
            if fallback_collections > 0:
                print(f"⚠️ {fallback_collections} collections using fallback queries")
        else:
            print(f"⚠️ Using fallback queries for all collections ({fallback_collections}/{total_collections})")
            if customized_collections:
                print(f"🎯 Keyword-customized fallbacks for: {customized_collections}")
        
        # Log a sample of the actual queries for transparency
        print("📋 Query Generation Results:")
        for collection, queries in list(collection_queries.items())[:3]:  # Show first 3 collections
            status = "🤖 Gemini" if collection not in default_queries or queries != default_queries[collection] else "📋 Fallback"
            print(f"   {collection}: {queries} {status}")
            
            # Show comparison with default for Gemini queries
            if status == "🤖 Gemini" and collection in default_queries:
                print(f"     └─ Default would be: {default_queries[collection]}")
        
        if len(collection_queries) > 3:
            print(f"   ... and {len(collection_queries) - 3} more collections")
        
        # Calculate and log quality metrics
        print(f"📊 Query Generation Quality:")
        print(f"   • Gemini Success Rate: {(gemini_collections/total_collections)*100:.1f}% ({gemini_collections}/{total_collections})")
        if customized_collections:
            print(f"   • Keyword Customizations: {len(customized_collections)} collections")
        print(f"   • Fallback Usage: {(fallback_collections/total_collections)*100:.1f}% ({fallback_collections}/{total_collections})")