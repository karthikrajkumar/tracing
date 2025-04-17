from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: Optional[int] = Field(1, ge=1, le=5)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class Item(ItemBase):
    id: int
    is_completed: bool
    created_at: datetime
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    items: List[Item] = []

    class Config:
        orm_mode = True


class WeatherResponse(BaseModel):
    city: str
    temperature: float
    conditions: str
    humidity: float
    wind_speed: float


class ErrorResponse(BaseModel):
    detail: str
