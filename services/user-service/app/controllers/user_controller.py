from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import json
import jwt
from datetime import datetime, timedelta
import os
from app.database import get_db
from app.models import schemas
from app.services.user_service import UserService

# Set up logging with more detail
logger = logging.getLogger("user_controller")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

# Create router
router = APIRouter()

# JWT Configuration - HARDCODED to match API Gateway
# IMPORTANT: This is only for development. In production, use environment variables.
JWT_SECRET_KEY = "your-secret-key-for-development-only"  # MUST match API gateway's JWT_SECRET
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 1440  # 24 hours

# Log JWT configuration
logger.info(f"Using JWT secret key: {JWT_SECRET_KEY[:5]}...")
logger.info(f"Using JWT algorithm: {JWT_ALGORITHM}")

def create_jwt_token(user_data: dict) -> str:
    """Generate a JWT token with user data and expiration"""
    token_data = user_data.copy()
    
    # Add expiration time
    expires_delta = timedelta(minutes=JWT_EXPIRATION_MINUTES)
    expire = datetime.utcnow() + expires_delta
    token_data.update({"exp": expire})
    
    logger.debug(f"Creating JWT token with data: {token_data}")
    logger.debug(f"Using secret key: {JWT_SECRET_KEY[:5]}...")
    
    # Create token
    encoded_jwt = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    # Debug log the token
    logger.debug(f"Generated token: {encoded_jwt[:15]}...")
    
    return encoded_jwt

# Updated registration endpoint that doesn't rely on request.json()
@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        # Log the request
        logger.debug(f"Register endpoint called with path: {request.url.path}")
        logger.debug(f"Register endpoint headers: {request.headers}")
        
        # Read raw body to avoid middleware conflicts
        try:
            raw_body = await request.body()
            body_str = raw_body.decode('utf-8')
            logger.debug(f"Raw request body: {body_str}")
            body = json.loads(body_str)
        except Exception as e:
            logger.error(f"Error reading request body: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Could not parse request body: {str(e)}"}
            )
            
        logger.debug(f"Parsed body: {body}")
        
        # Extract required fields
        email = body.get("email")
        password = body.get("password")
        
        if not email or not password:
            logger.error("Missing required fields")
            return JSONResponse(
                status_code=400,
                content={"detail": "Email and password are required"}
            )
        
        # Create user data object
        try:
            user_data = schemas.UserCreate(
                email=email,
                username=body.get("username") or email.split('@')[0],
                password=password,
                full_name=body.get("full_name") or body.get("name", ""),
                allergies=body.get("allergies", []),
                disliked_ingredients=body.get("disliked_ingredients", []),
                preferred_cuisines=body.get("preferred_cuisines", []),
                preferences=body.get("preferences", {})
            )
        except Exception as e:
            logger.error(f"Error creating UserCreate object: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid user data: {str(e)}"}
            )
        
        # Create user
        try:
            user = UserService(db).create_user(user_data)
            logger.info(f"User successfully created with email: {user.email}")
            
            # Return success response
            user_dict = {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": "user",
                "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
                "updatedAt": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None,
            }
            
            # Generate proper JWT token
            token = create_jwt_token(user_dict)
            
            return {
                "user": user_dict,
                "token": token
            }
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Error creating user: {str(e)}"}
            )
            
    except Exception as e:
        logger.exception(f"Registration error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server error: {str(e)}"}
        )

