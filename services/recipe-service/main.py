"""
MealMateAI Recipe Service - Main FastAPI Application

This is the main entry point for the Recipe Service, a sophisticated AI-powered 
microservice that provides semantic recipe search and AI-driven meal recommendations.

ARCHITECTURE OVERVIEW:
=====================
This service implements a modern RAG (Retrieval-Augmented Generation) architecture:

1. **Vector Search Layer**: Uses Qdrant vector database with 9,366 recipe embeddings
   - 8 specialized collections (desserts-sweets, protein-mains, etc.)
   - 768-dimensional embeddings from SentenceTransformer all-mpnet-base-v2
   - Cosine similarity search for semantic matching

2. **AI Integration Layer**: Google Gemini LLM for intelligent processing
   - Conversation analysis for user preference extraction
   - Smart query generation for each recipe collection
   - Context-aware recommendation generation

3. **API Layer**: RESTful FastAPI endpoints
   - /search - Direct semantic search across collections
   - /recommendations - AI-powered meal suggestions with conversation analysis
   - /collections - Collection management and information
   - /recipes/{id} - Detailed recipe information

KEY FEATURES:
=============
- **Semantic Recipe Search**: Natural language queries like "chocolate cake" or "healthy dinner"
- **AI Conversation Analysis**: Understands user preferences from chat history
- **Multi-Collection Search**: Searches across 8 specialized recipe categories
- **Real-time Processing**: Sub-second search with quality similarity scores
- **Rich Metadata**: Recipe summaries, ingredients, instructions, confidence scores

TECHNICAL STACK:
================
- FastAPI: Modern Python web framework with automatic OpenAPI documentation
- Qdrant: Specialized vector database for AI applications
- SentenceTransformers: State-of-the-art text embedding models
- Google Gemini: Large Language Model for natural language processing
- Pydantic: Data validation and serialization
- Async/Await: Non-blocking I/O for high performance

USAGE:
======
Run locally: python main.py
Run with Docker: docker-compose up recipe-service
API Documentation: http://localhost:8001/docs

DEPENDENCIES:
=============
- Vector Database: Qdrant running on port 6333
- LLM Service: Google Gemini API with valid API key
- Python 3.9+ with requirements from requirements.txt

AUTHORS: MealMateAI Development Team
VERSION: 2.0.0 (AI-Powered with Vector Search)
"""

import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Add current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup centralized logging system
from logging_config import setup_logging, log_system_info
logger = setup_logging("recipe-service-api", level="INFO")

# Import Pydantic models for request/response validation
from models import (
    RecommendationRequest, RecommendationResponse,
    SearchRequest, SearchResponse, CollectionSearchRequest,
    CollectionsResponse, CollectionInfo, RecipeDetail, ErrorResponse
)

# Import main service orchestrator
from services.recommendation_service import RecommendationService

# Global service instance - shared across all API requests
# This prevents reinitialization on every request and maintains AI model state
recommendation_service = None

# PostgreSQL configuration
# Support both DATABASE_URL (Docker) and individual params (local dev)
DATABASE_URL = os.getenv('DATABASE_URL')

if DATABASE_URL:
    # Parse DATABASE_URL for Docker environment
    # Format: postgresql://user:password@host:port/database
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
    if match:
        DB_CONFIG = {
            'user': match.group(1),
            'password': match.group(2),
            'host': match.group(3),
            'port': match.group(4),
            'database': match.group(5)
        }
    else:
        # Fallback if parsing fails
        DB_CONFIG = {
            'host': 'postgres',
            'port': '5432',
            'database': 'recipe_db',
            'user': 'recipe_user',
            'password': 'recipe_password'
        }
else:
    # Local development configuration
    DB_CONFIG = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '15432'),
        'database': os.getenv('DB_NAME', 'recipe_db'),
        'user': os.getenv('DB_USER', 'recipe_user'),
        'password': os.getenv('DB_PASSWORD', 'recipe_password')
    }

