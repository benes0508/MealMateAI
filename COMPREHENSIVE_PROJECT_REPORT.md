# MealMateAI - Comprehensive Project Report

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Summary](#architecture-summary)
3. [Database Systems](#database-systems)
4. [API Documentation](#api-documentation)
5. [Frontend Implementation](#frontend-implementation)
6. [Backend Implementation](#backend-implementation)
7. [Software Features](#software-features)
8. [Implementation Details](#implementation-details)
9. [Technical Stack](#technical-stack)
10. [AI/ML Components](#aiml-components)
11. [Deployment & Infrastructure](#deployment--infrastructure)

---

## Project Overview

**MealMateAI** is an intelligent, AI-powered meal planning application built using a modern microservices architecture. The system leverages advanced machine learning technologies including Large Language Models (LLMs) and vector databases to provide personalized recipe recommendations and automated meal planning.

### Core Vision
Transform the way people plan meals by providing:
- AI-powered personalized meal recommendations
- Intelligent recipe search using semantic similarity
- Automated grocery list generation
- User preference learning and adaptation
- Scalable microservices architecture for enterprise deployment

### Key Technologies
- **Frontend**: React 18 with TypeScript, Material-UI, Vite
- **Backend**: FastAPI microservices with Python 3.9+
- **AI/ML**: Google Gemini LLM, Qdrant Vector Database, SentenceTransformers
- **Databases**: PostgreSQL, MySQL, Qdrant Vector DB
- **Infrastructure**: Docker, Docker Compose, NGINX
- **Authentication**: JWT-based authentication system

---

## Architecture Summary

### System Architecture
MealMateAI follows a **microservices architecture** pattern with the following key principles:
- **Service Independence**: Each microservice operates independently with its own database
- **API-First Design**: All services communicate via RESTful APIs
- **Containerization**: All components are containerized using Docker
- **Scalability**: Horizontal scaling capabilities for individual services
- **AI Integration**: Seamless integration with external AI services

### Core Components
1. **React Frontend** (Port 80) - User interface layer
2. **Express.js API Gateway** (Port 3000) - Authentication & request routing
3. **User Service** (Port 8000) - User management & authentication
4. **Recipe Service** (Port 8001) - Recipe management & vector search
5. **Meal Planner Service** (Port 8002) - AI-powered meal planning
6. **Notification Service** (Port 8003) - Notification management
7. **Database Layer** - Multiple specialized databases
8. **External AI Services** - Google Gemini API integration

---

## Database Systems

### 1. MySQL Database (User Service)
**Purpose**: User account management and authentication
**Port**: 13306
**Schema**:
```sql
-- Users table with authentication and basic preferences
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- User Preference Fields
    allergies JSON,                    -- List of user allergies
    disliked_ingredients JSON,         -- Ingredients user dislikes
    preferred_cuisines JSON,           -- Preferred cuisine types
    preferences JSON                   -- Additional user preferences
);
```

**Key Features**:
- JWT-based authentication
- User preference storage as JSON fields
- Account activation and role management
- Optimized for transactional operations

### 2. PostgreSQL Database (Recipe & Meal Planner Services)
**Purpose**: Recipe storage and meal plan management
**Port**: 15432
**Shared Database Strategy**: Both Recipe and Meal Planner services share the same PostgreSQL instance for data consistency

#### Recipe Service Tables:
```sql
-- Comprehensive recipe storage with metadata
CREATE TABLE recipes (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    ingredients TEXT[],                -- Array of ingredients
    meal_type TEXT[],                 -- breakfast, lunch, dinner, snack
    dietary_tags TEXT[],              -- vegan, vegetarian, gluten-free, etc.
    allergens TEXT[],                 -- known allergens in recipe
    difficulty TEXT,                  -- easy, medium, hard
    json_path TEXT,                   -- path to detailed recipe JSON
    txt_path TEXT,                    -- path to recipe text file
    cuisine TEXT[],                   -- cuisine types
    tags TEXT[],                      -- general tags
    directions TEXT,                  -- cooking instructions
    img_src TEXT,                     -- recipe image URL
    prep_time TEXT,                   -- preparation time
    cook_time TEXT,                   -- cooking time
    servings TEXT,                    -- number of servings
    rating TEXT,                      -- recipe rating
    nutrition TEXT,                   -- nutritional information
    url TEXT,                         -- source URL
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Meal Planner Service Tables:
```sql
-- Meal plan metadata
CREATE TABLE meal_plans (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,              -- Foreign key to users table
    plan_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    days INT NOT NULL DEFAULT 7,       -- Duration of meal plan
    meals_per_day INT NOT NULL DEFAULT 3,
    plan_data TEXT,                    -- Serialized meal plan data
    plan_explanation TEXT              -- AI-generated explanation
);

-- Recipe assignments to meal plans
CREATE TABLE meal_plan_recipes (
    id SERIAL PRIMARY KEY,
    meal_plan_id INT REFERENCES meal_plans(id),
    recipe_id INT,                     -- Reference to recipe
    day INT NOT NULL,                  -- Day number (1-7)
    meal_type VARCHAR(50) NOT NULL     -- breakfast, lunch, dinner, snack
);

-- Cached user preferences for faster meal planning
CREATE TABLE user_preferences_cache (
    id SERIAL PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    dietary_restrictions TEXT,
    allergies TEXT,
    cuisine_preferences TEXT,
    disliked_ingredients TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Key Features**:
- Full-text search capabilities for recipes
- JSON field support for flexible metadata
- Complex relational queries for meal planning
- Optimized indexes for search performance

### 3. Qdrant Vector Database
**Purpose**: Semantic recipe search using machine learning embeddings
**Port**: 6333
**Type**: Specialized vector database for AI applications

#### Collection Structure:
The system uses **8 specialized collections** based on recipe categories:

1. **baked-breads** (885 recipes) - Baking-focused dishes
2. **quick-light** (2,476 recipes) - Fast preparation and light meals  
3. **protein-mains** (1,379 recipes) - Meat, poultry, seafood main dishes
4. **comfort-cooked** (718 recipes) - Slow-cooked and braised dishes
5. **desserts-sweets** (2,465 recipes) - All sweet treats and desserts
6. **breakfast-morning** (415 recipes) - Morning-specific foods
7. **plant-based** (78 recipes) - Vegetarian and vegan dishes
8. **fresh-cold** (950 recipes) - Salads and raw preparations

#### Vector Structure:
```python
# Each recipe vector contains:
{
    "id": recipe_id,                    # Unique recipe identifier
    "vector": [768-dimensional array],   # SentenceTransformer embedding
    "payload": {
        "recipe_id": str,
        "title": str,
        "collection": str,              # Collection name
        "confidence": float,            # Classification confidence
        "summary": str,                 # AI-generated recipe summary
        "ingredients_preview": str,     # First 5 ingredients
        "instructions_preview": str     # First 200 chars of instructions
    }
}
```

**Key Features**:
- **768-dimensional vectors** using `all-mpnet-base-v2` model
- **Cosine similarity** search for semantic matching
- **Collection-based filtering** for targeted searches
- **Rich metadata payload** for detailed results
- **9,366 total recipe embeddings** across all collections

---

## API Documentation

### 1. User Service API (Port 8000)
**Base URL**: `http://localhost:8000/api/users/`
**Technology**: FastAPI with SQLAlchemy ORM

#### Endpoints:
```http
# Authentication
POST /login
Content-Type: application/json
{
    "email": "user@example.com",
    "password": "password123"
}
Response: { "access_token": "jwt_token", "user_id": 123 }

# User Management
GET /                          # List all users (admin only)
POST /                         # Create new user
GET /{user_id}                 # Get user details
PUT /{user_id}                 # Update user
DELETE /{user_id}              # Delete user
GET /health                    # Health check
```

#### Features:
- JWT token generation and validation
- Password hashing with bcrypt
- User preference management
- Role-based access control
- Email uniqueness validation

### 2. Recipe Service API (Port 8001)
**Base URL**: `http://localhost:8001/`
**Technology**: FastAPI with advanced AI integration

#### Core Endpoints:
```http
# Vector-Powered Search
POST /search
Content-Type: application/json
{
    "query": "chocolate cake recipes",
    "max_results": 10,
    "collections": ["desserts-sweets", "baked-breads"]  # Optional
}
Response: {
    "results": [...],
    "total_results": 5,
    "processing_time_ms": 157,
    "collections_searched": ["desserts-sweets"]
}

# AI-Powered Recommendations
POST /recommendations
Content-Type: application/json
{
    "conversation_history": [
        {"role": "user", "content": "I want something sweet for dessert"},
        {"role": "assistant", "content": "What type of dessert?"},
        {"role": "user", "content": "Something with chocolate"}
    ],
    "max_results": 5
}

# Collection Management
GET /collections                    # List all recipe collections
GET /collections/{collection}/info  # Collection details
POST /collections/{collection}/search # Search within collection

# Recipe Details
GET /recipes/{recipe_id}            # Detailed recipe information

# Legacy Support
GET /                              # Basic recipe listing
GET /csv                           # Original CSV data access
```

#### Advanced Features:
- **Semantic Search**: Uses Qdrant vector database for AI-powered recipe matching
- **Conversation Analysis**: Gemini LLM analyzes user conversations to understand preferences
- **Multi-Collection Search**: Search across multiple recipe categories simultaneously
- **Real-time Query Generation**: AI generates optimized search queries for each collection
- **Rich Metadata**: Returns detailed recipe information with similarity scores

### 3. Meal Planner Service API (Port 8002)
**Base URL**: `http://localhost:8002/`
**Technology**: FastAPI with RAG (Retrieval-Augmented Generation)

#### Core Endpoints:
```http
# AI-Powered Meal Planning
POST /rag
Content-Type: application/json
{
    "user_id": 123,
    "preferences": {
        "dietary_restrictions": ["vegetarian"],
        "allergies": ["nuts"],
        "cuisine_preferences": ["italian", "mediterranean"]
    },
    "days": 7,
    "meals_per_day": 3,
    "additional_requirements": "low sodium, high protein"
}

# Basic Meal Planning
POST /
Content-Type: application/json
{
    "user_id": 123,
    "days": 7,
    "meals_per_day": 3
}

# Meal Plan Management
GET /{meal_plan_id}                    # Get meal plan details
PUT /{meal_plan_id}/move-meal          # Move meals between days
PUT /{meal_plan_id}/swap-days          # Swap entire days

# Grocery List Generation
GET /{meal_plan_id}/grocery-list       # Generate shopping list

# Health Check
GET /health                            # Service health status
```

#### RAG Workflow Features:
1. **User Preference Analysis**: Retrieves and analyzes user dietary preferences
2. **Recipe Retrieval**: Uses vector search to find compatible recipes
3. **Context Assembly**: Combines user preferences with retrieved recipes
4. **LLM Generation**: Google Gemini generates personalized meal plans
5. **Interactive Modification**: Users can modify and regenerate plans
6. **Automated Grocery Lists**: Generates consolidated shopping lists

### 4. Notification Service API (Port 8003)
**Base URL**: `http://localhost:8003/api/notifications/`
**Technology**: FastAPI with email integration

#### Endpoints:
```http
# Notification Management
GET /                              # List user notifications
POST /                             # Create notification
GET /{notification_id}             # Get notification details
PUT /{notification_id}/read        # Mark as read

# Email Notifications
POST /email
Content-Type: application/json
{
    "user_id": 123,
    "subject": "Your meal plan is ready!",
    "message": "Check out your personalized meal plan...",
    "priority": "normal"
}

# Health Check
GET /health                        # Service health status
```

### 5. API Gateway (Port 3000)
**Technology**: Express.js with JWT middleware

#### Routing Structure:
```javascript
// Authentication & Authorization
app.use('/api/users/*', authenticateJWT, proxyTo('user-service:8000'))
app.use('/api/recipes/*', authenticateJWT, proxyTo('recipe-service:8001'))
app.use('/api/meal-plans/*', authenticateJWT, proxyTo('meal-planner-service:8002'))
app.use('/api/notifications/*', authenticateJWT, proxyTo('notification-service:8003'))

// Public endpoints (no authentication required)
app.use('/health', healthCheckRouter)
app.use('/api/users/login', proxyTo('user-service:8000'))
```

#### Features:
- **JWT Token Validation**: Validates tokens on every request
- **Request Routing**: Routes requests to appropriate microservices
- **CORS Handling**: Manages cross-origin requests
- **Rate Limiting**: Prevents API abuse
- **Logging & Monitoring**: Comprehensive request logging

---

## Frontend Implementation

### Technology Stack
- **React 18**: Latest React with hooks and concurrent features
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and development server
- **Material-UI (MUI) v5**: Google's Material Design components
- **React Router v6**: Client-side routing
- **Axios**: HTTP client for API communication
- **Formik + Yup**: Form handling and validation
- **React Beautiful DnD**: Drag-and-drop functionality

### Project Structure
```
frontend/src/
├── components/           # Reusable UI components
│   ├── layouts/         # Layout components
│   ├── ProtectedRoute.tsx
│   ├── PreferenceSetup.tsx
│   └── Footer.tsx
├── context/             # React Context providers
│   ├── AuthContext.tsx  # Authentication state
│   └── ThemeContext.tsx # Theme management
├── pages/               # Page components
│   ├── Home.tsx
│   ├── Login.tsx
│   ├── MealPlanning.tsx
│   ├── Recipes.tsx
│   └── Profile.tsx
├── services/            # API service layer
│   ├── api.ts          # Axios configuration
│   ├── authService.ts  # Authentication API calls
│   ├── recipeService.ts # Recipe API calls
│   └── mealPlanService.ts # Meal planning API calls
├── types/              # TypeScript type definitions
├── utils/              # Utility functions
├── App.tsx             # Main application component
└── main.tsx           # Application entry point
```

### Key Components

#### 1. Authentication System
```typescript
// AuthContext.tsx - Global authentication state
interface AuthContextType {
    user: User | null;
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    loading: boolean;
}

// Features:
// - JWT token management
// - Automatic token refresh
// - Protected route handling
// - User session persistence
```

#### 2. Material-UI Integration
```typescript
// Theme system with dark/light mode
const theme = createTheme({
    palette: {
        mode: isDarkMode ? 'dark' : 'light',
        primary: { main: '#4CAF50' },      // Green theme
        secondary: { main: '#FF9800' }     // Orange accent
    },
    typography: {
        fontFamily: '"Roboto", "Arial", sans-serif'
    }
});

// Key UI Components:
// - AppBar with navigation
// - Drawer for mobile navigation
// - Card-based recipe display
// - Form components with validation
// - Data tables for meal plans
// - Drag-and-drop meal organization
```

#### 3. Recipe Search Interface
```typescript
// Advanced search with real-time results
const RecipeSearch: React.FC = () => {
    const [query, setQuery] = useState('');
    const [filters, setFilters] = useState<SearchFilters>({});
    const [results, setResults] = useState<Recipe[]>([]);
    
    // Features:
    // - Real-time search suggestions
    // - Advanced filtering options
    // - Infinite scroll loading
    // - Recipe favoriting
    // - Detailed recipe modal
};
```

#### 4. Meal Planning Interface
```typescript
// Interactive meal planning with drag-and-drop
const MealPlanningBoard: React.FC = () => {
    // Features:
    // - 7-day calendar view
    // - Drag-and-drop meal assignment
    // - AI-powered meal suggestions
    // - Dietary restriction filtering
    // - Grocery list generation
    // - Meal plan sharing
};
```

### State Management
- **React Context**: Global state for authentication and theme
- **Local Component State**: Component-specific state with hooks
- **Custom Hooks**: Reusable state logic for API calls
- **Form State**: Formik for complex form management

### Responsive Design
- **Mobile-First**: Designed for mobile devices first
- **Breakpoints**: Material-UI breakpoint system
- **Touch-Friendly**: Large touch targets and gestures
- **Progressive Web App**: PWA capabilities for mobile installation

---

## Backend Implementation

### Technology Stack
- **FastAPI**: Modern Python web framework with automatic API documentation
- **SQLAlchemy 2.0**: Advanced ORM with async support
- **Pydantic**: Data validation and serialization
- **Uvicorn**: ASGI server for high-performance async operations
- **PostgreSQL**: Primary database with advanced features
- **MySQL**: User data with transactional consistency
- **Docker**: Containerization for all services

### Service Architecture

#### 1. User Service
**File Structure**:
```
services/user-service/
├── app/
│   ├── controllers/         # API route handlers
│   ├── services/           # Business logic layer
│   ├── models/            # SQLAlchemy database models
│   ├── repositories/      # Data access layer
│   ├── database.py        # Database configuration
│   └── main.py           # FastAPI application setup
├── requirements.txt
├── Dockerfile
└── init.sql             # Database initialization
```

**Key Features**:
```python
# Authentication with JWT
from passlib.context import CryptContext
from jose import JWTError, jwt

class AuthService:
    def authenticate_user(self, email: str, password: str) -> User:
        # Verify password with bcrypt hashing
        # Generate JWT token with user claims
        # Return authenticated user object
        
    def create_access_token(self, data: dict) -> str:
        # Create JWT token with expiration
        # Include user ID and permissions
```

#### 2. Recipe Service (Advanced AI Integration)
**File Structure**:
```
services/recipe-service/
├── main.py                          # FastAPI application
├── models.py                        # Pydantic models
├── services/
│   ├── recommendation_service.py    # Main orchestration
│   ├── vector_search_service.py     # Qdrant integration
│   └── query_generation_service.py  # Gemini LLM integration
├── function_classification_results/ # Recipe classification data
├── recipe_summaries/               # AI-generated summaries
├── qdrant_loader.py               # Vector database loader
└── requirements.txt
```

**Advanced Features**:
```python
# Vector Search Service
class VectorSearchService:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
        self.model = SentenceTransformer("all-mpnet-base-v2")
    
    async def search_collection(self, collection_name: str, 
                              query: str, limit: int = 5):
        # Generate 768-dimensional embedding for query
        query_embedding = self.model.encode(query)
        
        # Perform semantic search in Qdrant
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=limit,
            with_payload=True
        )
        
        # Convert to recipe recommendations
        return [self._create_recommendation(r) for r in results]

# AI Query Generation
class QueryGenerationService:
    def __init__(self):
        self.client = GoogleGenerativeAI(api_key=GOOGLE_API_KEY)
    
    async def analyze_conversation_context(self, 
                                         conversation_history: List[Message]):
        # Use Gemini to analyze user preferences
        # Extract dietary restrictions, cuisines, meal types
        # Generate targeted search queries for each collection
```

#### 3. Meal Planner Service (RAG Implementation)
**RAG Workflow**:
```python
# Retrieval-Augmented Generation for Meal Planning
class RAGMealPlannerService:
    async def generate_meal_plan(self, user_preferences: dict, 
                               days: int = 7) -> MealPlan:
        # Step 1: Retrieve user preferences from User Service
        user_data = await self.get_user_preferences(user_id)
        
        # Step 2: Generate search queries for compatible recipes
        search_queries = await self.generate_search_queries(
            user_preferences, user_data
        )
        
        # Step 3: Retrieve relevant recipes using vector search
        relevant_recipes = await self.search_recipes(search_queries)
        
        # Step 4: Assemble context for LLM
        context = self.assemble_context(
            user_preferences, relevant_recipes, user_data
        )
        
        # Step 5: Generate meal plan using Gemini LLM
        meal_plan = await self.generate_with_llm(context, days)
        
        # Step 6: Store and return structured meal plan
        return await self.store_meal_plan(meal_plan)
```

#### 4. Inter-Service Communication
```python
# Service-to-Service HTTP Communication
class ServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def get_user_preferences(self, user_id: int) -> dict:
        response = await self.client.get(
            f"{self.base_url}/api/users/{user_id}"
        )
        return response.json()
    
    async def search_recipes(self, query: str, 
                           collections: List[str]) -> List[dict]:
        response = await self.client.post(
            f"{self.recipe_service_url}/search",
            json={"query": query, "collections": collections}
        )
        return response.json()["results"]
```

### Database Integration

#### SQLAlchemy Models
```python
# User model with preferences
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # JSON fields for flexible preferences
    allergies = Column(JSON)
    disliked_ingredients = Column(JSON)
    preferred_cuisines = Column(JSON)
    preferences = Column(JSON)

# Recipe model with full metadata
class Recipe(Base):
    __tablename__ = "recipes"
    
    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)
    ingredients = Column(ARRAY(Text))      # PostgreSQL array
    dietary_tags = Column(ARRAY(Text))
    cuisine = Column(ARRAY(Text))
    
    # Full-text search index
    __table_args__ = (
        Index('ix_recipes_search', 'name', 'ingredients', 
              postgresql_using='gin'),
    )
```

### Error Handling & Logging
```python
# Comprehensive error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.utcnow()}
    )

# Structured logging
import structlog
logger = structlog.get_logger()

async def process_request(request_data):
    logger.info("Processing request", 
               user_id=request_data.user_id,
               request_type=request_data.type)
```

---

## Software Features

### 1. User Management Features
- **User Registration & Authentication**: Secure account creation with email verification
- **JWT-Based Security**: Stateless authentication with token refresh
- **User Profiles**: Comprehensive user preference management
- **Dietary Restrictions**: Support for allergies, dietary preferences, and restrictions
- **Role-Based Access**: Admin and user role management
- **Account Management**: Profile editing, password reset, account deactivation

### 2. Recipe Management Features
- **Recipe Database**: 13,501 classified recipes across 8 categories
- **AI-Powered Search**: Semantic search using vector embeddings
- **Advanced Filtering**: Filter by cuisine, dietary restrictions, cooking time, difficulty
- **Recipe Collections**: Organized categories (desserts, proteins, quick meals, etc.)
- **Recipe Details**: Comprehensive recipe information with images and nutrition
- **Recipe Ratings**: User rating and review system (planned)
- **Recipe Favorites**: Personal recipe collection management

### 3. Intelligent Meal Planning Features
- **AI-Powered Meal Plans**: LLM-generated personalized meal plans
- **RAG-Based Recommendations**: Context-aware recipe suggestions
- **Conversation Analysis**: Natural language preference understanding
- **Flexible Planning**: 1-30 day meal plans with customizable meals per day
- **Dietary Compliance**: Automatic filtering based on user restrictions
- **Meal Plan Modification**: Drag-and-drop meal rearrangement
- **Smart Substitutions**: AI-powered recipe alternatives
- **Nutritional Balance**: Automated nutritional analysis and balancing

### 4. Shopping & Grocery Features
- **Automated Grocery Lists**: Generated from meal plans
- **Ingredient Consolidation**: Smart combination of similar ingredients
- **Shopping List Optimization**: Organized by store categories
- **Pantry Management**: Track existing ingredients (planned)
- **Price Comparison**: Grocery price tracking (planned)
- **Delivery Integration**: Integration with grocery delivery services (planned)

### 5. AI & Machine Learning Features
- **Semantic Recipe Search**: 768-dimensional vector embeddings using SentenceTransformers
- **Natural Language Processing**: Google Gemini LLM for conversation analysis
- **Preference Learning**: AI learns user preferences over time
- **Recipe Classification**: Automatic recipe categorization into 8 collections
- **Smart Query Generation**: AI generates optimized search queries
- **Contextual Recommendations**: Context-aware recipe suggestions

### 6. Social & Community Features (Planned)
- **Recipe Sharing**: Share custom recipes and meal plans
- **Community Ratings**: Recipe rating and review system
- **Social Meal Planning**: Family and group meal planning
- **Recipe Comments**: Community discussion on recipes
- **User-Generated Content**: Custom recipe submissions

### 7. Mobile & Accessibility Features
- **Responsive Design**: Mobile-first responsive web application
- **Progressive Web App**: PWA capabilities for mobile installation
- **Touch-Friendly Interface**: Optimized for touch devices
- **Accessibility**: WCAG 2.1 AA compliance
- **Offline Functionality**: Basic offline recipe viewing (planned)
- **Voice Integration**: Voice commands for hands-free cooking (planned)

### 8. Analytics & Insights Features
- **Usage Analytics**: User behavior tracking and insights
- **Nutritional Tracking**: Track nutritional intake over time (planned)
- **Meal Planning Insights**: AI-powered meal planning analytics
- **Recipe Performance**: Track recipe popularity and success rates
- **User Feedback**: Comprehensive feedback collection system

---

## Implementation Details

### AI/ML Implementation

#### 1. Vector Database Architecture
```python
# Recipe Embedding Generation
class RecipeEmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer("all-mpnet-base-v2")
        # 768-dimensional embeddings optimized for semantic similarity
    
    def generate_recipe_embedding(self, recipe_summary: str) -> List[float]:
        # Generate embeddings from AI-generated recipe summaries
        # Summaries provide better semantic representation than raw recipes
        embedding = self.model.encode(recipe_summary, convert_to_tensor=False)
        return embedding.tolist()

# Collection Strategy
COLLECTIONS_CONFIG = {
    "desserts-sweets": {
        "description": "All sweet treats and desserts",
        "estimated_count": 2465,
        "search_weight": 1.2  # Higher weight for dessert searches
    },
    "protein-mains": {
        "description": "Meat, poultry, seafood main dishes", 
        "estimated_count": 1379,
        "search_weight": 1.0
    }
    # ... 8 total collections
}
```

#### 2. RAG Implementation Details
```python
# Retrieval-Augmented Generation Pipeline
class RAGPipeline:
    async def process_meal_request(self, user_input: str, user_id: int):
        # 1. Conversation Analysis
        context = await self.analyze_conversation_context(user_input)
        
        # 2. Query Generation for Each Collection
        collection_queries = {}
        for collection in AVAILABLE_COLLECTIONS:
            queries = await self.generate_collection_queries(
                context, collection
            )
            collection_queries[collection] = queries
        
        # 3. Vector Retrieval
        retrieved_recipes = await self.search_multiple_collections(
            collection_queries, results_per_query=3
        )
        
        # 4. Context Assembly
        assembled_context = self.assemble_context(
            user_preferences=context,
            retrieved_recipes=retrieved_recipes,
            user_history=await self.get_user_history(user_id)
        )
        
        # 5. LLM Generation
        meal_plan = await self.generate_meal_plan(assembled_context)
        
        return meal_plan
```

#### 3. Google Gemini Integration
```python
# LLM Service for Meal Plan Generation
class GeminiLLMService:
    def __init__(self):
        self.client = GoogleGenerativeAI(api_key=GOOGLE_API_KEY)
        self.model_name = "gemini-2.5-flash"
    
    async def generate_meal_plan(self, context: dict) -> dict:
        prompt = self.construct_meal_planning_prompt(context)
        
        response = await self.client.generate_content(
            model=self.model_name,
            contents=prompt,
            generation_config={
                "temperature": 0.7,  # Balanced creativity
                "max_output_tokens": 2048,
                "response_mime_type": "application/json"
            }
        )
        
        return json.loads(response.text)
    
    def construct_meal_planning_prompt(self, context: dict) -> str:
        return f"""
        Create a {context['days']}-day meal plan for a user with the following:
        
        Dietary Restrictions: {context['dietary_restrictions']}
        Allergies: {context['allergies']}
        Cuisine Preferences: {context['cuisine_preferences']}
        Available Recipes: {context['retrieved_recipes']}
        
        Generate a JSON response with detailed meal assignments...
        """
```

### Database Optimization

#### 1. PostgreSQL Performance
```sql
-- Advanced indexing for recipe search
CREATE INDEX CONCURRENTLY idx_recipes_gin_search 
ON recipes USING gin(to_tsvector('english', name || ' ' || array_to_string(ingredients, ' ')));

-- Partial indexes for common queries
CREATE INDEX idx_recipes_dietary_tags 
ON recipes USING gin(dietary_tags) 
WHERE dietary_tags IS NOT NULL;

-- Composite indexes for meal planning
CREATE INDEX idx_meal_plans_user_date 
ON meal_plans(user_id, created_at DESC);
```

#### 2. Qdrant Vector Optimization
```python
# Optimized vector search configuration
class QdrantOptimization:
    COLLECTION_CONFIG = {
        "vectors": {
            "size": 768,
            "distance": "Cosine",  # Optimal for semantic similarity
            "on_disk": True        # Store vectors on disk for large datasets
        },
        "optimizers_config": {
            "deleted_threshold": 0.2,
            "vacuum_min_vector_number": 1000,
            "default_segment_number": 2
        },
        "quantization_config": {
            "scalar": {
                "type": "int8",    # 8-bit quantization for speed
                "quantile": 0.99
            }
        }
    }
```

### Security Implementation

#### 1. Authentication Security
```python
# JWT Security Configuration
class SecurityConfig:
    SECRET_KEY = os.getenv("JWT_SECRET", "secure-random-key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # Password hashing
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    @classmethod
    def verify_password(cls, plain_password: str, hashed_password: str) -> bool:
        return cls.pwd_context.verify(plain_password, hashed_password)
    
    @classmethod
    def get_password_hash(cls, password: str) -> str:
        return cls.pwd_context.hash(password)
```

#### 2. API Security
```python
# Request validation and rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/recipes/search")
@limiter.limit("10/minute")  # Rate limiting
async def search_recipes(
    request: Request,
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user)  # JWT validation
):
    # Input validation with Pydantic
    # SQL injection prevention with parameterized queries
    # XSS prevention with response sanitization
```

### Performance Optimizations

#### 1. Caching Strategy
```python
# Redis caching for frequent queries
import redis
from functools import wraps

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_recipe_search(expire_time=300):  # 5 minutes
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"recipe_search:{hash(str(args) + str(kwargs))}"
            
            # Check cache first
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire_time, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### 2. Async Processing
```python
# Async processing for heavy operations
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncProcessor:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def process_embeddings_batch(self, recipes: List[Recipe]):
        # Process embeddings in parallel
        tasks = [
            asyncio.create_task(self.generate_embedding(recipe))
            for recipe in recipes
        ]
        
        embeddings = await asyncio.gather(*tasks, return_exceptions=True)
        return [e for e in embeddings if not isinstance(e, Exception)]
```

### Monitoring & Observability

#### 1. Health Checks
```python
# Comprehensive health checking
@app.get("/health")
async def health_check():
    health_status = {
        "service": "recipe-service",
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "checks": {}
    }
    
    # Database connectivity
    try:
        await database.execute("SELECT 1")
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    # Qdrant connectivity
    try:
        qdrant_client.get_collections()
        health_status["checks"]["qdrant"] = "healthy"
    except Exception as e:
        health_status["checks"]["qdrant"] = f"unhealthy: {e}"
        health_status["status"] = "degraded"
    
    return health_status
```

#### 2. Logging Strategy
```python
# Structured logging with correlation IDs
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    
    with structlog.contextvars.bound_contextvars(
        correlation_id=correlation_id,
        endpoint=request.url.path,
        method=request.method
    ):
        start_time = time.time()
        logger.info("Request started")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info("Request completed", 
                   status_code=response.status_code,
                   process_time=process_time)
        
        response.headers["X-Correlation-ID"] = correlation_id
        return response
```

---

## Technical Stack

### Frontend Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.2.0 | UI library with hooks and concurrent features |
| TypeScript | 5.0.4 | Type-safe JavaScript development |
| Vite | 4.3.5 | Fast build tool and development server |
| Material-UI | 5.13.0 | Google Material Design components |
| React Router | 6.11.1 | Client-side routing |
| Axios | 1.4.0 | HTTP client for API communication |
| Formik | 2.2.9 | Form handling and validation |
| Yup | 1.1.1 | Schema validation |
| React Beautiful DnD | 13.1.1 | Drag and drop functionality |
| JWT Decode | 3.1.2 | JWT token handling |

### Backend Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.100.0 | Modern Python web framework |
| Uvicorn | 0.23.2 | ASGI server for async operations |
| SQLAlchemy | 2.0.19 | Advanced ORM with async support |
| Pydantic | Latest | Data validation and serialization |
| psycopg2-binary | 2.9.7 | PostgreSQL database adapter |
| python-dotenv | 1.0.0 | Environment variable management |

### AI/ML Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| Google Gemini | API | Large Language Model for meal planning |
| SentenceTransformers | 2.3.1 | Text embedding generation |
| Qdrant Client | 1.4.0 | Vector database client |
| Transformers | 4.32.1 | Hugging Face transformer models |
| PyTorch | 2.0.1 | Machine learning framework |
| NumPy | 1.24.4 | Numerical computing |
| Pandas | 2.0.3 | Data manipulation and analysis |

### Database Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 15 | Primary database with pgvector extension |
| MySQL | 8.0 | User authentication and preferences |
| Qdrant | Latest | Specialized vector database |

### Infrastructure Stack
| Technology | Version | Purpose |
|------------|---------|---------|
| Docker | Latest | Application containerization |
| Docker Compose | Latest | Multi-container orchestration |
| NGINX | Latest | Web server and reverse proxy |
| Express.js | Latest | API Gateway implementation |

### Development Tools
| Technology | Purpose |
|------------|---------|
| Git | Version control |
| GitHub | Repository hosting |
| VS Code | IDE with extensions |
| Postman | API testing |
| pgAdmin | PostgreSQL administration |
| Redis | Caching (planned) |

---

## AI/ML Components

### 1. Large Language Model Integration
**Google Gemini 2.5 Flash**
- **Purpose**: Meal plan generation and conversation analysis
- **Features**: 
  - Natural language understanding for user preferences
  - Structured JSON response generation
  - Context-aware meal planning
  - Dietary restriction compliance
  - Creative recipe combinations

### 2. Vector Embeddings
**SentenceTransformers (all-mpnet-base-v2)**
- **Model Size**: 768-dimensional embeddings
- **Training**: Pre-trained on large corpus of text data
- **Performance**: State-of-the-art semantic similarity
- **Use Cases**:
  - Recipe semantic search
  - Ingredient similarity matching
  - Cuisine classification
  - User preference matching

### 3. Recipe Classification System
**Function-Based Classification**
- **Method**: Ingredient and cooking method analysis
- **Categories**: 8 semantic recipe collections
- **Accuracy**: High confidence scores for each classification
- **Benefits**: Better search relevance than cuisine-based classification

### 4. Vector Database Architecture
**Qdrant Vector Database**
- **Storage**: 9,366 recipe embeddings across 8 collections
- **Search**: Cosine similarity for semantic matching
- **Performance**: Sub-second search across entire recipe database
- **Scalability**: Horizontal scaling for large datasets

### 5. RAG (Retrieval-Augmented Generation)
**Hybrid AI Approach**
- **Retrieval**: Vector search for relevant recipes
- **Augmentation**: Context assembly with user preferences
- **Generation**: LLM-powered meal plan creation
- **Benefits**: Factual accuracy with creative generation

---

## Deployment & Infrastructure

### Container Architecture
```yaml
# docker-compose.yml structure
services:
  frontend:          # React app (Port 80)
  api-gateway:       # Express.js (Port 3000)
  user-service:      # FastAPI (Port 8000)
  recipe-service:    # FastAPI (Port 8001)
  meal-planner:      # FastAPI (Port 8002)
  notification:      # FastAPI (Port 8003)
  mysql:            # MySQL 8.0 (Port 13306)
  postgres:         # PostgreSQL 15 (Port 15432)
  qdrant:           # Qdrant Vector DB (Port 6333)
```

### Performance Optimizations
- **Multi-stage Docker builds** for smaller images
- **Shared volume caching** for dependencies
- **BuildKit** for parallel build optimization
- **Health checks** for all services
- **Graceful shutdown** handling

### Scalability Considerations
- **Horizontal scaling** for individual microservices
- **Database connection pooling** for performance
- **Caching strategies** for frequent queries
- **Load balancing** capabilities (planned)
- **CDN integration** for static assets (planned)

### Security Measures
- **JWT authentication** with token refresh
- **CORS configuration** for cross-origin requests
- **Input validation** with Pydantic models
- **SQL injection prevention** with parameterized queries
- **Rate limiting** for API endpoints
- **Environment variable** security for secrets

---

## Conclusion

MealMateAI represents a sophisticated implementation of modern software architecture principles combined with cutting-edge AI technologies. The system successfully integrates:

- **Microservices Architecture** for scalability and maintainability
- **Advanced AI/ML** for intelligent meal planning and recipe recommendations
- **Modern Web Technologies** for exceptional user experience
- **Robust Database Design** for data integrity and performance
- **Comprehensive Security** for user data protection

The project demonstrates practical application of:
- **Vector Databases** for semantic search
- **Large Language Models** for natural language processing
- **RAG Architecture** for knowledge-grounded AI responses
- **Containerized Deployment** for operational excellence
- **API-First Design** for system integration

This comprehensive system provides a solid foundation for future enhancements and demonstrates enterprise-grade software development practices with innovative AI integration.

---

*Document prepared for project review and technical documentation purposes.*
*Last updated: August 20, 2025*