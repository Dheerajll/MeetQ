"""
Pydantic schemas for LMA token management.
"""
from datetime import datetime
from pydantic import BaseModel


class LMATokenCreate(BaseModel):
    """Payload for generating a new LMA token."""
    device_name: str | None = None


class LMATokenResponse(BaseModel):
    """Schema for returning token info (token value masked after first view)."""
    id: int
    user_id: int
    token: str
    device_name: str | None
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}