# MealMateAI Architecture

This document describes the architecture of the MealMateAI system, including all components, databases, and their communication patterns.

## System Overview

MealMateAI is built using a microservices architecture with the following key components:

1. **Frontend**: React application providing the user interface
2. **API Gateway**: Express.js service that routes requests to the appropriate microservice
3. **Microservices**:
   - User Service: Manages user accounts, authentication, and preferences
   - Recipe Service: Stores and retrieves recipes
   - Meal Planner Service: Generates personalized meal plans
   - Notification Service: Sends email notifications and reminders
4. **Databases**: Each service has its own dedicated database

## Block Diagram

```
┌───────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                           │
│                                           CLIENT LAYER                                                    │
│                                                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐                   │
│  │                  │  │                  │  │                  │  │                  │                   │
│  │   Web Browser    │  │  Mobile Browser  │  │  iOS App         │  │  Android App     │                   │
│  │                  │  │                  │  │  (Future)        │  │  (Future)        │                   │
│  │                  │  │                  │  │                  │  │                  │                   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘                   │
│           │                     │                     │                     │                             │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────────────┘
            │                     │                     │                     │                              
            │  HTTPS/WSS          │  HTTPS/WSS          │  HTTPS              │  HTTPS                      
            │                     │                     │                     │                              
┌───────────┼─────────────────────┼─────────────────────┼─────────────────────┼─────────────────────────────┐
│           │                     │                     │                     │                             │
│           ▼                     ▼                     ▼                     ▼                             │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐                    │
│  │                                                                                  │                    │
│  │                                FRONTEND (React)                                  │                    │
│  │                                                                                  │                    │
│  └───────────────────────────────────────┬──────────────────────────────────────────┘                    │
│                                          │                                                               │
│                                          │  HTTPS                                                        │
│                                          │                                                               │
│                                          ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────────────────────┐                    │
│  │                                                                                  │                    │
│  │                             API GATEWAY (Express.js)                             │                    │
│  │                                                                                  │                    │
│  │                Authentication & Authorization, Request Routing                    │                    │
│  │                                                                                  │                    │
│  └─────────────┬────────────────────┬───────────────────────┬─────────────────────┬─┘                    │
│                │                    │                       │                     │                      │
│                │                    │                       │                     │                      │
│                │                    │                       │                     │                      │
│                ▼                    ▼                       ▼                     ▼                      │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐         │
│  │                    │  │                    │  │                    │  │                    │         │
│  │   User Service     │  │   Recipe Service   │  │  Meal-Planner      │  │   Notification     │         │
│  │   (FastAPI)        │  │   (FastAPI)        │  │  Service (FastAPI) │  │   Service (FastAPI)│         │
│  │                    │  │                    │  │                    │  │                    │         │
│  └─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘  └─────────┬──────────┘         │
│            │                       │                       │                       │                     │
│            │                       │                       │                       │                     │
│            │                       │                       │                       │                     │
│            ▼                       ▼                       ▼                       ▼                     │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐         │
│  │                    │  │                    │  │                    │  │                    │         │
│  │    MySQL Database  │  │   PostgreSQL DB    │  │   PostgreSQL DB    │  │  Notification DB   │         │
│  │    (User data)     │  │   (Recipe data)    │  │   (Meal Plans)     │  │  (Future)          │         │
│  │                    │  │                    │  │                    │  │                    │         │
│  └────────────────────┘  └─────────┬──────────┘  └────────────────────┘  └────────────────────┘         │
│                                    │                                                                     │
│                                    │                                                                     │
│                                    ▼                                                                     │
│                          ┌────────────────────┐                                                          │
│                          │                    │                                                          │
│                          │  Qdrant Vector DB  │                                                          │
│                          │ (Recipe Embeddings)│                                                          │
│                          │                    │                                                          │
│                          └────────────────────┘                                                          │
│                                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                                                            
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                          │
│                                          EXTERNAL SERVICES                                               │
│                                                                                                          │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐          │
│  │                    │  │                    │  │                    │  │                    │          │
│  │   Email Service    │  │  Google Gemini API │  │   Cloud Storage    │  │   Analytics        │          │
│  │   (SMTP)           │  │     (LLM)          │  │   (AWS S3)         │  │   (Future)         │          │
│  │                    │  │                    │  │                    │  │                    │          │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘  └────────────────────┘          │ 
│                                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Communication Flow and API Patterns

### Client-to-Backend Communication
- Frontend communicates with API Gateway via RESTful HTTP requests
- API Gateway provides authentication, authorization, and routes requests to appropriate microservices

### Microservice-to-Microservice Communication
1. **User Service API**:
   - Exposes: `/api/users/` endpoints for CRUD operations on users
   - Current Endpoints:
     - `GET /api/users/`: List all users
     - `POST /api/users/`: Create new user
     - `GET /api/users/{user_id}`: Get user details
     - `PUT /api/users/{user_id}`: Update user
     - `DELETE /api/users/{user_id}`: Delete user
     - `POST /api/users/login`: Authenticate user

2. **Recipe Service API**:
   - Exposes: `/api/recipes/` endpoints (via API Gateway)
   - Current Endpoints:
     - `GET /`: List all recipes from CSV
     - `GET /csv`: Get recipes from Kaggle CSV file
     - `GET /search`: Search recipes by query parameters
     - `GET /health`: Health check endpoint
   - Features:
     - Recipe storage and retrieval from PostgreSQL
     - Vector search using Qdrant for semantic recipe matching
     - CSV recipe import from Kaggle dataset
     - Recipe embeddings generation for AI-powered search

3. **Meal Planner Service API**:
   - Exposes: `/api/meal-plans/` endpoints (via API Gateway)
   - Current Endpoints:
     - `POST /`: Create basic meal plan
     - `POST /rag`: Create AI-powered meal plan using RAG (Retrieval-Augmented Generation)
     - `GET /{meal_plan_id}`: Get specific meal plan
     - `PUT /{meal_plan_id}/move-meal`: Move meals between days
     - `PUT /{meal_plan_id}/swap-days`: Swap entire days
     - `GET /{meal_plan_id}/grocery-list`: Generate shopping list
     - `GET /health`: Health check endpoint
   - Features:
     - AI-powered meal plan generation using Google Gemini LLM
     - RAG-based recipe recommendations using vector search
     - Interactive meal plan modifications
     - Automated grocery list generation
     - User preference integration

4. **Notification Service API** (Basic Implementation):
   - Exposes: `/api/notifications/` endpoints (via API Gateway)
   - Current Features:
     - Basic notification framework
     - Email notification capabilities (planned)
     - User notification preferences (planned)

### Inter-Service Dependencies

```
                           get user prefs
        ____________________________________________________________
        |                                                           |
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│                 │          │                 │          │                 │
│   User Service  │          |  Recipe Service │◄─────────┤  Meal Planner   │
│                 │          │                 │  Vector  │     Service     │
│                 │          │  + Qdrant DB    │  search  │   + Gemini AI   │
└────────▲────────┘          └─────────────────┘          └─────────▲───────┘
         │                                                          │        
         │                                                          │        
         │                                                          │        
         │                          ┌─────────────────┐             │        
         │                          │                 │             │        
         └──────────────────────────┤  Notification   │◄────────────┘        
                        Gets user   │     Service     │    Gets meal plan    
                        contact info│                 │    schedules         
                                    └─────────────────┘                      
