from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import schemas
from app.services.user_service import UserService

# Create router
router = APIRouter()

@router.get("/", response_model=List[schemas.UserResponse])
def get_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = UserService(db).get_all_users(skip=skip, limit=limit)
    return users

@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        return UserService(db).create_user(user)
    except ValueError as e:
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
    user = UserService(db).authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"message": "Login successful", "user": user}