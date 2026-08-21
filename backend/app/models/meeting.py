from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import TYPE_CHECKING

from sqlalchemy import String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.transcript import TranscriptChunk


class MeetingStatus(str, PyEnum):
    """Meeting lifecycle states."""
    PENDING = "pending"           # Created, waiting for LMA to join
    RECORDING = "recording"       # LMA joined and capturing audio
    PROCESSING = "processing"     # Recording done, cleaning/summarizing
    COMPLETED = "completed"       # All processing done
    FAILED = "failed"             # Something went wrong


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500))
    meeting_url: Mapped[str] = mapped_column(String(1000))
    language: Mapped[str] = mapped_column(String(10), default="en")  # ← NEW
    status: Mapped[MeetingStatus] = mapped_column(
        Enum(MeetingStatus),
        default=MeetingStatus.PENDING,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[User] = relationship(back_populates="meetings")
    transcript_chunks: Mapped[list[TranscriptChunk]] = relationship(
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptChunk.chunk_id",
    )

    def __repr__(self) -> str:
        return f"<Meeting id={self.id} title='{self.title}' status={self.status}>"