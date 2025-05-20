from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.models.schemas import UserCreate, UserUpdate

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
        update_data = {}
        if allergies is not None:
            update_data['allergies'] = allergies
        if disliked_ingredients is not None:
            update_data['disliked_ingredients'] = disliked_ingredients
        if preferred_cuisines is not None:
            update_data['preferred_cuisines'] = preferred_cuisines
        if preferences is not None:
            update_data['preferences'] = preferences
            
        return self.repository.update_user(user_id, update_data)
    
    def delete_user(self, user_id: int) -> bool:
        return self.repository.delete_user(user_id)
        
    def authenticate_user(self, username: str, password: str):
        user = self.repository.get_user_by_username(username)
        if not user:
            return False
        
        if not self.repository.verify_password(password, user.hashed_password):
            return False
            
        return user