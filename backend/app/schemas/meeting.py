from datetime import datetime
from pydantic import BaseModel

from app.models.meeting import MeetingStatus


class MeetingCreate(BaseModel):
    """Payload for creating a new meeting."""
    title: str
    meeting_url: str
    language: str = "en"  # ← Added
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
    language: str  # ← Added
    status: MeetingStatus
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    notes: str | None

    model_config = {"from_attributes": True}


class MeetingListResponse(BaseModel):
    """Schema for listing all meetings."""
    meetings: list[MeetingResponse]
    total: int