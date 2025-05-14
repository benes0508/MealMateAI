# User Service Microservice

## Overview
The User Service is a core microservice of the MealMateAI platform that handles user management, authentication, and user preferences. It provides APIs for user registration, authentication, profile management, and storing dietary preferences.

## Features
- User registration and authentication
- User profile management
- Storage and retrieval of user dietary preferences
- Secure password handling with passlib
- RESTful API endpoints for user operations

## Tech Stack
- **Python 3.11**: Core programming language
- **FastAPI**: Web framework for building APIs
- **SQLAlchemy**: ORM for database operations
- **MySQL**: Database for storing user information
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization
- **Passlib**: Password hashing and verification

## System Architecture

### Block Diagram

```
┌─────────────────┐     ┌───────────────────────────────────────────────────────────────────────┐
│                 │     │                                                                       │
│    Frontend     │◄────┤                           API Gateway                                 │
│  (React App)    │     │                          (Express.js)                                 │
│                 │     │                                                                       │
└────────┬────────┘     └───────┬────────────────────┬────────────────────┬────────────────────┘
         │                      │                    │                    │                     
         │                      │                    │                    │                     
         │                      ▼                    ▼                    ▼                     
         │        ┌─────────────────────┐  ┌─────────────────────┐ ┌─────────────────────┐     
         │        │                     │  │                     │ │                     │     
         └───────►│    User Service     │  │   Recipe Service    │ │  Meal-Planner       │     
                  │    (FastAPI)        │  │   (FastAPI)         │ │  Service (FastAPI)  │     
                  │                     │  │                     │ │                     │     
                  └────────┬────────────┘  └────────┬────────────┘ └─────────┬───────────┘     
                           │                        │                        │                  
                           │                        │                        │                  
                           ▼                        ▼                        ▼                  
                  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐    
                  │                     │  │                     │  │                     │    
                  │    User Database    │  │   Recipe Database   │  │   Meal Plans DB     │    
                  │      (MySQL)        │  │     (Planned)       │  │     (Planned)       │    
                  │                     │  │                     │  │                     │    
                  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘    
                                                                                               
                                           ┌─────────────────────┐                             
                                           │                     │                             
                                           │  Notification       │                             
                                           │  Service (FastAPI)  │                             
                                           │                     │                             
                                           └─────────┬───────────┘                             
                                                     │                                          
                                                     │                                          
                                                     ▼                                          
                                           ┌─────────────────────┐                             
                                           │                     │                             
                                           │ Notification DB     │                             
                                           │    (Planned)        │                             
                                           │                     │                             
                                           └─────────────────────┘                             
```

### Communication Flow

1. **Client-to-Server Communication**:
   - The React frontend communicates with the API Gateway via RESTful HTTP requests
   - The API Gateway authenticates requests and routes them to the appropriate microservice

2. **Inter-Service Communication**:
   - **User Service** serves as an identity provider and manages user profiles
     - Exposes `/api/users/` endpoints for user management
     - Stores user data including dietary preferences in MySQL
   - **Recipe Service** (planned) will handle recipe storage and retrieval
     - Will communicate with User Service to get user preferences for personalization
   - **Meal Planner Service** (planned) will generate meal plans
     - Will communicate with Recipe Service to get recipe details
     - Will communicate with User Service to get user preferences
   - **Notification Service** (planned) will handle email notifications
     - Will communicate with User Service to get user contact information
     - Will communicate with Meal Planner Service to get scheduled meal information

3. **Data Storage**:
   - Each service maintains its own dedicated database
   - User Service: MySQL database for user information
   - Other services will have their own dedicated databases (not yet implemented)

4. **Authentication Flow**:
   - Authentication happens via the User Service
   - JWT tokens are issued to authenticated clients
   - API Gateway validates tokens for protected routes

## API Endpoints

### User Management
- `GET /api/users/`: Get a list of all users
- `GET /api/users/{user_id}`: Get details of a specific user
- `POST /api/users/`: Create a new user
- `PUT /api/users/{user_id}`: Update user information
- `DELETE /api/users/{user_id}`: Delete a user

## Setup and Installation

### Prerequisites
- Docker and Docker Compose (for Docker-based setup)
- Python 3.11+ (for local development)

### Environment Variables
The service uses the following environment variables:
- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT token generation
- `ALGORITHM`: Algorithm for JWT token
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time

### Running with Docker
The service can be run as part of the entire MealMateAI platform:

```bash
# From the root directory of MealMateAI
docker-compose up --build
```

To run only the user service and its dependencies:

```bash
# From the root directory of MealMateAI
docker-compose up --build user-service mysql
```

### Running Locally Without Docker
For easy local development without Docker, use the provided script:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service with SQLite (easiest for local development)
python run_local.py

# Or run with MySQL if you have a local MySQL server
python run_local.py --db mysql
```

This will start the service on http://localhost:8000 with API documentation available at http://localhost:8000/docs.

The local development script (`run_local.py`) automatically:
1. Sets up environment variables
2. Configures the database (SQLite by default for easy local development)
3. Starts the FastAPI server with hot-reload enabled

### Local Development Setup
For manual local development setup:

```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the service
cd app
uvicorn main:app --reload
```

## Testing
The service includes API tests to verify functionality:

```bash
# Make sure the service is running
cd tests
python test_user_api.py
```

See the [tests README](tests/README.md) for more details.

## Database Schema

### Users Table
- `id`: Unique identifier
- `username`: User's unique username
- `name`: User's full name
- `email`: User's email address
- `hashed_password`: Securely hashed password
- `preferences`: JSON field for dietary preferences

## Integration with Other Services
The User Service integrates with:
- **Recipe Service**: For personalized recipe recommendations
- **Meal Planner Service**: For creating personalized meal plans
- **Notification Service**: For user notifications
- **API Gateway**: For routing and authentication

## Contributing
To contribute to this service:
1. Follow the project's coding standards
2. Write tests for new features
3. Ensure all tests pass before submitting changes
4. Document new API endpoints or changes to existing ones

## License
Proprietary - MealMateAI © 2025