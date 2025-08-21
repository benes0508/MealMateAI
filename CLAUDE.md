# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Docker Operations

**🚀 Optimized Build (Recommended)**
- **Fast build with caching**: `./docker-build-optimized.sh`
- **Start optimized services**: `docker-compose up -d`

**⚡ Development Mode (Hot Reload)**
- **Dev build**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build`
- **Dev start**: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d`

**🐳 Standard Docker Operations**
- **Start all services**: `docker-compose up --build`
- **Start detached**: `docker-compose up -d --build`
- **View logs**: `docker-compose logs -f`
- **Stop services**: `docker-compose down`
- **Rebuild single service**: `docker-compose build <service-name>`

**🏎️ Build Optimizations Included**
- Multi-stage Docker builds for smaller images
- Shared pip cache across all Python services (up to 90% faster pip installs)
- HuggingFace and PyTorch model caching for recipe service
- BuildKit cache mounts for lightning-fast rebuilds
- Health checks for better container monitoring

### Frontend (React + Vite)
- **Development server**: `npm start` (from `/frontend`)
- **Build**: `npm run build` (from `/frontend`)
- **Preview build**: `npm run serve` (from `/frontend`)
- **Tests**: `npm test` (from `/frontend`)
- **Lint/Type check**: Check package.json scripts for linting commands

### API Gateway (Express.js)
- **Development**: `npm run dev` (from `/api-gateway`)
- **Production**: `npm start` (from `/api-gateway`)
- **Tests**: `npm test` (from `/api-gateway`)
- **Lint/Type check**: Check package.json scripts for linting commands

### Python Services (FastAPI)
- **Run locally**: `python run.py` or `python run_local.py` (from service directory)
- **Tests**: `pytest` (from service directory)
- **Dependencies**: Install from `requirements.txt` in each service
- **Lint/Type check**: `ruff check .` and `ruff format .` (if ruff is configured) or check individual service requirements

### Recipe Service Specific Commands
- **Classify recipes**: `python3.9 function_based_classifier.py` (from `/services/recipe-service`)
- **Generate summaries**: `python3.9 generate_missing_summaries.py` (from `/services/recipe-service`)
- **Test summary generation**: `python3.9 test_and_validate.py` (from `/services/recipe-service/test_summary_generation`)
- **Load vector database**: `python3.9 qdrant_loader.py` (from `/services/recipe-service`)
- **Test vector search**: `python3.9 test_qdrant_cli.py` (from `/services/recipe-service`)
- **Start API server**: `python3.9 main.py` (from `/services/recipe-service`)
- **Run comprehensive tests**: `python3.9 run_tests.py` (from `/services/recipe-service`)
- **Run integration tests**: `python3.9 test_integration.py` (from `/services/recipe-service`)
- **Run API tests**: `python3.9 test_simple.py` (from `/services/recipe-service`)

### Testing
- **End-to-end tests**: `python scripts/test_end_to_end.py`
- **RAG workflow test**: `./test_rag_workflow.sh`
- **Detailed RAG test**: `./test_rag_detailed.sh`
- **Individual service tests**: Run `pytest` from any `/services/<service-name>/` directory

### Performance Testing

**⚠️ WARNING**: Performance testing AI endpoints can incur significant costs! Always monitor API usage and set budget limits.

#### Quick Start (Safe Testing)
```bash
# Install dependencies
pip install locust faker python-dotenv

# Run minimal test (NO AI costs)
locust -f performance-testing/locustfile_minimal.py --host=http://localhost:3000 \
  --headless -u 5 -r 1 -t 1m --csv=performance-testing/results/minimal_test

# Run auth-only test (NO AI costs)
locust -f performance-testing/locustfile_auth_only.py --host=http://localhost:3000 \
  --headless -u 10 -r 2 -t 2m --csv=performance-testing/results/auth_test
```

#### Cost Monitoring (Required for AI Testing)
```bash
# Start cost monitor BEFORE any AI tests
python performance-testing/scripts/cost_monitor.py --watch

# Check current costs
python performance-testing/scripts/cost_monitor.py --status
```

