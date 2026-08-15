# User schemas for request/response validation
# UserCreate, UserLogin, UserResponse schemas
"""
Pydantic schemas for User-related request/response payloads.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for creating a user (from Google OAuth callback)."""
    google_id: str
    email: EmailStr
    name: str


class UserResponse(BaseModel):
    """Schema for returning user data to the client."""
    id: int
    google_id: str
    email: str
    name: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}