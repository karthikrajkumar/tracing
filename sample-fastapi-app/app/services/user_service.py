from sqlalchemy.orm import Session
import hashlib
import time
import random
from app.database import User

def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a stored password against a provided password."""
    return get_password_hash(plain_password) == hashed_password

def get_user(db: Session, user_id: int):
    """Get a user by ID."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.05, 0.2))
    
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """Get a user by email."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.05, 0.2))
    
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str):
    """Get a user by username."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.05, 0.2))
    
    return db.query(User).filter(User.username == username).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get a list of users."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.4))
    
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, username: str, email: str, password: str):
    """Create a new user."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Check if user already exists
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")
    
    if get_user_by_username(db, username):
        raise ValueError("Username already taken")
    
    # Create new user
    hashed_password = get_password_hash(password)
    db_user = User(username=username, email=email, hashed_password=hashed_password)
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def update_user(db: Session, user_id: int, user_data: dict):
    """Update a user."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Get user
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    # Update user data
    for key, value in user_data.items():
        if value is not None:
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    
    return db_user

def delete_user(db: Session, user_id: int):
    """Delete a user."""
    # Simulate database operation delay
    time.sleep(random.uniform(0.1, 0.3))
    
    # Get user
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    
    # Delete user
    db.delete(db_user)
    db.commit()
    
    return True