#### AI Testing (HIGH RISK - Costs Money!)
```bash
# Set safety environment variables FIRST
export PERFORMANCE_TEST_MODE=true
export GEMINI_API_DAILY_LIMIT=50  # Your budget in dollars
export CONFIRM_AI_TESTING=yes

# Run LIMITED AI test with monitoring
locust -f performance-testing/locustfile_full.py --host=http://localhost:3000 \
  --headless -u 2 -r 1 -t 30s --csv=performance-testing/results/ai_test
```

#### Key Files
- **Test Scripts**: `/performance-testing/locustfile_*.py`
- **Cost Monitor**: `/performance-testing/scripts/cost_monitor.py`
- **Safety Guide**: `/performance-testing/safety_measures.md`
- **Test Plan**: `/performance-testing/stress_test_plan.md`
- **Results**: `/performance-testing/results/`

#### Safety Guidelines
1. **Always start with minimal tests** (no AI)
2. **Set budget limits** before AI testing
3. **Monitor costs in real-time** during tests
4. **Use test accounts only**, never production
5. **Have emergency shutdown ready**: `pkill -f locust`

#### Performance Targets
- **Auth/CRUD**: < 200ms P95
- **Recipe Browse**: < 500ms P95
- **Vector Search**: < 1s P95
- **AI Generation**: < 5s P95 (costs apply!)

See `/performance-testing/README.md` for complete documentation.

## Architecture Overview

MealMateAI is a microservices-based meal planning application with AI-powered recipe recommendations using RAG (Retrieval-Augmented Generation).

### Core Components
1. **Frontend (React)**: Port 80 - User interface using Material-UI, TypeScript, and Vite
2. **API Gateway (Express.js)**: Port 3000 - Authentication, authorization, and request routing
3. **Microservices**:
   - **User Service (FastAPI)**: Port 8000 - User management, auth, preferences (MySQL)
   - **Recipe Service (FastAPI)**: Port 8001 - Recipe CRUD, vector search (PostgreSQL + Qdrant)
   - **Meal Planner Service (FastAPI)**: Port 8002 - AI meal planning with Gemini LLM (PostgreSQL)
   - **Notification Service (FastAPI)**: Port 8003 - Email notifications (basic implementation)

### Databases
- **MySQL** (Port 13306): User data, authentication, preferences
- **PostgreSQL** (Port 15432): Recipes, meal plans, shared between recipe and meal-planner services
- **Qdrant Vector DB** (Port 6333): Recipe embeddings for semantic search

### Key External Dependencies
- **Google Gemini API**: LLM for meal plan generation and embeddings
- **SMTP**: Email notifications (planned)

## Recipe Service API v2.0 - Vector Search & AI Integration

The Recipe Service has been completely rewritten to provide sophisticated AI-powered recipe recommendations using semantic search and conversation analysis.

### New Architecture Overview

**Complete Upgrade**: The Recipe Service has been transformed from a basic PostgreSQL CRUD API to an advanced semantic search system with AI-powered query generation.

**Core Components:**
- **Vector Database**: 9,366 recipe summaries across 8 semantic collections
- **AI Query Generation**: Gemini 2.5-flash analyzes conversation context  
- **Semantic Search**: `all-mpnet-base-v2` embeddings with cosine similarity
- **Smart Orchestration**: Multi-service architecture with graceful fallbacks

### API Endpoints (v2.0)

**Core AI Endpoints**
- `POST /recommendations` - Main AI-powered personalized recommendations
- `POST /search` - Direct semantic search across collections
- `POST /collections/{name}/search` - Collection-specific semantic search

**Information Endpoints**
- `GET /health` - Service health with detailed component status
- `GET /collections` - List all recipe collections with metadata
- `GET /collections/{name}/info` - Detailed collection information
- `GET /recipes/{id}` - Full recipe details with metadata

**Legacy Compatibility**
- `GET /` - Migration guidance for v1 users
- `GET /search` - Legacy search endpoint with upgrade instructions
- `GET /{recipe_id}` - Legacy recipe access with redirection

### Request/Response Examples