def get_db_connection():
    """Get PostgreSQL connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Manager - Handles service startup and shutdown
    
    This function manages the complete lifecycle of the Recipe Service:
    1. Initializes the AI/ML components (vector database, LLM connections)
    2. Loads recipe embeddings and classification data
    3. Establishes connections to external services (Qdrant, Google Gemini)
    4. Provides graceful shutdown handling
    
    INITIALIZATION PROCESS:
    =======================
    1. RecommendationService orchestrator creation
    2. VectorSearchService initialization (connects to Qdrant)
    3. QueryGenerationService setup (connects to Google Gemini)
    4. Recipe classification data loading
    5. SentenceTransformer model loading (768-dim embeddings)
    
    FAILURE HANDLING:
    =================
    - 30-second timeout prevents hanging on initialization
    - Falls back to "basic mode" if AI components fail
    - Service remains available for health checks and basic operations
    - All failures are logged with detailed error information
    
    PERFORMANCE NOTES:
    ==================
    - First startup takes 30-60 seconds (model downloads)
    - Subsequent startups are faster due to model caching
    - Model weights cached in Docker volumes for production
    """
    global recommendation_service
    
    # === STARTUP PHASE ===
    logger.info("🚀 Starting MealMateAI Recipe Service with Vector Search...")
    print("🚀 Starting MealMateAI Recipe Service with Vector Search...")
    
    # Log system information for debugging
    log_system_info(logger)
    
    try:
        import asyncio
        
        # Create the main service orchestrator
        recommendation_service = RecommendationService()
        
        # Initialize with timeout to prevent Docker hanging
        logger.info("⏳ Initializing AI components (Vector DB + LLM) with 30 second timeout...")
        success = await asyncio.wait_for(
            recommendation_service.initialize(), 
            timeout=30.0
        )
        
        if success:
            # Full AI functionality available
            logger.info("✅ Recipe Service initialized successfully")
            logger.info("🔍 Vector search with 8 collections ready")
            logger.info("🤖 Gemini query generation enabled")
            print("✅ Recipe Service initialized successfully")
            print("🔍 Vector search with 8 collections ready") 
            print("🤖 Gemini query generation enabled")
        else:
            # Partial functionality - basic endpoints only
            logger.warning("⚠️  Recipe Service initialized with limited functionality")
            print("⚠️  Recipe Service initialized with limited functionality")
            
    except asyncio.TimeoutError:
        # Timeout during initialization - common on first run due to model downloads
        logger.error("⏰ Service initialization timed out (30s)")
        logger.warning("🔧 Service will run in basic mode (health checks only)")
        print("⏰ Service initialization timed out (30s)")
        print("🔧 Service will run in basic mode (health checks only)")
        recommendation_service = RecommendationService()  # Create basic instance
    except Exception as e:
        # Any other initialization error
        logger.error(f"❌ Failed to initialize Recipe Service: {e}")
        logger.warning("🔧 Service will run in basic mode (health checks only)")
        print(f"❌ Failed to initialize Recipe Service: {e}")
        print("🔧 Service will run in basic mode (health checks only)")
        recommendation_service = RecommendationService()  # Create basic instance
    
    yield
    
    # === SHUTDOWN PHASE ===
    logger.info("🛑 Shutting down Recipe Service...")
    print("🛑 Shutting down Recipe Service...")
    # Note: Cleanup of AI models and connections happens automatically
    # when the service process terminates

# === FASTAPI APPLICATION SETUP ===

# Create FastAPI application with comprehensive configuration
app = FastAPI(
    title="MealMateAI Recipe Service",
    description="""
    AI-Powered Recipe Recommendation Service
    
    This service provides intelligent recipe search and meal recommendations using:
    - Vector-based semantic search across 9,366 recipes
    - 8 specialized recipe collections (desserts, proteins, etc.)
    - Google Gemini LLM for conversation analysis
    - Real-time recommendation generation with RAG architecture
    
    Key Endpoints:
    - /search: Direct semantic recipe search
    - /recommendations: AI-powered meal suggestions
    - /collections: Browse recipe categories
    """,
    version="2.0.0",
    lifespan=lifespan,
    # Automatic OpenAPI documentation available at /docs
    docs_url="/docs",
    redoc_url="/redoc"
)

# === MIDDLEWARE CONFIGURATION ===

# CORS (Cross-Origin Resource Sharing) - allows frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure specific origins for production security
    allow_credentials=True,
    allow_methods=["*"],   # Allow all HTTP methods
    allow_headers=["*"],   # Allow all headers
)

# === STATIC FILES ===
# Mount the images directory to serve recipe images
from pathlib import Path
images_path = Path("NewDataset13k/Food Images/Food Images")
if images_path.exists():
    app.mount("/images", StaticFiles(directory=str(images_path)), name="images")
    logger.info(f"✅ Mounted images directory at /images")

# === DEPENDENCY INJECTION ===