# Also add a simplified endpoint for debugging
@router.post("/register/simple", status_code=status.HTTP_201_CREATED)
def register_simple(user_data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    """Simple registration endpoint that uses Body(...) instead of Request to avoid body reading issues"""
    try:
        logger.debug(f"Simple register endpoint called with data: {user_data}")
        
        # Extract fields from the request body
        email = user_data.get("email")
        password = user_data.get("password")
        
        if not email or not password:
            logger.error("Missing required fields")
            return JSONResponse(
                status_code=400,
                content={"detail": "Email and password are required"}
            )
        
        # Create user data object
        try:
            user_create = schemas.UserCreate(
                email=email,
                username=user_data.get("username") or email.split('@')[0],
                password=password,
                full_name=user_data.get("full_name") or user_data.get("name", ""),
                allergies=user_data.get("allergies", []),
                disliked_ingredients=user_data.get("disliked_ingredients", []),
                preferred_cuisines=user_data.get("preferred_cuisines", []),
                preferences=user_data.get("preferences", {})
            )
        except Exception as e:
            logger.error(f"Error creating UserCreate object: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Invalid user data: {str(e)}"}
            )
        
        # Create user
        try:
            user = UserService(db).create_user(user_create)
            logger.info(f"User successfully created with email: {user.email}")
            
            # Return success response
            user_dict = {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": "user",
                "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
                "updatedAt": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None,
            }
            
            # Generate proper JWT token
            token = create_jwt_token(user_dict)
            
            return {
                "user": user_dict,
                "token": token
            }
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"detail": f"Error creating user: {str(e)}"}
            )
    except Exception as e:
        logger.exception(f"Registration error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server error: {str(e)}"}
        )

# Debug endpoint to see what's coming in
@router.post("/debug", status_code=200)
async def debug_request(request: Request):
    try:
        body = await request.body()
        logger.info(f"Debug endpoint called with body: {body}")
        return {"message": "Debug endpoint called", "received": True}
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return {"error": str(e)}

@router.get("/", response_model=List[schemas.UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = UserService(db).get_all_users(skip=skip, limit=limit)
    return users

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Root POST endpoint called with user data: {user.email}")
    try:
        return UserService(db).create_user(user)
    except ValueError as e:
        logger.error(f"User creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = UserService(db).get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(user_id: int, user_data: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = UserService(db).update_user(user_id, user_data)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}/preferences", response_model=schemas.UserResponse)
def update_user_preferences(
    user_id: int,
    preferences: schemas.UserPreferencesUpdate,
    db: Session = Depends(get_db)
):
    user = UserService(db).update_user_preferences(
        user_id,
        allergies=preferences.allergies,
        disliked_ingredients=preferences.disliked_ingredients,
        preferred_cuisines=preferences.preferred_cuisines,
        preferences=preferences.preferences
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    deleted = UserService(db).delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return None

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    logger.debug(f"Login endpoint called for username: {username}")
    user = UserService(db).authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": "Login successful", "user": user}

# Add enhanced login endpoint that accepts JSON body
@router.post("/login/json", status_code=status.HTTP_200_OK)
def login_json(login_data: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    try:
        # Log the raw request data for debugging
        logger.debug(f"Login JSON endpoint called")
        logger.debug(f"Login data received: {login_data}")
        logger.debug(f"Login data type: {type(login_data)}")
        
        # Extract email/username and password from the request body
        email = login_data.get("email")
        password = login_data.get("password")
        
        logger.debug(f"Extracted email: {email}")
        logger.debug(f"Password present: {password is not None}")
        
        if not email or not password:
            logger.error(f"Missing login credentials - Email present: {email is not None}, Password present: {password is not None}")
            return JSONResponse(
                status_code=400,
                content={"detail": "Email and password are required"}
            )
        
        # First try to get user by email
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        
        # If not found by email, try by username
        if not user:
            logger.debug(f"User not found by email, trying username: {email}")
            user = user_service.get_user_by_username(email)
        
        # If user found, verify the password
        if user and user_service.repository.verify_password(password, user.hashed_password):
            logger.info(f"User successfully authenticated: {email}")
            
            # Format user data for response
            user_dict = {
                "id": user.id,
                "email": user.email,
                "name": user.full_name,
                "role": "user",  # Default role
                "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
                "updatedAt": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None,
            }
            
            # Generate proper JWT token
            token = create_jwt_token(user_dict)
            
            # Return user and token
            return {
                "user": user_dict,
                "token": token
            }
        else:
            logger.error(f"Authentication failed for email/username: {email}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Incorrect email or password"}
            )
    except Exception as e:
        logger.exception(f"Login error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server error during login: {str(e)}"}
        )