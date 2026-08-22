"""
Meeting endpoints.

Thin router layer — handles HTTP concerns only:
- Request validation (via Pydantic schemas)
- Authentication (via dependencies)
- Response formatting (via response_model)
- HTTP status codes

All business logic lives in app/services/meeting_service.py
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.lma_token import LMAToken
from app.models.meeting import MeetingStatus
from app.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
    MeetingStatusUpdate,
)
from app.schemas.transcript import TranscriptChunkResponse
from app.api.deps import get_current_user, get_current_lma
from app.services.meeting_service import MeetingService
from app.services.lma_command import send_join_meeting_command, is_lma_connected
from app.schemas.summary import SummaryResponse, MeetingWithSummary
router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.post(
    "",
    response_model=MeetingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_meeting(
    payload: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new meeting and signal the LMA daemon to join.
    """
    # Check if LMA daemon is connected
    if not is_lma_connected(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LMA daemon is not connected. Start it with: lma daemon",
        )

    # Create meeting via service
    service = MeetingService(db)
    meeting = await service.create_meeting(current_user.id, payload)

    # Send join command to LMA daemon
    await send_join_meeting_command(
        user_id=current_user.id,
        meeting_id=meeting.id,
        meeting_url=payload.meeting_url,
        language=payload.language,
    )

    return meeting


@router.get("", response_model=list[MeetingResponse])
async def list_meetings(
    status_filter: MeetingStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all meetings for the logged-in user."""
    service = MeetingService(db)
    return await service.list_meetings(current_user.id, status_filter)


@router.get("/summaries", response_model=list[MeetingWithSummary])
async def list_meetings_with_summaries(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all meetings with their summaries (for the dashboard)."""
    service = MeetingService(db)
    return await service.list_meetings_with_summaries(current_user.id)


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific meeting by ID."""
    service = MeetingService(db)
    meeting = await service.get_meeting(meeting_id, current_user.id)

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    return meeting


@router.patch("/{meeting_id}/status", response_model=MeetingResponse)
async def update_meeting_status(
    meeting_id: int,
    payload: MeetingStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_lma: LMAToken = Depends(get_current_lma),
):
    """Update meeting status (called by LMA)."""
    service = MeetingService(db)
    meeting = await service.update_meeting_status(
        meeting_id, current_lma.user_id, payload
    )

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )
    return meeting


@router.get(
    "/{meeting_id}/transcripts",
    response_model=list[TranscriptChunkResponse],
)
async def get_meeting_transcripts(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all transcript chunks for a meeting."""
    service = MeetingService(db)

    # Verify meeting belongs to user
    meeting = await service.get_meeting(meeting_id, current_user.id)
    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    return await service.get_meeting_transcripts(meeting_id)


@router.get(
    "/{meeting_id}/summary",
    response_model=SummaryResponse,
)
async def get_meeting_summary(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the summary for a specific meeting."""
    service = MeetingService(db)
    summary = await service.get_summary(meeting_id, current_user.id)

    if summary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not found. The meeting may not be processed yet.",
        )
    return summary



@router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a meeting and all associated data."""
    service = MeetingService(db)
    deleted = await service.delete_meeting(meeting_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )