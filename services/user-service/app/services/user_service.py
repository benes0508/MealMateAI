from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.models.schemas import UserCreate, UserUpdate
import logging
import jwt
from datetime import datetime, timedelta

# Set up logging
logger = logging.getLogger("user_service")
logger.setLevel(logging.DEBUG)

# JWT Configuration - moved from controller
JWT_SECRET_KEY = "your-secret-key-for-development-only"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = 1440  # 24 hours

class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
    
    def get_all_users(self, skip: int = 0, limit: int = 100):
        return self.repository.get_all_users(skip, limit)
    
    def get_user_by_id(self, user_id: int):
        return self.repository.get_user_by_id(user_id)
    
    def get_user_by_email(self, email: str):
        return self.repository.get_user_by_email(email)
    
    def get_user_by_username(self, username: str):
        return self.repository.get_user_by_username(username)
    
    def create_user(self, user_data: UserCreate):
        # Check if user already exists
        if self.repository.get_user_by_email(user_data.email):
            raise ValueError(f"User with email {user_data.email} already exists")
            
        if self.repository.get_user_by_username(user_data.username):
            raise ValueError(f"User with username {user_data.username} already exists")
            
        return self.repository.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
            allergies=user_data.allergies,
            disliked_ingredients=user_data.disliked_ingredients,
            preferred_cuisines=user_data.preferred_cuisines,
            preferences=user_data.preferences
        )
    
    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
        # Convert Pydantic model to dict, excluding None values
        update_data = user_data.dict(exclude_unset=True)
        
        # If there are no fields to update, return None
        if not update_data:
            return None
            
        return self.repository.update_user(user_id, update_data)
    
    def update_user_preferences(self, user_id: int, 
                              allergies: Optional[List[str]] = None,
                              disliked_ingredients: Optional[List[str]] = None,
                              preferred_cuisines: Optional[List[str]] = None,
                              preferences: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        try:
            # First, verify user exists
            user = self.repository.get_user_by_id(user_id)
            if not user:
                logger.error(f"User not found for preference update: {user_id}")
                return None
                
            logger.debug(f"Updating preferences for user {user_id}:")
            logger.debug(f"- allergies: {allergies}")
            logger.debug(f"- disliked_ingredients: {disliked_ingredients}")
            logger.debug(f"- preferred_cuisines: {preferred_cuisines}")
            logger.debug(f"- preferences: {preferences}")
            
            # Build update data dictionary only with fields that are not None
            update_data = {}
            if allergies is not None:
                update_data['allergies'] = allergies
            if disliked_ingredients is not None:
                update_data['disliked_ingredients'] = disliked_ingredients
            if preferred_cuisines is not None:
                update_data['preferred_cuisines'] = preferred_cuisines
            if preferences is not None:
                update_data['preferences'] = preferences
                
            logger.debug(f"Final update data: {update_data}")
            
            # Perform the update with better error handling
            try:
                updated_user = self.repository.update_user(user_id, update_data)
                logger.info(f"Preferences updated successfully for user {user_id}")
                return updated_user
            except Exception as e:
                logger.exception(f"Repository error updating preferences: {str(e)}")
                raise Exception(f"Failed to update preferences: {str(e)}")
                
        except Exception as e:
            logger.exception(f"Error in update_user_preferences: {str(e)}")
            raise Exception(f"Error updating user preferences: {str(e)}")
    
    def delete_user(self, user_id: int) -> bool:
        return self.repository.delete_user(user_id)
        
    def authenticate_user(self, username_or_email: str, password: str):
        """Authenticate a user by username/email and password"""
        # Try to find user by email first
        user = self.repository.get_user_by_email(username_or_email)
        
        # If not found by email, try by username
        if not user:
            user = self.repository.get_user_by_username(username_or_email)
            
        # If user exists, verify password
        if not user or not self.repository.verify_password(password, user.hashed_password):
            return None
            
        return user
    
    def format_user_response(self, user) -> Dict[str, Any]:
        """Format user data for response"""
        if not user:
            return None
            
        return {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": "user",
            "createdAt": user.created_at.isoformat() if hasattr(user, 'created_at') else None,
            "updatedAt": user.updated_at.isoformat() if hasattr(user, 'updated_at') else None,
        }
    
    def create_jwt_token(self, user_data: dict) -> str:
        """Generate a JWT token with user data and expiration"""
        token_data = user_data.copy()
        
        # Add expiration time
        expires_delta = timedelta(minutes=JWT_EXPIRATION_MINUTES)
        expire = datetime.utcnow() + expires_delta
        token_data.update({"exp": expire})
        
        logger.debug(f"Creating JWT token with data: {token_data}")
        
        # Create token
        encoded_jwt = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        # Debug log the token
        logger.debug(f"Generated token: {encoded_jwt[:15]}...")
        
        return encoded_jwt