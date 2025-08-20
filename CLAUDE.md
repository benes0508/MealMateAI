# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Docker Operations
- **Start all services**: `docker-compose up --build`
- **Start detached**: `docker-compose up -d --build`
- **View logs**: `docker-compose logs -f`
- **Stop services**: `docker-compose down`
- **Rebuild single service**: `docker-compose build <service-name>`

### Frontend (React + Vite)
- **Development server**: `npm start` (from `/frontend`)
- **Build**: `npm run build` (from `/frontend`)
- **Preview build**: `npm run serve` (from `/frontend`)
- **Tests**: `npm test` (from `/frontend`)

### API Gateway (Express.js)
- **Development**: `npm run dev` (from `/api-gateway`)
- **Production**: `npm start` (from `/api-gateway`)
- **Tests**: `npm test` (from `/api-gateway`)

### Python Services (FastAPI)
- **Run locally**: `python run.py` or `python run_local.py` (from service directory)
- **Tests**: `pytest` (from service directory)
- **Dependencies**: Install from `requirements.txt` in each service

### Recipe Service Specific Commands
- **Classify recipes**: `python3.9 function_based_classifier.py` (from `/services/recipe-service`)
- **Generate summaries**: `python3.9 generate_missing_summaries.py` (from `/services/recipe-service`)
- **Test summary generation**: `python3.9 test_and_validate.py` (from `/services/recipe-service/test_summary_generation`)
- **Load vector database**: `python3.9 qdrant_loader.py` (from `/services/recipe-service`)
- **Test vector search**: `python3.9 test_qdrant_cli.py` (from `/services/recipe-service`)

### Testing
- **End-to-end tests**: `python scripts/test_end_to_end.py`
- **RAG workflow test**: `./test_rag_workflow.sh`
- **Detailed RAG test**: `./test_rag_detailed.sh`

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

### Recipe Service Key Files  
- `services/recipe-service/function_based_classifier.py`: Current recipe classification system
- `services/recipe-service/generate_missing_summaries.py`: Gemini-powered summary generator
- `services/recipe-service/qdrant_loader.py`: Vector database population script
- `services/recipe-service/test_qdrant_cli.py`: Interactive vector search test CLI
- `services/recipe-service/function_classification_results/`: Classification outputs and statistics
- `services/recipe-service/recipe_summaries/`: 9,366 generated recipe summaries
- `services/recipe-service/NewDataset13k/`: Complete recipe dataset with images
- `services/recipe-service/test_summary_generation/`: Comprehensive testing infrastructure
- `services/recipe-service/old/`: Archived legacy files and experiments
- `services/recipe-service/requirements.txt`: Python dependencies for recipe service

### Service-Specific Files
- Service-specific `requirements.txt`: Python dependencies for each microservice
- Service `main.py`: FastAPI application entry points
- Service `init.sql`: Database initialization scripts