**Personalized Recommendations**
```json
POST /recommendations
{
  "conversation_history": [
    {"role": "user", "content": "I want something sweet for dessert tonight"},
    {"role": "assistant", "content": "What type of dessert are you in the mood for?"},
    {"role": "user", "content": "Something with chocolate would be perfect"}
  ],
  "max_results": 10
}

Response:
{
  "recommendations": [
    {
      "recipe_id": "12345",
      "title": "Double Chocolate Brownies", 
      "collection": "desserts-sweets",
      "similarity_score": 0.95,
      "summary": "Rich, fudgy brownies with...",
      "ingredients_preview": ["dark chocolate", "butter", "eggs"],
      "confidence": 0.87
    }
  ],
  "query_analysis": {
    "detected_preferences": ["sweet", "chocolate", "dessert"],
    "generated_queries": {
      "desserts-sweets": ["chocolate desserts", "rich chocolate treats"],
      "baked-breads": ["chocolate baked goods", "sweet chocolate pastries"]
    },
    "collections_searched": ["desserts-sweets", "baked-breads"],
    "processing_time_ms": 1250
  },
  "total_results": 8
}
```

**Direct Search**
```json
POST /search
{
  "query": "quick breakfast ideas",
  "max_results": 5,
  "collections": ["breakfast-morning", "quick-light"]
}

Response:
{
  "results": [
    {
      "recipe_id": "67890", 
      "title": "5-Minute Scrambled Eggs",
      "collection": "breakfast-morning",
      "similarity_score": 0.89,
      "summary": "Quick and fluffy scrambled eggs..."
    }
  ],
  "query": "quick breakfast ideas",
  "collections_searched": ["breakfast-morning", "quick-light"],
  "total_results": 5,
  "processing_time_ms": 450
}
```

### Service Architecture

**VectorSearchService** (`services/vector_search_service.py`)
- Manages Qdrant client and embedding model
- Handles semantic search across collections
- Enriches results with recipe metadata
- Provides collection management

**QueryGenerationService** (`services/query_generation_service.py`)
- Integrates with Google Gemini API
- Analyzes conversation history for preferences
- Generates 2 optimized queries per collection (16 total)
- Provides intelligent fallbacks when Gemini unavailable

**RecommendationService** (`services/recommendation_service.py`)
- Orchestrates complete recommendation workflow
- Combines query generation and vector search
- Applies preference filtering and ranking
- Manages service health and monitoring

### Data Models

**Pydantic Models** (`models.py`)
- Type-safe request/response validation
- Comprehensive error handling
- Collection configuration management
- Rich metadata structures

### Testing Infrastructure

**Comprehensive Test Suite**
- `run_tests.py` - Complete test runner with dependency checking
- `test_integration.py` - Core service component testing (no server required)
- `test_simple.py` - FastAPI endpoint testing with TestClient
- `test_api.py` - Full API testing with server startup
- `TESTING.md` - Complete testing documentation

**Test Coverage**
- Service initialization and health checks
- Vector search functionality across all collections
- Query generation with/without Gemini API
- Complete API endpoint validation
- Error handling and edge cases
- Legacy endpoint compatibility

### Deployment Requirements

**Prerequisites**
- Qdrant running on localhost:6333
- Vector database loaded via `qdrant_loader.py`
- `GOOGLE_API_KEY` environment variable (optional, has fallback)

**Startup Sequence**
1. Start Qdrant: `docker run -p 6333:6333 qdrant/qdrant`
2. Load vectors: `python3.9 qdrant_loader.py` (one-time setup)
3. Start API: `python3.9 main.py`
4. Validate: `python3.9 run_tests.py`

**Performance Characteristics**
- Semantic search: ~100-500ms per query
- AI query generation: ~1-3 seconds (with Gemini)
- Fallback mode: ~50-200ms (without Gemini)
- Concurrent request handling via FastAPI async

### Migration from v1

**Backward Compatibility**
- Legacy endpoints provide migration guidance
- Existing integrations continue to work
- Clear upgrade paths documented

**New Capabilities** 
- Context-aware recommendations based on conversation
- Semantic search across 8 specialized collections
- AI-powered query optimization
- Rich metadata and similarity scoring

