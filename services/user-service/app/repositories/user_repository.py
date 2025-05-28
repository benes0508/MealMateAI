from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
import json
import logging
from app.models.models import User
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Set up logging
logger = logging.getLogger("user_repository")
logger.setLevel(logging.DEBUG)

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def create_user(self, email: str, username: str, password: str, full_name: str = None,
                   allergies: List[str] = None, disliked_ingredients: List[str] = None,
                   preferred_cuisines: List[str] = None, preferences: Dict = None) -> User:
        hashed_password = pwd_context.hash(password)
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            allergies=allergies or [],
            disliked_ingredients=disliked_ingredients or [],
            preferred_cuisines=preferred_cuisines or [],
            preferences=preferences or {}
        )
        
        try:
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError:
            self.db.rollback()
            raise ValueError("User with this email or username already exists")
    
    def _ensure_json_serializable(self, value: Any) -> Any:
        """Ensure that a value is JSON serializable for MySQL JSON columns"""
        if value is None:
            return value
            
        try:
            # Test if it can be serialized
            json.dumps(value)
            return value
        except (TypeError, OverflowError) as e:
            logger.error(f"Value is not JSON serializable: {e}")
            # Try to convert it to a string representation
            return str(value)
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        try:
            # Process special fields that need JSON serialization    
            json_fields = ["allergies", "disliked_ingredients", "preferred_cuisines", "preferences"]
            
            for key, value in user_data.items():
                if key == 'password':
                    user.hashed_password = pwd_context.hash(value)
                elif key in json_fields:
                    # Ensure the value is JSON serializable
                    logger.debug(f"Processing JSON field {key} with value: {value}")
                    processed_value = self._ensure_json_serializable(value)
                    setattr(user, key, processed_value)
                else:
                    setattr(user, key, value)
                    
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error updating user {user_id}: {str(e)}")
            raise e
    
    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
            
        self.db.delete(user)
        self.db.commit()
        return True
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)