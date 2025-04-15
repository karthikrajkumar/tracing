from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# Todo schemas
class TodoBase(BaseModel):
    title: str
    description: str = ""
    priority: int = Field(1, ge=1, le=5)

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)

class Todo(TodoBase):
    id: int
    completed: bool
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True

# Weather schema
class WeatherResponse(BaseModel):
    city: str
    temperature: float
    conditions: str
    humidity: int
    wind_speed: float
    timestamp: float

# Error schema
class ErrorResponse(BaseModel):
    detail: str
