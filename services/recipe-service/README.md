# MealMateAI Recipe Service

## Overview

The Recipe Service is an AI-powered microservice that provides intelligent recipe search and meal recommendations using advanced RAG (Retrieval-Augmented Generation) architecture. It combines vector-based semantic search with Google Gemini LLM for contextual understanding and personalized recommendations.

## Key Features

- 🔍 **Semantic Recipe Search**: Natural language queries across 9,366 recipes
- 🤖 **AI-Powered Recommendations**: Conversation-aware meal suggestions
- 📚 **Multi-Collection Architecture**: 8 specialized recipe categories
- ⚡ **Real-time Processing**: Sub-second search with quality similarity scores
- 🎯 **Intelligent Query Generation**: Context-aware search optimization

## Architecture

### Technical Stack
- **FastAPI**: Modern Python web framework with automatic OpenAPI documentation
- **Qdrant**: Specialized vector database for AI applications  
- **SentenceTransformers**: all-mpnet-base-v2 model for 768-dimensional embeddings
- **Google Gemini**: Large Language Model for natural language processing
- **Pydantic**: Data validation and serialization

### RAG Workflow
1. **Conversation Analysis**: Extract user preferences and context
2. **Smart Query Generation**: AI generates targeted queries per collection
3. **Vector Search**: Semantic similarity search across recipe embeddings  
4. **Result Assembly**: Combine, filter, and rank recommendations
5. **Response Generation**: Structured recommendations with metadata

## Recipe Collections

The service organizes recipes into 8 specialized collections for optimal search:

| Collection | Count | Description |
|------------|-------|-------------|
| **desserts-sweets** | 2,465 | Sweet treats, cakes, cookies, candies |
| **quick-light** | 2,476 | Fast prep, salads, light meals, healthy options |
| **protein-mains** | 1,379 | Meat, poultry, seafood main dishes |
| **baked-breads** | 885 | Breads, pastries, baked goods |
| **comfort-cooked** | 718 | Slow-cooked, braised, hearty comfort foods |
| **fresh-cold** | 950 | Salads, raw preparations, cold dishes |
| **breakfast-morning** | 415 | Morning-specific foods and drinks |
| **plant-based** | 78 | Vegetarian and vegan specialized dishes |

**Total**: 9,366 recipes with AI-generated summaries

## API Endpoints

### Core Endpoints

- `POST /recommendations` - AI-powered meal recommendations with conversation analysis
- `POST /search` - Direct semantic search across collections
- `POST /collections/{name}/search` - Search within specific collection
- `GET /collections` - List all available collections with statistics
- `GET /recipes/{id}` - Get detailed recipe information
- `GET /health` - Service health and status check

### Example Usage

```bash
# AI-powered recommendations
curl -X POST "http://localhost:8001/recommendations" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_history": [
      {"role": "user", "content": "I want something sweet for dessert"},
      {"role": "user", "content": "Something with chocolate would be perfect"}
    ],
    "max_results": 5
  }'

# Direct semantic search
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "chocolate cake",
    "max_results": 10,
    "collections": ["desserts-sweets", "baked-breads"]
  }'
```

## Setup and Installation

### Prerequisites
- Python 3.9+
- Qdrant vector database (Docker: `qdrant/qdrant`)
- Google Gemini API key

### Environment Variables
```bash
GOOGLE_API_KEY=your_gemini_api_key_here
QDRANT_URL=http://localhost:6333  # Default for local development
```

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize vector database (first time only)
python qdrant_loader.py

# Run the service
python main.py
```

### Docker Deployment
```bash
# Build and run with docker-compose
docker-compose up --build recipe-service
```

## File Structure

### Core Application Files
- `main.py` - FastAPI application with comprehensive API endpoints
- `models.py` - Pydantic data models for request/response validation
- `requirements.txt` - Python dependencies

### AI/ML Service Layer  
- `services/recommendation_service.py` - Main RAG orchestrator
- `services/vector_search_service.py` - Qdrant vector database interface
- `services/query_generation_service.py` - Google Gemini LLM integration

### Data Processing & Classification
- `function_based_classifier.py` - Recipe classification system (9 categories)
- `generate_missing_summaries.py` - Gemini-powered summary generation
- `qdrant_loader.py` - Vector database population script

### Dataset & Generated Content
- `NewDataset13k/` - Complete recipe dataset with 13,501 recipes
- `function_classification_results/` - Classification outputs and statistics
- `recipe_summaries/` - 9,366 AI-generated recipe summaries (organized by collection)

### Configuration & Utilities
- `logging_config.py` - Centralized logging with timestamped files
- `test_api_clean.py` - Comprehensive API testing script
- `Dockerfile` - Multi-stage container build configuration
- `init.sql` - Database initialization scripts

## Performance Characteristics

- **Embedding Generation**: ~50-200ms per query (cached model)
- **Vector Search**: ~100-500ms per collection (parallel processing)
- **AI Recommendations**: 10-20 seconds (includes LLM analysis)
- **Direct Search**: 100-800ms (depending on collection size)
- **Memory Usage**: ~2GB for model + embeddings in production

## Data Sources

The service uses the "Food Ingredients and Recipe Dataset with Image Name Mapping" containing 13,501 recipes. Each recipe includes:
- Title and ingredients list
- Step-by-step cooking instructions  
- AI-generated summary for better semantic search
- Classification confidence scores
- Collection assignment based on cooking method/meal type

## Development Workflow

### Adding New Recipes
1. Add recipes to `NewDataset13k/` directory
2. Run `function_based_classifier.py` to classify into collections
3. Generate summaries with `generate_missing_summaries.py`
4. Populate vector database with `qdrant_loader.py`

### Testing
```bash
# Run comprehensive API tests
python test_api_clean.py

# Test individual components
python -c "from services.vector_search_service import VectorSearchService; print('Import successful')"
```

### Monitoring
- Health endpoint: `GET /health` 
- Logs: `logs/recipe-service-*.log`
- Performance metrics available via structured logging

## API Documentation

Interactive API documentation available at:
- Swagger UI: `http://localhost:8001/docs`
- ReDoc: `http://localhost:8001/redoc`

## Version History

- **v2.0.0** - AI-powered architecture with RAG implementation
- **v1.0.0** - Basic CRUD operations with PostgreSQL

## Support

For issues and questions:
- Check logs in `logs/` directory
- Verify Qdrant connection and collections
- Ensure GOOGLE_API_KEY is properly configured
- Test individual components with health checks

---

**MealMateAI Development Team** | Recipe Service v2.0.0