## Key Patterns and Conventions

### Authentication
- JWT-based authentication system
- Tokens issued by User Service, validated by API Gateway
- JWT_SECRET must match between API Gateway and User Service

### Database Patterns
- Each service has dedicated database access
- PostgreSQL shared between Recipe and Meal Planner services for consistency
- Vector embeddings stored in Qdrant for semantic recipe search

### API Patterns
- RESTful APIs with FastAPI auto-documentation at `/docs`
- Consistent error handling and response formats
- Health check endpoints at `/health` for all services

### RAG Implementation
The meal planner uses a sophisticated RAG workflow:
1. **Query Processing**: User requests converted to embeddings
2. **Vector Search**: Semantic recipe matching via Qdrant
3. **Context Assembly**: Retrieved recipes + user preferences
4. **LLM Generation**: Google Gemini generates personalized meal plans
5. **Storage**: Results stored in PostgreSQL

### Inter-Service Communication
Services communicate via HTTP using service names defined in docker-compose.yml:
- `user-service:8000`
- `recipe-service:8001`
- `meal-planner-service:8002`
- Environment variables configure service URLs

### Frontend Architecture
- React 18 with TypeScript
- Material-UI for components
- Context-based state management (AuthContext, ThemeContext)
- React Router for navigation
- Axios for API communication

## Recipe Service Deep Dive

The Recipe Service has been extensively enhanced with AI-powered classification, summary generation, and vector search capabilities.

### Dataset and Classification

**NewDataset13k Integration**
- **Source**: 13,501 recipes from "Food Ingredients and Recipe Dataset with Image Name Mapping"
- **Location**: `/services/recipe-service/NewDataset13k/`
- **Format**: CSV with ingredients, instructions, titles, and image mappings
- **Processing**: Function-based classification system (not cuisine-based)

**Classification System**
- **Script**: `function_based_classifier.py`
- **Method**: Ingredient and cooking method analysis
- **Collections**: 9 semantic categories (beverages excluded from processing)
  - `baked-breads` (885 recipes) - Baking-focused dishes
  - `quick-light` (2,476 recipes) - Fast preparation and light meals  
  - `protein-mains` (1,379 recipes) - Meat, poultry, seafood main dishes
  - `comfort-cooked` (718 recipes) - Slow-cooked and braised dishes
  - `desserts-sweets` (2,465 recipes) - All sweet treats and desserts
  - `breakfast-morning` (415 recipes) - Morning-specific foods
  - `plant-based` (78 recipes) - Vegetarian and vegan dishes
  - `fresh-cold` (950 recipes) - Salads and raw preparations
- **Output**: `/services/recipe-service/function_classification_results/`

### Summary Generation Pipeline

**Gemini API Integration**
- **Purpose**: Generate concise recipe summaries for better semantic search
- **Script**: `generate_missing_summaries.py` 
- **Model**: `gemini-2.5-flash`
- **Authentication**: Requires `GOOGLE_API_KEY` environment variable
- **Processing**: Batch API calls with retry logic and error handling

**Batch Processing Features**
- **Smart Batching**: Collection-specific batch sizes (desserts: 50, protein: 30, etc.)
- **Resume Capability**: Skips existing summaries, regenerates empty files
- **Error Recovery**: Handles API overload (503 errors) with exponential backoff
- **Data Safety**: Handles mixed data types and null values gracefully

**Generated Summaries**
- **Total**: 9,366 recipe summaries (excluding beverages)
- **Location**: `/services/recipe-service/recipe_summaries/`
- **Format**: Individual `.txt` files per recipe, organized by collection
- **Quality**: Clean, concise summaries optimized for vector embedding
- **Usage**: Replace full recipe text for embedding generation

### Testing Infrastructure

**Test Suite Location**: `/services/recipe-service/test_summary_generation/`
- `extract_test_recipes.py` - Creates representative 50-recipe test dataset
- `test_summary_generator.py` - Modified generator for testing
- `test_and_validate.py` - Complete test runner with validation
- `test_parsing_only.py` - Standalone parsing logic validation

