# Summary schemas for request/response validation
# SummaryResponse, ActionItem schemas
"""
Pydantic schemas for meeting summaries.
"""

from datetime import datetime
from pydantic import BaseModel

from app.models.meeting import MeetingStatus


class SummaryResponse(BaseModel):
    """A single meeting summary."""
    meeting_id: int
    meeting_type: str
    overview: str
    key_topics: list[str]
    decisions: list[str]
    action_items: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class MeetingWithSummary(BaseModel):
    """Meeting + its summary, shaped for the dashboard list."""
    id: int
    title: str
    meeting_url: str
    language: str
    status: MeetingStatus
    started_at: datetime | None
    created_at: datetime

    # Summary fields (None if not yet processed)
    meeting_type: str | None = None
    overview: str | None = None
    key_topics: list[str] = []
    decisions: list[str] = []
    action_items: list[str] = []

    model_config = {"from_attributes": True}