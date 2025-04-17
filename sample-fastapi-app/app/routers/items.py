from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import Item, ItemCreate, ItemUpdate
from app.services.item_service import (
    create_item, get_item, get_items, get_user_items,
    update_item, delete_item, mark_item_completed
)

router = APIRouter(tags=["items"])

@router.post("/users/{user_id}/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item_endpoint(
    user_id: int,
    item: ItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new item for a user."""
    try:
        return create_item(
            db, 
            user_id=user_id,
            title=item.title,
            description=item.description,
            priority=item.priority
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/items/{item_id}", response_model=Item)
def get_item_endpoint(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific item by ID."""
    db_item = get_item(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    return db_item

@router.get("/items", response_model=List[Item])
def get_items_endpoint(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get a list of all items."""
    return get_items(db, skip, limit)

@router.get("/users/{user_id}/items", response_model=List[Item])
def get_user_items_endpoint(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get a list of items for a specific user."""
    try:
        return get_user_items(db, user_id, skip, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/items/{item_id}", response_model=Item)
def update_item_endpoint(
    item_id: int,
    item: ItemUpdate,
    db: Session = Depends(get_db)
):
    """Update an item."""
    # Convert Pydantic model to dict, excluding unset fields
    item_data = item.dict(exclude_unset=True)
    
    # Update item
    db_item = update_item(db, item_id, item_data)
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    
    return db_item

@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item_endpoint(
    item_id: int,
    db: Session = Depends(get_db)
):
    """Delete an item."""
    success = delete_item(db, item_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    
    return None

@router.put("/items/{item_id}/complete", response_model=Item)
def mark_item_completed_endpoint(
    item_id: int,
    completed: bool = True,
    db: Session = Depends(get_db)
):
    """Mark an item as completed or not completed."""
    db_item = mark_item_completed(db, item_id, completed)
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with ID {item_id} not found"
        )
    
    return db_item