**Test Validation**
- **Format Checks**: Appropriate length, no artifacts, proper content
- **Batch Processing**: Validates X recipes → X individual summaries
- **Success Metrics**: 80%+ success rate considered excellent
- **Automated Cleanup**: Optional test file cleanup after validation

### File Organization

**Current Active Files**
```
recipe-service/
├── function_based_classifier.py     # Current classification system
├── generate_missing_summaries.py    # Perfect summary generator
├── function_classification_results/ # Classification data & stats
├── recipe_summaries/               # 9,366 generated summaries
├── NewDataset13k/                  # Source dataset with images
├── test_summary_generation/        # Comprehensive test suite
├── main.py, init.sql, Dockerfile  # Core FastAPI service
└── old/                           # Legacy files (preserved)
```

**Legacy Files Management**
- **Location**: `/services/recipe-service/old/`
- **Contents**: Superseded classification systems, old datasets, debug scripts
- **Purpose**: Preserve development history while maintaining clean workspace

### Vector Database Implementation

**Embedding Approach**
- **Model**: `sentence-transformers/all-mpnet-base-v2` (768 dimensions)
- **Source**: Recipe summaries (not full recipes) for better semantic quality
- **Collections**: 8 separate Qdrant collections (excluding beverages)
- **Metadata**: Rich payloads with recipe details, confidence scores

**Implementation Complete**
- `qdrant_loader.py` - Vector database population script with batch processing
- `test_qdrant_cli.py` - Interactive search testing CLI with collection switching
- Supports resume capability for interrupted loads
- Individual collection search and cross-collection search modes

**Usage Workflow**
1. **Start Qdrant**: `docker run -p 6333:6333 qdrant/qdrant` 
2. **Load Vector Database**: `python3.9 qdrant_loader.py` (one-time setup)
3. **Test Search**: `python3.9 test_qdrant_cli.py` (interactive testing)

**Collections Available**
- `baked-breads` (885 recipes) - Baking-focused dishes
- `quick-light` (2,476 recipes) - Fast preparation and light meals  
- `protein-mains` (1,379 recipes) - Meat, poultry, seafood main dishes
- `comfort-cooked` (718 recipes) - Slow-cooked and braised dishes
- `desserts-sweets` (2,465 recipes) - All sweet treats and desserts
- `breakfast-morning` (415 recipes) - Morning-specific foods
- `plant-based` (78 recipes) - Vegetarian and vegan dishes
- `fresh-cold` (950 recipes) - Salads and raw preparations

### Environment Setup

**Required Environment Variables**
```bash
GOOGLE_API_KEY=your_gemini_api_key_here  # For summary generation
QDRANT_URL=http://localhost:6333        # Vector database connection
```

**Python Version**: Use `python3.9` for all recipe service scripts

### Common Issues and Solutions

**API Overload (503 Errors)**
- **Cause**: High-volume Gemini API usage
- **Solution**: Built-in retry logic with exponential backoff (5s, 10s, 20s)
- **Recovery**: Automatically resumes from last successful batch

**String Concatenation Errors**  
- **Cause**: Mixed data types in recipe data (floats, nulls)
- **Solution**: Automatic type conversion and null handling in batch processing

**Empty Summaries**
- **Detection**: Automatic empty file detection and regeneration
- **Validation**: Test suite checks for content quality and completeness

**Collection Management**
- **Beverages**: Intentionally excluded from processing as requested
- **Switching**: Easy to include/exclude collections by modifying configuration

### Performance Metrics

**Classification Performance**
- **Speed**: ~1,000 recipes/minute on standard hardware
- **Accuracy**: Function-based approach provides better semantic grouping than cuisine-based
- **Confidence**: Average confidence scores tracked per collection

**Summary Generation Performance**  
- **Throughput**: ~50-100 summaries/minute (depends on API limits)
- **Quality**: 95%+ success rate after error handling improvements
- **Efficiency**: Batch processing reduces API calls by 10-50x vs individual requests

### Development Workflow and Decisions

