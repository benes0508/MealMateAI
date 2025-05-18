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
│  │    MySQL Database  │  │    Recipe Database │  │   Meal Plans DB    │  │  Notification DB   │         │
│  │    (User data)     │  │    (Future)        │  │   (Future)         │  │  (Future)          │         │
│  │                    │  │                    │  │                    │  │                    │         │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘  └────────────────────┘         │
│                                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                                                                                            
┌──────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                          │
│                                          EXTERNAL SERVICES                                               │
│                                                                                                          │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐          │
│  │                    │  │                    │  │                    │  │                    │          │
│  │   Email Service    │  │   Recipe APIs      │  │   Cloud Storage    │  │   Analytics        │          │
│  │   (SMTP)           │  │   (Future)         │  │   (AWS S3)         │  │   (Future)         │          │
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

2. **Recipe Service API** (Planned):
   - Will expose: `/api/recipes/` endpoints
   - Will provide:
     - Recipe storage and retrieval
     - Recipe search (by ingredients, cuisine, dietary restrictions)
     - Recipe recommendations based on user preferences

3. **Meal Planner Service API** (Planned):
   - Will expose: `/api/meal-plans/` endpoints
   - Will provide:
     - Weekly meal plan generation
     - Meal plan customization
     - Shopping list generation

4. **Notification Service API** (Planned):
   - Will expose: `/api/notifications/` endpoints
   - Will provide:
     - Email notification sending
     - Notification preferences management
     - Scheduled reminders

### Inter-Service Dependencies

```
                           get user prefs
        ____________________________________________________________
        |                                                           |
┌─────────────────┐          ┌─────────────────┐          ┌─────────────────┐
│                 │          │                 │          │                 │
│   User Service  │          |  Recipe Service │◄─────────┤  Meal Planner   │
│                 │          │                 │  Gets    │     Service     │
│                 │          │                 │  recipe  │                 │
└────────▲────────┘          └─────────────────┘  data    └─────────▲───────┘
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

## Data Storage

Each microservice has its own dedicated database:

1. **User Service Database (MySQL)**:
   - `users` table: Stores user account information
   - Columns: id, username, email, hashed_password, full_name, is_active, is_admin, created_at, updated_at

2. **Recipe Service Database (Planned)**:
   - Will store recipes, ingredients, and recipe metadata
   - Will include tables for recipes, ingredients, and recipe-ingredient relationships

3. **Meal Planner Service Database (Planned)**:
   - Will store meal plans, user-meal plan associations
   - Will include tables for meal plans, meal schedules

4. **Notification Service Database (Planned)**:
   - Will store notification templates and scheduled notifications
   - Will include tables for notification history and preferences

## Deployment Architecture

All services are containerized using Docker and orchestrated using Docker Compose:

- Each microservice is defined in its own Dockerfile
- Services are networked together via Docker Compose
- Persistent data is stored in Docker volumes
- Environment configuration is managed via .env files

## Authentication and Authorization

- JWT-based authentication system
- Tokens issued by User Service
- Token validation performed by API Gateway
- Role-based authorization for administrative functions

## Future Expansion

The system is designed to easily accommodate future services and capabilities:

1. **Machine Learning Service** for advanced recipe recommendations
2. **Shopping List Service** for grocery price comparison and delivery scheduling
3. **Social Service** for community features like recipe sharing and commenting
4. **Voice Assistant Integration** for hands-free cooking instructions