from sqlalchemy.orm import Session
import time
import random
from app.database import Item, User
from app.services.user_service import get_user

def get_item(db: Session, item_id: int):
    """Get an item by ID."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.05, 0.2))
    
    return db.query(Item).filter(Item.id == item_id).first()

def get_items(db: Session, skip: int = 0, limit: int = 100):
    """Get a list of items."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    return db.query(Item).offset(skip).limit(limit).all()

def get_user_items(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get a list of items for a specific user."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Check if user exists
    user = get_user(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    return db.query(Item).filter(Item.owner_id == user_id).offset(skip).limit(limit).all()

def create_item(db: Session, user_id: int, title: str, description: str = None, priority: int = 1):
    """Create a new item for a user."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Check if user exists
    user = get_user(db, user_id)
    if not user:
        raise ValueError(f"User with ID {user_id} not found")
    
    # Create new item
    db_item = Item(
        title=title,
        description=description,
        priority=priority,
        owner_id=user_id
    )
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item

def update_item(db: Session, item_id: int, item_data: dict):
    """Update an item."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Get item
    db_item = get_item(db, item_id)
    if not db_item:
        return None
    
    # Update item data
    for key, value in item_data.items():
        if value is not None:
            setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    
    return db_item

def delete_item(db: Session, item_id: int):
    """Delete an item."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Get item
    db_item = get_item(db, item_id)
    if not db_item:
        return False
    
    # Delete item
    db.delete(db_item)
    db.commit()
    
    return True

def mark_item_completed(db: Session, item_id: int, completed: bool = True):
    """Mark an item as completed or not completed."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.2))
    
    # Get item
    db_item = get_item(db, item_id)
    if not db_item:
        return None
    
    # Update completion status
    db_item.is_completed = completed
    
    db.commit()
    db.refresh(db_item)
    
    return db_item