**Why Function-Based Classification?**
- **Better Semantic Grouping**: Users search by cooking method/meal type, not cuisine
- **Improved Search Quality**: "baked desserts" vs "Italian desserts" - more useful categories  
- **RAG Optimization**: Collections align with user intent and meal planning needs
- **Scalable**: Easy to add new functional categories as dataset grows

**Why Summary-Based Embeddings?**
- **Quality**: Gemini-generated summaries are more coherent than raw recipe text
- **Consistency**: Standardized format eliminates noise from varied recipe sources
- **Performance**: Shorter text = faster embedding generation and search
- **Semantic Density**: Summaries capture key recipe elements without irrelevant details

**Why Exclude Beverages?**
- **User Requirement**: Explicitly excluded from meal planning scope
- **Resource Optimization**: Focus processing power on relevant food categories
- **Clean Separation**: Beverages require different search patterns than food recipes

**Technical Architecture Decisions**
- **Batch Processing**: Reduces API costs and improves reliability vs individual calls  
- **File-Based Caching**: Simple, reliable persistence with easy debugging
- **Collection Separation**: Enables targeted search within specific meal categories
- **Summary Validation**: Automated testing ensures quality before vector database loading

**Error Handling Philosophy**
- **Graceful Degradation**: Continue processing despite individual failures
- **Smart Retry**: Exponential backoff for API limits, immediate retry for network issues
- **Resume Capability**: Always allow restarting from last successful point
- **Data Preservation**: Never overwrite good data, only regenerate empty/failed items

## Development Guidelines

### Code Quality and Linting
- **Always run linting** before committing code
- **Python services**: Use `ruff check .` and `ruff format .` for code formatting (if configured)
- **Frontend/API Gateway**: Check individual `package.json` files for ESLint/Prettier configurations
- **Testing**: Run tests before merging - use service-specific test commands above

### Adding New Features
1. Determine appropriate service or create new microservice
2. Follow FastAPI patterns for backend services
3. Use existing database models and schemas as templates
4. Implement health checks for new services
5. Update docker-compose.yml for new services

### Testing Strategy
- Unit tests in `/tests/unit/` directories
- Integration tests in `/tests/integration/` directories
- End-to-end testing via Python scripts
- RAG workflow testing scripts for AI functionality

### Database Migrations
- Use SQLAlchemy for Python services
- Migration files should be added to `/migrations/` if created
- Services auto-create tables on startup (see `init.sql` files)

### Environment Configuration
- Environment variables defined in docker-compose.yml
- Database credentials and API keys configured per service
- JWT secrets must be consistent across gateway and user service

### AI/ML Components
- Recipe embeddings generated using SentenceTransformers (all-mpnet-base-v2)
- Recipe summaries generated using Google Gemini API for better semantic search
- Vector similarity search for recipe recommendations via Qdrant
- LLM prompts stored in `/prompts/` directories
- Embedding dimension: 768 (matches all-mpnet-base-v2)

### File Structure Patterns
- Each microservice follows similar structure: `/app/controllers/`, `/app/services/`, `/app/models/`, `/app/repositories/`
- React components in `/src/components/`, pages in `/src/pages/`
- Shared utilities in `/src/services/` for frontend

## Important Files

### Project-Level Files
- `ARCHITECTURE.md`: Detailed system architecture documentation
- `docs/architecture-diagram.md`: Mermaid diagrams for system visualization
- `docker-compose.yml`: Service orchestration and environment configuration
- `CLAUDE.md`: This comprehensive development guide
- Frontend `package.json`: Node.js dependencies and scripts

### Recipe Service Key Files (AI-Powered Architecture v2.0.0)

**Core Application Files:**
- `services/recipe-service/main.py`: FastAPI application with comprehensive RAG architecture
- `services/recipe-service/models.py`: Pydantic models for request/response validation
- `services/recipe-service/requirements.txt`: Python dependencies (FastAPI, Qdrant, Gemini, etc.)
- `services/recipe-service/Dockerfile`: Multi-stage container build with model caching
- `services/recipe-service/init.sql`: Database initialization for PostgreSQL