async def get_recommendation_service():
    """
    Dependency injection for RecommendationService
    
    This ensures that:
    1. Service is properly initialized before handling requests
    2. Same service instance is shared across requests (maintains AI model state)
    3. Proper error handling if service fails to initialize
    
    Returns:
        RecommendationService: Initialized service instance
        
    Raises:
        HTTPException: 503 Service Unavailable if service not initialized
    """
    if recommendation_service is None:
        logger.error("Service not initialized when requested")
        raise HTTPException(
            status_code=503, 
            detail="Service not initialized - AI components may be loading"
        )
    return recommendation_service

# ===========================
# API ENDPOINTS DOCUMENTATION
# ===========================

@app.get("/health")
async def health_check(service: RecommendationService = Depends(get_recommendation_service)):
    """
    Health Check Endpoint
    
    PURPOSE:
    ========
    Provides comprehensive system health status including:
    - Service availability and version
    - AI component status (Vector DB, LLM)
    - Performance metrics
    - System resource information
    
    USAGE:
    ======
    GET /health
    
    RESPONSE:
    =========
    {
        "status": "ok" | "degraded" | "down",
        "service": "recipe-service",
        "version": "2.0.0",
        "details": {
            "recommendation_service": "healthy",
            "vector_search_service": "healthy" | "unhealthy",
            "query_generation_service": "healthy" | "unavailable",
            "timestamp": "2025-08-20T20:16:09.354378"
        }
    }
    """
    try:
        health_status = await service.health_check()
        logger.debug("Health check completed successfully")
        return {
            "status": "ok",
            "service": "recipe-service",
            "version": "2.0.0",
            "details": health_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "service": "recipe-service", 
            "version": "2.0.0",
            "error": str(e)
        }

