from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import time
import random

from app.database import get_db
from app.schemas import User, UserCreate, UserUpdate
from app.services.user_service import (
    create_user, get_user, get_users, update_user, delete_user
)
from app.services.external_service import ExternalApiService

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user_endpoint(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user."""
    try:
        return create_user(db, user.username, user.email, user.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=User)
def get_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific user by ID."""
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return db_user

@router.get("/", response_model=List[User])
def get_users_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get a list of users."""
    return get_users(db, skip, limit)

@router.put("/{user_id}", response_model=User)
def update_user_endpoint(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db)
):
    """Update a user."""
    # Convert Pydantic model to dict, excluding unset fields
    user_data = user.dict(exclude_unset=True)
    
    # Update user
    db_user = update_user(db, user_id, user_data)
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return db_user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Delete a user."""
    success = delete_user(db, user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return None

@router.get("/{user_id}/external-data")
def get_external_data(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get external data for a user."""
    # Check if user exists
    db_user = get_user(db, user_id)
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Get external data
    external_service = ExternalApiService()
    try:
        external_user = external_service.get_user_data(user_id)
        todos = external_service.get_todos(user_id)
        
        return {
            "user": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email
            },
            "external_user": external_user,
            "todos": todos
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
