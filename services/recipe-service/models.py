"""
Pydantic Models for MealMateAI Recipe Service

This module defines all data models used for API request/response validation
and internal data structures. Uses Pydantic for automatic validation, 
serialization, and OpenAPI documentation generation.

MODEL CATEGORIES:
=================

1. **Request Models**: Validate incoming API requests
   - RecommendationRequest: AI-powered meal recommendations
   - SearchRequest: Direct semantic search
   - CollectionSearchRequest: Collection-specific search

2. **Response Models**: Structure API responses
   - RecommendationResponse: AI recommendation results with analysis
   - SearchResponse: Search results with metadata
   - CollectionsResponse: Collection information and statistics

3. **Data Models**: Internal data structures
   - RecipeRecommendation: Individual recipe with similarity score
   - QueryAnalysis: AI conversation analysis results
   - CollectionInfo: Recipe collection metadata

4. **Configuration Models**: System configuration
   - CollectionConfig: Recipe collection settings
   - AVAILABLE_COLLECTIONS: Predefined collection definitions

VALIDATION FEATURES:
====================
- **Type Safety**: Ensures correct data types at runtime
- **Field Validation**: Min/max lengths, ranges, patterns
- **Optional Fields**: Clear distinction between required/optional
- **Nested Models**: Complex data structures with validation
- **Auto Documentation**: Generates OpenAPI/Swagger docs

USAGE:
======
These models are used throughout the service for:
- API request validation (FastAPI dependency injection)
- Response serialization (automatic JSON conversion)
- Internal data passing between service layers
- Type hints for better code completion and error detection

VERSION: 2.0.0 (AI-Enhanced with Vector Search Support)
AUTHORS: MealMateAI Development Team
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# === Request Models ===

class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: str = Field(..., description="Message role: 'user', 'assistant', 'system'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[datetime] = Field(None, description="Message timestamp")

class RecommendationRequest(BaseModel):
    """Request for personalized recipe recommendations"""
    conversation_history: List[ConversationMessage] = Field(
        ..., 
        description="Recent conversation messages for context",
        min_items=1
    )
    max_results: Optional[int] = Field(10, ge=1, le=50, description="Maximum number of recommendations")
    collections: Optional[List[str]] = Field(None, description="Specific collections to search (optional)")
    user_preferences: Optional[Dict[str, Any]] = Field(None, description="Additional user preferences")

class SearchRequest(BaseModel):
    """Direct search request"""
    query: str = Field(..., min_length=1, description="Search query")
    max_results: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of results")
    collections: Optional[List[str]] = Field(None, description="Collections to search in")

class CollectionSearchRequest(BaseModel):
    """Search within a specific collection"""
    query: str = Field(..., min_length=1, description="Search query")
    max_results: Optional[int] = Field(5, ge=1, le=20, description="Maximum number of results")

# === Response Models ===

class RecipeRecommendation(BaseModel):
    """Single recipe recommendation with metadata"""
    recipe_id: str = Field(..., description="Unique recipe identifier")
    title: str = Field(..., description="Recipe title")
    collection: str = Field(..., description="Collection name")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")
    summary: str = Field(..., description="Generated recipe summary")
    ingredients_preview: List[str] = Field(default=[], description="Preview of main ingredients")
    instructions_preview: str = Field("", description="Preview of cooking instructions")
    confidence: Optional[float] = Field(None, description="Classification confidence score")
    metadata: Dict[str, Any] = Field(default={}, description="Additional recipe metadata")

class QueryAnalysis(BaseModel):
    """Analysis of user context and generated queries"""
    detected_preferences: List[str] = Field(default=[], description="Detected food preferences")
    detected_restrictions: List[str] = Field(default=[], description="Detected dietary restrictions")
    meal_context: Optional[str] = Field(None, description="Detected meal type/context")
    generated_queries: Dict[str, List[str]] = Field(default={}, description="Generated queries per collection")
    collections_searched: List[str] = Field(default=[], description="Collections that were searched")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")

class RecommendationResponse(BaseModel):
    """Response for recipe recommendations"""
    recommendations: List[RecipeRecommendation] = Field(default=[], description="Recipe recommendations")
    query_analysis: QueryAnalysis = Field(..., description="Analysis of the query process")
    total_results: int = Field(..., description="Total number of results found")
    status: str = Field("success", description="Response status")

class SearchResponse(BaseModel):
    """Response for direct search queries"""
    results: List[RecipeRecommendation] = Field(default=[], description="Search results")
    query: str = Field(..., description="Original search query")
    collections_searched: List[str] = Field(default=[], description="Collections searched")
    total_results: int = Field(..., description="Total number of results")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")

class CollectionInfo(BaseModel):
    """Information about a recipe collection"""
    name: str = Field(..., description="Collection name")
    description: str = Field(..., description="Collection description")
    recipe_count: int = Field(..., description="Number of recipes in collection")
    status: str = Field(..., description="Collection status")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")

class CollectionsResponse(BaseModel):
    """Response listing all available collections"""
    collections: List[CollectionInfo] = Field(default=[], description="Available collections")
    total_collections: int = Field(..., description="Total number of collections")
    total_recipes: int = Field(..., description="Total recipes across all collections")

class RecipeDetail(BaseModel):
    """Detailed recipe information"""
    recipe_id: str = Field(..., description="Unique recipe identifier")
    title: str = Field(..., description="Recipe title")
    collection: str = Field(..., description="Collection name")
    summary: str = Field(..., description="Recipe summary")
    ingredients: List[str] = Field(default=[], description="Full ingredients list")
    instructions: str = Field("", description="Full cooking instructions")
    confidence: Optional[float] = Field(None, description="Classification confidence")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    status: str = Field("error", description="Response status")

# === Configuration Models ===

class CollectionConfig(BaseModel):
    """Configuration for a recipe collection"""
    name: str
    description: str
    estimated_count: int
    batch_size: int = 50

# Available collections configuration
AVAILABLE_COLLECTIONS = {
    "baked-breads": CollectionConfig(
        name="baked-breads",
        description="Baking-focused dishes",
        estimated_count=885,
        batch_size=50
    ),
    "quick-light": CollectionConfig(
        name="quick-light", 
        description="Fast preparation and light meals",
        estimated_count=2476,
        batch_size=100
    ),
    "protein-mains": CollectionConfig(
        name="protein-mains",
        description="Meat, poultry, seafood main dishes",
        estimated_count=1379,
        batch_size=75
    ),
    "comfort-cooked": CollectionConfig(
        name="comfort-cooked",
        description="Slow-cooked and braised dishes",
        estimated_count=718,
        batch_size=50
    ),
    "desserts-sweets": CollectionConfig(
        name="desserts-sweets",
        description="All sweet treats and desserts",
        estimated_count=2465,
        batch_size=100
    ),
    "breakfast-morning": CollectionConfig(
        name="breakfast-morning",
        description="Morning-specific foods",
        estimated_count=415,
        batch_size=50
    ),
    "plant-based": CollectionConfig(
        name="plant-based",
        description="Vegetarian and vegan dishes",
        estimated_count=78,
        batch_size=25
    ),
    "fresh-cold": CollectionConfig(
        name="fresh-cold",
        description="Salads and raw preparations",
        estimated_count=950,
        batch_size=75
    )
}