**AI/ML Service Layer:**
- `services/recipe-service/services/recommendation_service.py`: RAG orchestrator service
- `services/recipe-service/services/vector_search_service.py`: Qdrant vector database client
- `services/recipe-service/services/query_generation_service.py`: Google Gemini LLM integration
- `services/recipe-service/logging_config.py`: Centralized logging with file and console output

**Data Processing & Classification:**
- `services/recipe-service/function_based_classifier.py`: Function-based recipe classification (8 collections)
- `services/recipe-service/generate_missing_summaries.py`: Gemini-powered summary generator
- `services/recipe-service/qdrant_loader.py`: Vector database population with progress tracking
- `services/recipe-service/function_classification_results/`: Classification data for 13,501 recipes
- `services/recipe-service/recipe_summaries/`: 9,366 AI-generated recipe summaries for embeddings

**Dataset & Testing:**
- `services/recipe-service/NewDataset13k/`: Complete recipe dataset with images (13,501 recipes)  
- `services/recipe-service/test_api_clean.py`: Comprehensive API test suite
- `services/recipe-service/old/`: Legacy files and development history (preserved)

### Service-Specific Files
- Service-specific `requirements.txt`: Python dependencies for each microservice
- Service `main.py`: FastAPI application entry points
- Service `init.sql`: Database initialization scripts

## New Features - Recipe Replacement & Enhanced Grocery Lists

### Recipe Replacement System (v1.0.0)

**Overview**: A sophisticated recipe replacement system that allows users to swap recipes in their meal plans using AI-powered search with intelligent category detection.

#### Key Features

**1. Intelligent Category Detection**
- Automatically detects recipe categories based on meal type, ingredients, and recipe characteristics
- Maps to Recipe Service collections: `desserts-sweets`, `protein-mains`, `quick-light`, `breakfast-morning`, `comfort-cooked`, `baked-breads`, `plant-based`, `fresh-cold`
- Smart fallback logic based on meal context (breakfast → breakfast-morning, lunch → quick-light, dinner → protein-mains)

**2. Inline Search Interface**  
- Replace button on each meal card that opens an expandable search widget
- Real-time RAG-powered search with 500ms debouncing
- Auto-generated search queries based on current recipe context
- Visual similarity scoring and collection tags
- One-click recipe replacement with optimistic UI updates

**3. RAG Integration**
- Uses Recipe Service `/collections/{collection}/search` endpoint for targeted search
- Semantic search within appropriate recipe categories
- Returns recipes with similarity scores, summaries, and collection metadata
- Graceful fallbacks when search fails or returns no results

#### Implementation Details

**Frontend Components:**
- Enhanced `renderMealCard()` with replace functionality (`frontend/src/pages/MealPlanner.tsx`)
- Category detection algorithm with 8 recipe classification rules
- Debounced search with loading states and error handling
- Optimistic UI updates with undo functionality

**Backend Integration:**
- New endpoint: `POST /{meal_plan_id}/replace-recipe` (`services/meal-planner-service/app/controllers/meal_plan_controller.py`)
- Service method: `replace_recipe()` in meal plan service with database transaction support
- Pydantic schema: `ReplaceRecipeRequest` for API validation
- Full meal plan data synchronization after replacement

**API Endpoints:**
```
POST /api/meal-plans/{meal_plan_id}/replace-recipe
{
  "old_recipe_id": 123,
  "new_recipe_id": 456, 
  "day": 2,
  "meal_type": "lunch"
}
```

**Search Integration:**
```
POST /api/recipes/collections/{collection}/search
{
  "query": "similar breakfast dish",
  "max_results": 5
}
```

#### Usage Workflow

1. **User clicks "Replace" button** on any meal card
2. **System detects category** using ingredient analysis and meal context
3. **Auto-generates search query** like "lunch similar to [current recipe]"  
4. **Performs semantic search** within detected collection
5. **Displays results** with similarity scores and quick preview
6. **User selects replacement** with single click
7. **Updates meal plan** optimistically with database synchronization
8. **Provides undo option** via snackbar notification

### Enhanced Grocery List System (v2.1.0)