```

## Advanced Features

### RAG-Powered Meal Planning

The system implements a sophisticated Retrieval-Augmented Generation (RAG) workflow for intelligent meal planning:

1. **Vector Search**: User queries are converted to embeddings and matched against recipe embeddings in Qdrant
2. **Context Assembly**: Retrieved recipes are combined with user preferences and dietary restrictions
3. **LLM Generation**: Google Gemini API generates personalized meal plans based on the assembled context
4. **Interactive Refinement**: Users can provide feedback and iterate on meal plans

### Database Architecture by Service

**User Service (MySQL):**
- User accounts, authentication, and basic preferences
- Optimized for transactional operations and user sessions

**Recipe & Meal Planner Services (PostgreSQL):**
- Recipe storage with full-text search capabilities
- Meal plan storage with complex relational data
- Supports JSON fields for flexible recipe metadata

**Recipe Embeddings (Qdrant Vector Database):**
- High-dimensional recipe embeddings for semantic search
- Enables AI-powered recipe recommendations
- Supports similarity search and filtering

## Data Storage

Each microservice has its own dedicated database with specific optimizations:

1. **User Service Database (MySQL)**:
   - `users` table: Stores user account information and basic preferences
   - Columns: id, username, email, hashed_password, full_name, is_active, is_admin, created_at, updated_at
   - Additional preference columns: dietary_restrictions, allergies, cuisine_preferences, disliked_ingredients

2. **Recipe Service Database (PostgreSQL)**:
   - `recipes` table: Stores recipe information with full metadata
   - Supports complex recipe data including ingredients, instructions, and nutritional information
   - Integrated with Qdrant vector database for semantic search capabilities

3. **Meal Planner Service Database (PostgreSQL)**:
   - `meal_plans` table: Stores meal plan metadata (id, user_id, plan_name, days, meals_per_day, plan_explanation)
   - `meal_plan_recipes` table: Associates recipes with specific days and meal types
   - `user_preferences` table: Detailed user preferences for meal planning
   - Supports complex meal planning algorithms and grocery list generation

4. **Qdrant Vector Database**:
   - Stores high-dimensional embeddings of recipe descriptions and ingredients
   - Enables semantic similarity search for recipe recommendations
   - Supports filtering based on dietary restrictions and preferences

5. **Notification Service Database (Future)**:
   - Will store notification templates and scheduled notifications
   - Will include tables for notification history and user preferences

## Deployment Architecture

All services are containerized using Docker and orchestrated using Docker Compose:

- **Frontend Container**: React application served via Nginx (Port 80)
- **API Gateway Container**: Express.js server (Port 3000)
- **User Service Container**: FastAPI application (Port 8000) with MySQL database
- **Recipe Service Container**: FastAPI application (Port 8001) with PostgreSQL database
- **Meal Planner Service Container**: FastAPI application (Port 8002) with PostgreSQL database
- **Notification Service Container**: FastAPI application (Port 8003) - basic implementation
- **MySQL Database Container**: User data storage (Port 13306)
- **PostgreSQL Database Container**: Recipe and meal plan data (Port 15432)
- **Qdrant Vector Database Container**: Recipe embeddings (Port 6333)

### Container Communication:
- Services communicate via Docker network using container names
- Persistent data stored in Docker volumes
- Environment configuration managed via .env files and docker-compose.yml
- Health checks implemented for all services

### External Dependencies:
- **Google Gemini API**: For LLM-powered meal plan generation
- **SMTP Server**: For email notifications (planned)
- **AWS S3**: For image storage (planned)

## Authentication and Authorization

- JWT-based authentication system
- Tokens issued by User Service
- Token validation performed by API Gateway
- Role-based authorization for administrative functions

## Future Expansion

The system is designed to easily accommodate future services and capabilities:

1. **Enhanced AI Features**:
   - Advanced recipe recommendation algorithms using collaborative filtering
   - Nutritional analysis and optimization
   - Personalized cooking instruction generation

2. **Shopping and Logistics**:
   - **Shopping List Service** for grocery price comparison and delivery integration
   - **Pantry Management Service** for inventory tracking and expiration alerts
   - Integration with grocery delivery APIs

3. **Social and Community Features**:
   - **Social Service** for community features like recipe sharing and rating
   - User-generated recipe content and meal plan sharing
   - Social meal planning for families and groups

4. **Mobile and Voice Integration**:
   - **Voice Assistant Integration** for hands-free cooking instructions
   - Native mobile apps for iOS and Android
   - Offline functionality for key features

5. **Analytics and Insights**:
   - **Analytics Service** for usage patterns and meal planning insights
   - Nutritional tracking and health goal integration
   - Predictive meal planning based on user behavior

## Technology Highlights

- **Microservices Architecture**: Independent, scalable services
- **AI-Powered**: Uses Google Gemini LLM for intelligent meal planning
- **Vector Search**: Qdrant database for semantic recipe matching
- **RAG Implementation**: Retrieval-Augmented Generation for contextual responses
- **Modern Tech Stack**: FastAPI, React, PostgreSQL, MySQL, Docker
- **API-First Design**: RESTful APIs with comprehensive documentation

## Detailed Architecture Diagrams

For more detailed interactive diagrams and visual representations of the system architecture, see:

- **[Architecture Diagrams](docs/architecture-diagram.md)**: Contains Mermaid diagrams for:
  - System Architecture Overview
  - Component Communication Flow
  - Database Schema Relationships
  - Deployment Architecture
  - RAG Meal Planning Workflow
  - Microservices Communication Flow

These diagrams can be viewed directly in GitHub or pasted into [Mermaid Live Editor](https://mermaid.live/) for interactive viewing and editing.