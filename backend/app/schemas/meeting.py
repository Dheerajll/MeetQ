# Meeting schemas for request/response validation
# MeetingCreate, MeetingStatus, MeetingResponse schemas
"""
Pydantic schemas for Meeting-related request/response payloads.
"""
from datetime import datetime
from pydantic import BaseModel, HttpUrl

from app.models.meeting import MeetingStatus


class MeetingCreate(BaseModel):
    """Payload for creating a new meeting."""
    title: str
    meeting_url: str
    scheduled_at: datetime | None = None
    notes: str | None = None


class MeetingStatusUpdate(BaseModel):
    """Payload for updating meeting status (used by LMA)."""
    status: MeetingStatus


class MeetingResponse(BaseModel):
    """Schema for returning meeting data to the client."""
    id: int
    user_id: int
    title: str
    meeting_url: str
    status: MeetingStatus
    scheduled_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    notes: str | None

    model_config = {"from_attributes": True}