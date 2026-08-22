# Meeting service
# Creates meetings, updates statuses, handles meeting lifecycle
"""
Meeting Service.

Handles all meeting-related business logic and database operations.
The API layer (router) calls this service — it never touches the DB directly.

Responsibilities:
- Create meetings
- List meetings
- Get meeting by ID
- Update meeting status
- Get meeting transcripts
- Delete meetings
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import TranscriptChunk
from app.schemas.meeting import MeetingCreate, MeetingStatusUpdate
from app.models.summary import MeetingSummary

class MeetingService:
    """
    Service layer for meeting operations.
    
    Each method receives a database session and performs
    the actual business logic. The router just calls these.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ──────────────────────────────────────────────
    # Create
    # ──────────────────────────────────────────────

    async def create_meeting(
        self,
        user_id: int,
        payload: MeetingCreate,
    ) -> Meeting:
        """Create a new meeting record."""
        meeting = Meeting(
            user_id=user_id,
            title=payload.title,
            meeting_url=payload.meeting_url,
            language=payload.language,
            status=MeetingStatus.PENDING,
            notes=payload.notes,
        )
        self.db.add(meeting)
        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting

    # ──────────────────────────────────────────────
    # Read
    # ──────────────────────────────────────────────

    async def list_meetings(
        self,
        user_id: int,
        status_filter: MeetingStatus | None = None,
    ) -> list[Meeting]:
        """List all meetings for a user, optionally filtered by status."""
        stmt = select(Meeting).where(Meeting.user_id == user_id)

        if status_filter is not None:
            stmt = stmt.where(Meeting.status == status_filter)

        stmt = stmt.order_by(Meeting.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_meeting(
        self,
        meeting_id: int,
        user_id: int,
    ) -> Meeting | None:
        """Get a specific meeting by ID, scoped to the user."""
        stmt = select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ──────────────────────────────────────────────
    # Update Status
    # ──────────────────────────────────────────────

    async def update_meeting_status(
        self,
        meeting_id: int,
        user_id: int,
        payload: MeetingStatusUpdate,
    ) -> Meeting | None:
        """
        Update meeting status with timestamp transitions.
        
        Returns None if meeting not found.
        """
        meeting = await self.get_meeting(meeting_id, user_id)
        if meeting is None:
            return None

        old_status = meeting.status
        meeting.status = payload.status

        # Set timestamps based on transitions
        if (
            old_status == MeetingStatus.PENDING
            and payload.status == MeetingStatus.RECORDING
        ):
            meeting.started_at = datetime.now(timezone.utc)
        elif payload.status in (
            MeetingStatus.PROCESSING,
            MeetingStatus.COMPLETED,
            MeetingStatus.FAILED,
        ):
            if meeting.ended_at is None:
                meeting.ended_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(meeting)
        return meeting

    # ──────────────────────────────────────────────
    # Transcripts
    # ──────────────────────────────────────────────

    async def get_meeting_transcripts(
        self,
        meeting_id: int,
    ) -> list[TranscriptChunk]:
        """Get all transcript chunks for a meeting."""
        stmt = (
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == meeting_id)
            .order_by(TranscriptChunk.chunk_id)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # ──────────────────────────────────────────────
    # Summary
    # ──────────────────────────────────────────────

    async def get_summary(
        self,
        meeting_id: int,
        user_id: int,
    ) -> MeetingSummary | None:
        """Get the summary for a meeting (with ownership check)."""
        # Verify the meeting belongs to this user first
        meeting = await self.get_meeting(meeting_id, user_id)
        if meeting is None:
            return None

        stmt = select(MeetingSummary).where(
            MeetingSummary.meeting_id == meeting_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_meetings_with_summaries(
        self,
        user_id: int,
    ) -> list[dict]:
        """
        List all meetings with their summaries joined in.
        Returns a list of dicts ready for MeetingWithSummary schema.
        """
        stmt = (
            select(Meeting, MeetingSummary)
            .outerjoin(
                MeetingSummary,
                Meeting.id == MeetingSummary.meeting_id,
            )
            .where(Meeting.user_id == user_id)
            .order_by(Meeting.created_at.desc())
        )
        result = await self.db.execute(stmt)
        rows = result.all()

        items = []
        for meeting, summary in rows:
            items.append({
                "id": meeting.id,
                "title": meeting.title,
                "meeting_url": meeting.meeting_url,
                "language": meeting.language,
                "status": meeting.status,
                "started_at": meeting.started_at,
                "created_at": meeting.created_at,
                "meeting_type": summary.meeting_type if summary else None,
                "overview": summary.overview if summary else None,
                "key_topics": summary.key_topics if summary else [],
                "decisions": summary.decisions if summary else [],
                "action_items": summary.action_items if summary else [],
            })
        return items

    # ──────────────────────────────────────────────
    # Delete
    # ──────────────────────────────────────────────

    async def delete_meeting(
        self,
        meeting_id: int,
        user_id: int,
    ) -> bool:
        """
        Delete a meeting and all associated data.
        Returns True if deleted, False if not found.
        """
        meeting = await self.get_meeting(meeting_id, user_id)
        if meeting is None:
            return False

        await self.db.delete(meeting)
        await self.db.commit()
        return True