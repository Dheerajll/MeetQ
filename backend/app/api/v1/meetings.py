from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import TranscriptChunk
from app.schemas.meeting import (
    MeetingCreate,
    MeetingResponse,
    MeetingStatusUpdate,
)
from app.schemas.transcript import TranscriptChunkResponse
from app.api.deps import get_current_user, get_current_lma

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
    Create a new meeting.
    Starts in PENDING status, ready for LMA to join immediately.
    """
    meeting = Meeting(
        user_id=current_user.id,
        title=payload.title,
        meeting_url=payload.meeting_url,
        status=MeetingStatus.PENDING,
        notes=payload.notes,
    )
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)

    return meeting


@router.get("", response_model=list[MeetingResponse])
async def list_meetings(
    status_filter: MeetingStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all meetings for the logged-in user."""
    stmt = select(Meeting).where(Meeting.user_id == current_user.id)

    if status_filter is not None:
        stmt = stmt.where(Meeting.status == status_filter)

    stmt = stmt.order_by(Meeting.created_at.desc())

    result = await db.execute(stmt)
    meetings = result.scalars().all()

    return meetings


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific meeting by ID."""
    stmt = select(Meeting).where(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

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
    current_lma=Depends(get_current_lma),
):
    """
    Update meeting status (called by LMA).
    
    Status transitions:
    - PENDING → RECORDING (LMA joined)
    - RECORDING → PROCESSING (meeting ended)
    - PROCESSING → COMPLETED (transcripts cleaned/summarized)
    - Any → FAILED (error occurred)
    """
    stmt = select(Meeting).where(
        Meeting.id == meeting_id,
        Meeting.user_id == current_lma.user_id,
    )
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    old_status = meeting.status
    meeting.status = payload.status

    # Set timestamps based on transitions
    if old_status == MeetingStatus.PENDING and payload.status == MeetingStatus.RECORDING:
        meeting.started_at = datetime.now(timezone.utc)
    elif payload.status in (MeetingStatus.PROCESSING, MeetingStatus.COMPLETED, MeetingStatus.FAILED):
        if meeting.ended_at is None:
            meeting.ended_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(meeting)

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
    stmt = select(Meeting).where(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    stmt = (
        select(TranscriptChunk)
        .where(TranscriptChunk.meeting_id == meeting_id)
        .order_by(TranscriptChunk.chunk_id)
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()

    return chunks


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
    stmt = select(Meeting).where(
        Meeting.id == meeting_id,
        Meeting.user_id == current_user.id,
    )
    result = await db.execute(stmt)
    meeting = result.scalar_one_or_none()

    if meeting is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found",
        )

    await db.delete(meeting)
    await db.commit()