@app.post("/recommendations", response_model=RecommendationResponse)
async def get_recommendations(
    request: RecommendationRequest,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    AI-Powered Recipe Recommendations (RAG Architecture)
    
    PURPOSE:
    ========
    This is the flagship endpoint that provides intelligent meal recommendations
    using advanced RAG (Retrieval-Augmented Generation) architecture.
    
    PROCESS FLOW:
    =============
    1. **Conversation Analysis**: Uses Google Gemini LLM to analyze chat history
       - Extracts user preferences (sweet, spicy, healthy, etc.)
       - Identifies dietary restrictions (vegan, gluten-free, etc.)
       - Determines meal context (breakfast, lunch, dinner, snack)
    
    2. **Smart Query Generation**: AI generates targeted queries for each collection
       - desserts-sweets: "chocolate desserts", "sweet treats"
       - protein-mains: "grilled chicken", "seafood dishes"  
       - quick-light: "quick healthy meals", "light lunch"
       - etc. (8 collections total)
    
    3. **Vector Search**: Performs semantic search across all relevant collections
       - 768-dimensional embeddings with cosine similarity
       - Finds recipes matching user intent, not just keywords
       - Returns top matches with similarity scores
    
    4. **Result Assembly**: Combines and ranks results from all collections
       - Applies user preference filtering
       - Removes duplicates and low-quality matches
       - Returns structured recommendations with metadata
    
    REQUEST FORMAT:
    ===============
    {
        "conversation_history": [
            {"role": "user", "content": "I want something sweet for dessert"},
            {"role": "assistant", "content": "What type of dessert?"},
            {"role": "user", "content": "Something with chocolate"}
        ],
        "max_results": 5,
        "user_preferences": {  // Optional
            "dietary_restrictions": ["vegetarian"],
            "allergies": ["nuts"],
            "cuisine_preferences": ["italian", "mexican"]
        }
    }
    
    RESPONSE FORMAT:
    ================
    {
        "recommendations": [
            {
                "recipe_id": "8225",
                "title": "Chocolate Cake",
                "collection": "desserts-sweets",
                "similarity_score": 0.677,
                "summary": "A classic moist chocolate cake...",
                "ingredients_preview": ["chocolate", "butter", "sugar"],
                "confidence": 17.0,
                "metadata": {...}
            }
        ],
        "query_analysis": {
            "detected_preferences": ["sweet", "chocolate"],
            "detected_restrictions": [],
            "meal_context": "dessert",
            "generated_queries": {...},
            "processing_time_ms": 14908
        },
        "total_results": 3,
        "status": "success"
    }
    
    PERFORMANCE:
    ============
    - Processing time: 10-20 seconds (includes LLM analysis)
    - Quality: High-relevance matches with 0.6+ similarity scores
    - Scalability: Handles complex multi-turn conversations
    """
    try:
        logger.info(f"Recommendations request: {len(request.conversation_history)} messages, max_results={request.max_results}")
        result = await service.get_recommendations(request)
        logger.info(f"Recommendations returned: {result.total_results} results")
        return result
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def direct_search(
    request: SearchRequest,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Direct Semantic Search (Fast Vector Search)
    
    PURPOSE:
    ========
    Performs direct semantic search without AI conversation analysis.
    Ideal for:
    - Quick recipe lookups
    - Testing vector search quality
    - Simple search interfaces
    - API integrations requiring fast response times
    
    TECHNICAL DETAILS:
    ==================
    1. **Query Processing**: Converts natural language to 768-dimensional vector
    2. **Vector Search**: Searches across specified collections (or all if none specified)
    3. **Similarity Matching**: Uses cosine similarity to find closest recipes
    4. **Result Ranking**: Returns results sorted by similarity score
    
    REQUEST FORMAT:
    ===============
    {
        "query": "chocolate cake",
        "max_results": 10,
        "collections": ["desserts-sweets", "baked-breads"]  // Optional
    }
    
    RESPONSE FORMAT:
    ================
    {
        "results": [
            {
                "recipe_id": "8225",
                "title": "Chocolate Cake", 
                "collection": "desserts-sweets",
                "similarity_score": 0.677,
                "summary": "A classic moist chocolate cake...",
                "ingredients_preview": ["chocolate", "butter"],
                "instructions_preview": "Preheat oven to 350°F...",
                "confidence": 17.0
            }
        ],
        "query": "chocolate cake",
        "collections_searched": ["desserts-sweets", "baked-breads"],
        "total_results": 3,
        "processing_time_ms": 641
    }
    
    PERFORMANCE:
    ============
    - Processing time: 100-800ms (depending on collection size)
    - Quality: 0.5+ similarity scores for good matches
    - Scalability: Sub-second response for most queries
    """
    try:
        import time
        start_time = time.time()
        
        logger.info(f"Direct search request: '{request.query}', collections={request.collections}, max_results={request.max_results}")
        
        recommendations = await service.direct_search(
            query=request.query,
            collections=request.collections,
            max_results=request.max_results
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        collections_searched = request.collections if request.collections else list(recommendation_service.vector_service.classified_recipes.keys()) if recommendation_service.vector_service.classified_recipes else []
        
        logger.info(f"Direct search completed: {len(recommendations)} results in {processing_time}ms")
        
        return SearchResponse(
            results=recommendations,
            query=request.query,
            collections_searched=collections_searched,
            total_results=len(recommendations),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing search: {str(e)}")

@app.post("/collections/{collection_name}/search", response_model=SearchResponse)
async def search_collection(
    collection_name: str,
    request: CollectionSearchRequest,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Search within a specific recipe collection
    """
    try:
        import time
        start_time = time.time()
        
        recommendations = await service.search_collection(
            collection_name=collection_name,
            query=request.query,
            max_results=request.max_results
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            results=recommendations,
            query=request.query,
            collections_searched=[collection_name],
            total_results=len(recommendations),
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching collection {collection_name}: {str(e)}")

@app.get("/collections", response_model=CollectionsResponse)
async def get_collections(
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get information about all available recipe collections
    """
    try:
        collections_info = await service.get_collections_info()
        
        total_recipes = sum(info.recipe_count for info in collections_info)
        
        return CollectionsResponse(
            collections=collections_info,
            total_collections=len(collections_info),
            total_recipes=total_recipes
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collections: {str(e)}")

@app.get("/collections/{collection_name}/info", response_model=CollectionInfo)
async def get_collection_info(
    collection_name: str,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get detailed information about a specific collection
    """
    try:
        collection_info = await service.get_collection_info(collection_name)
        
        if not collection_info:
            raise HTTPException(status_code=404, detail=f"Collection {collection_name} not found")
        
        return collection_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting collection info: {str(e)}")

@app.get("/recipes/{recipe_id}")
async def get_recipe_details(
    recipe_id: str,
    service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get detailed information about a specific recipe
    Returns in frontend-compatible format
    """
    try:
        recipe_details = await service.get_recipe_details(recipe_id)
        
        if not recipe_details:
            raise HTTPException(status_code=404, detail=f"Recipe {recipe_id} not found")
        
        # Convert RecipeDetail object to frontend format
        # Access attributes properly from the Pydantic model
        frontend_recipe = {
            "id": recipe_details.recipe_id,
            "name": recipe_details.title,
            "description": recipe_details.summary or "No description available",
            "imageUrl": None,
            "prepTime": 30,
            "cookTime": 45,
            "servings": 4,
            "difficulty": "medium",
            "ingredients": recipe_details.ingredients or [],
            "instructions": recipe_details.instructions.split('\n') if recipe_details.instructions else [],
            "tags": [recipe_details.collection] if recipe_details.collection else [],
            "nutritionalInfo": {
                "calories": 0,
                "protein": 0,
                "carbs": 0,
                "fat": 0
            },
            "dietaryInfo": {
                "vegetarian": True,
                "vegan": False,
                "glutenFree": False,
                "dairyFree": False,
                "nutFree": True,
                "lowCarb": False
            },
            "createdAt": "2025-01-01T00:00:00Z",
            "updatedAt": "2025-01-01T00:00:00Z"
        }
        
        return frontend_recipe
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recipe details: {str(e)}")

# === LEGACY ENDPOINTS (for frontend compatibility) ===

@app.get("/")
async def get_all_recipes(
    page: int = 1,
    limit: int = 12
):
    """
    Legacy endpoint - Get all recipes from PostgreSQL for frontend compatibility
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM recipes")
        total_count = cursor.fetchone()['total']
        
        # Get paginated recipes
        cursor.execute("""
            SELECT id, name, ingredients, meal_type, dietary_tags, allergens,
                   difficulty, cuisine, tags, directions, img_src, 
                   prep_time, cook_time, servings, rating, nutrition, url,
                   created_at, updated_at
            FROM recipes
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        recipes = cursor.fetchall()
        
        # Convert to frontend format
        formatted_recipes = []
        for recipe in recipes:
            formatted_recipe = {
                "id": recipe['id'],
                "name": recipe['name'],
                "ingredients": recipe['ingredients'] if recipe['ingredients'] else [],
                "meal_type": recipe['meal_type'] if recipe['meal_type'] else [],
                "dietary_tags": recipe['dietary_tags'] if recipe['dietary_tags'] else [],
                "allergens": recipe['allergens'] if recipe['allergens'] else [],
                "difficulty": recipe['difficulty'],
                "cuisine": recipe['cuisine'] if recipe['cuisine'] else [],
                "tags": recipe['tags'] if recipe['tags'] else [],
                "directions": recipe['directions'],
                "img_src": recipe['img_src'],
                "prep_time": recipe['prep_time'],
                "cook_time": recipe['cook_time'],
                "servings": recipe['servings'],
                "rating": recipe['rating'],
                "nutrition": recipe['nutrition'],
                "url": recipe['url'],
                "created_at": recipe['created_at'].isoformat() if recipe['created_at'] else None,
                "updated_at": recipe['updated_at'].isoformat() if recipe['updated_at'] else None
            }
            formatted_recipes.append(formatted_recipe)
        
        total_pages = max(1, (total_count + limit - 1) // limit)
        
        return {
            "recipes": formatted_recipes,
            "total": total_count,
            "page": page,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error in get_all_recipes: {e}")
        return {
            "recipes": [],
            "total": 0,
            "page": page,
            "total_pages": 1
        }
    finally:
        cursor.close()
        conn.close()

@app.get("/search")
async def search_recipes_legacy(
    query: str = "",
    dietary: str = "",
    tags: str = "",
    page: int = 1,
    limit: int = 12,
    request: Request = None
):
    """
    Legacy search endpoint - searches PostgreSQL
    Handles both array parameters (dietary[]=value) and comma-separated strings
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Handle array parameters from query string
        query_params = request.query_params if request else {}
        
        # Process dietary filters - handle both array and string formats
        dietary_list = []
        if 'dietary[]' in query_params:
            # Handle array format from frontend (dietary[]=vegetarian&dietary[]=vegan)
            dietary_list = query_params.getlist('dietary[]')
        elif dietary:
            # Handle comma-separated string format
            dietary_list = [d.strip() for d in dietary.split(",") if d.strip()]
        
        # Process tags - handle both array and string formats
        tags_list = []
        if 'tags[]' in query_params:
            # Handle array format from frontend
            tags_list = query_params.getlist('tags[]')
        elif tags:
            # Handle comma-separated string format
            tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Build WHERE clause
        where_conditions = []
        params = []
        
        if query:
            where_conditions.append("(name ILIKE %s OR directions ILIKE %s)")
            params.extend([f'%{query}%', f'%{query}%'])
        
        if dietary_list:
            dietary_placeholders = ','.join(['%s'] * len(dietary_list))
            where_conditions.append(f"dietary_tags && ARRAY[{dietary_placeholders}]")
            params.extend(dietary_list)
        
        if tags_list:
            tags_placeholders = ','.join(['%s'] * len(tags_list))
            where_conditions.append(f"tags && ARRAY[{tags_placeholders}]")
            params.extend(tags_list)
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM recipes {where_clause}"
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()['total']
        
        # Get paginated recipes
        search_query = f"""
            SELECT id, name, ingredients, meal_type, dietary_tags, allergens,
                   difficulty, cuisine, tags, directions, img_src,
                   prep_time, cook_time, servings, rating, nutrition, url,
                   created_at, updated_at
            FROM recipes
            {where_clause}
            ORDER BY id
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        cursor.execute(search_query, params)
        
        recipes = cursor.fetchall()
        
        # Convert to frontend format
        formatted_recipes = []
        for recipe in recipes:
            formatted_recipe = {
                "id": recipe['id'],
                "name": recipe['name'],
                "ingredients": recipe['ingredients'] if recipe['ingredients'] else [],
                "meal_type": recipe['meal_type'] if recipe['meal_type'] else [],
                "dietary_tags": recipe['dietary_tags'] if recipe['dietary_tags'] else [],
                "allergens": recipe['allergens'] if recipe['allergens'] else [],
                "difficulty": recipe['difficulty'],
                "cuisine": recipe['cuisine'] if recipe['cuisine'] else [],
                "tags": recipe['tags'] if recipe['tags'] else [],
                "directions": recipe['directions'],
                "img_src": recipe['img_src'],
                "prep_time": recipe['prep_time'],
                "cook_time": recipe['cook_time'],
                "servings": recipe['servings'],
                "rating": recipe['rating'],
                "nutrition": recipe['nutrition'],
                "url": recipe['url'],
                "created_at": recipe['created_at'].isoformat() if recipe['created_at'] else None,
                "updated_at": recipe['updated_at'].isoformat() if recipe['updated_at'] else None
            }
            formatted_recipes.append(formatted_recipe)
        
        total_pages = max(1, (total_count + limit - 1) // limit)
        
        return {
            "recipes": formatted_recipes,
            "total": total_count,
            "page": page,
            "total_pages": total_pages
        }
        
    except Exception as e:
        logger.error(f"Error in search endpoint: {e}")
        return {
            "recipes": [],
            "total": 0,
            "page": page,
            "total_pages": 1
        }
    finally:
        cursor.close()
        conn.close()

@app.get("/csv")
async def get_csv_recipes():
    """
    Legacy CSV endpoint - returns recipes in CSV format from PostgreSQL
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get first 100 recipes for CSV format
        cursor.execute("""
            SELECT id, name, ingredients, directions, img_src,
                   prep_time, cook_time, servings, tags
            FROM recipes
            ORDER BY id
            LIMIT 100
        """)
        
        recipes = cursor.fetchall()
        
        # Convert to CSV format expected by frontend
        csv_recipes = []
        for recipe in recipes:
            csv_recipe = {
                "Unnamed_0": str(recipe['id']),
                "recipe_name": recipe['name'],
                "ingredients": ", ".join(recipe['ingredients']) if recipe['ingredients'] else "",
                "directions": recipe['directions'] if recipe['directions'] else "",
                "img_src": recipe['img_src'],
                "prep_time": recipe['prep_time'],
                "cook_time": recipe['cook_time'],
                "servings": recipe['servings'],
                "cuisine_path": "/".join(recipe['tags']) if recipe['tags'] else ""
            }
            csv_recipes.append(csv_recipe)
        
        return {
            "recipes": csv_recipes,
            "total": len(csv_recipes)
        }
        
    except Exception as e:
        logger.error(f"Error in CSV endpoint: {e}")
        return {
            "recipes": [],
            "total": 0
        }
    finally:
        cursor.close()
        conn.close()

# Removed problematic catch-all route /{recipe_id} that was intercepting /collections and other routes
# Legacy recipe access is now only available through /recipes/{recipe_id}

# === ERROR HANDLERS ===

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return ErrorResponse(
        error="Resource not found",
        error_code="NOT_FOUND",
        details={"path": str(request.url.path)},
        status="error"
    ).model_dump()

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    return ErrorResponse(
        error="Internal server error",
        error_code="INTERNAL_ERROR", 
        details={"path": str(request.url.path)},
        status="error"
    ).model_dump()

# === STARTUP ===

if __name__ == "__main__":
    # For development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )