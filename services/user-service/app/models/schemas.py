from pydantic import BaseModel, EmailStr, Field, conlist
from typing import Optional, List, Dict
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    
class UserPreferencesUpdate(BaseModel):
    allergies: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    preferred_cuisines: Optional[List[str]] = None
    preferences: Optional[Dict] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    allergies: Optional[List[str]] = []
    disliked_ingredients: Optional[List[str]] = []
    preferred_cuisines: Optional[List[str]] = []
    preferences: Optional[Dict] = {}
    
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)
    allergies: Optional[List[str]] = None
    disliked_ingredients: Optional[List[str]] = None
    preferred_cuisines: Optional[List[str]] = None
    preferences: Optional[Dict] = None
    
class UserInDB(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    allergies: List[str] = []
    disliked_ingredients: List[str] = []
    preferred_cuisines: List[str] = []
    preferences: Dict = {}
    
    class Config:
        orm_mode = True
        from_attributes = True
        
class UserResponse(UserInDB):
    # Add 'name' field that maps to 'full_name' to match frontend expectations
    @property
    def name(self) -> Optional[str]:
        return self.full_name