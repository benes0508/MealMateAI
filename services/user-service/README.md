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

## API Endpoints

### User Management
- `GET /api/users/`: Get a list of all users
- `GET /api/users/{user_id}`: Get details of a specific user
- `POST /api/users/`: Create a new user
- `PUT /api/users/{user_id}`: Update user information
- `DELETE /api/users/{user_id}`: Delete a user

## Setup and Installation

### Prerequisites
- Docker and Docker Compose
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

### Local Development Setup
For local development without Docker:

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