**Overview**: Completely rebuilt grocery list generation with robust error handling, intelligent ingredient processing, enhanced user experience, and **persistent caching with automatic invalidation**.

#### Key Improvements

**1. Robust Error Handling & Retry Logic**
- 3-tier retry system with exponential backoff (2s, 4s, 8s delays)
- Graceful degradation with multiple fallback strategies
- Smart ingredient preprocessing with type validation
- JSON response cleaning (removes markdown formatting)
- Comprehensive error logging and user feedback

**2. Enhanced Ingredient Processing**
- Advanced ingredient aggregation and deduplication
- Unit standardization and quantity consolidation  
- Category-based ingredient classification
- Handles mixed data types (strings, arrays, nulls)
- Intelligent cleanup of malformed ingredient data

**3. Improved User Experience**
- Enhanced loading states with progress indicators
- Detailed error messages with retry buttons
- Organized display by grocery store categories
- Quantity chips and hover effects
- Refresh functionality and empty state handling
- Professional UI with category sections and item counts

**4. Persistent Caching with Smart Invalidation (NEW in v2.1.0)**
- Grocery lists are automatically saved to database after generation
- Cached lists are served instantly on subsequent requests (<100ms)
- Cache is automatically cleared when meal plan changes:
  - Recipe replacement clears cache
  - Meal moving/swapping clears cache  
  - Day reordering clears cache
- Manual refresh option forces cache regeneration
- Graceful fallback handling for corrupted cache data

#### Technical Implementation

**Backend Enhancements:**
- Redesigned `generate_grocery_list()` with 3-attempt retry logic (`services/meal-planner-service/app/services/gemini_service.py`)
- New fallback methods: `_create_fallback_grocery_list_from_ingredients()` and `_create_fallback_grocery_list_from_recipes()`
- Enhanced Gemini prompt engineering for better JSON responses
- Comprehensive input validation and data type handling

**Frontend Improvements:**
- Enhanced grocery list UI with category organization (`frontend/src/pages/MealPlanner.tsx`)
- Professional loading states with detailed progress messages
- Error handling with retry buttons and helpful messaging
- Improved visual hierarchy with Paper components and chips
- Empty state with generate button for better UX

**Error Recovery Strategies:**
1. **Primary**: Gemini API with optimized prompts
2. **Secondary**: Basic ingredient categorization using keyword matching  
3. **Fallback**: Recipe name-based grocery items with manual review prompts

#### Usage Examples

**Enhanced Loading State:**
```
Generating your grocery list...
This may take a moment while we analyze your recipes
```

**Error Recovery:**
```
⚠️ Failed to generate grocery list [Retry Button]
There was an issue generating your grocery list. You can try again or manually review your meal plan recipes.
```

**Organized Display:**
```
📦 Produce (5 items)
  🥕 Carrots • 2 cups
  🧅 Onions • 1 large
  
🥛 Dairy (3 items)  
  🥛 Milk • 2.5 cups
  🧈 Butter • 4 tbsp
```

#### Key Files Modified

**Frontend:**
- `frontend/src/pages/MealPlanner.tsx`: Complete replacement UI and enhanced grocery list display
- `frontend/src/services/mealPlannerService.ts`: New search and replacement API functions

**Backend:**
- `services/meal-planner-service/app/services/gemini_service.py`: Robust grocery list generation
- `services/meal-planner-service/app/controllers/meal_plan_controller.py`: Recipe replacement endpoint
- `services/meal-planner-service/app/models/schemas.py`: New schemas for replacement requests
- `services/meal-planner-service/app/services/meal_plan_service.py`: Recipe replacement business logic

#### Performance & Reliability

**Recipe Replacement:**
- Search response: ~100-500ms (semantic search)
- Category detection: <50ms (rule-based algorithm)
- Database transaction: ~100-200ms (optimistic UI updates)

**Grocery List Generation:**
- Primary path: 1-3 seconds (Gemini API processing)
- Fallback path: 200-500ms (local categorization)
- Success rate: >95% with retry logic
- User feedback: Real-time loading states and error recovery

These enhancements significantly improve user experience and system reliability, providing intelligent recipe management and dependable grocery list functionality.