"""
Meeting Processing Pipeline.

Orchestrates the post-recording lifecycle:
    processing → cleaning → FAISS → summarization → completed

This is the SINGLE source of truth for what happens after recording ends.
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.meeting import Meeting, MeetingStatus
from app.services.cleaning import clean_meeting_transcripts
from app.services.summarization import summarize_meeting
from app.services.rag_service import index_meeting
from app.services.email_service import send_meeting_completed_email

async def start_processing(meeting_id: int) -> None:
    """
    Run the full processing pipeline for a meeting.
    
    Called when LMA disconnects and all chunks are acknowledged.
    Meeting status should already be PROCESSING when this is called.
    
    Pipeline:
        1. Clean transcripts (overlap removal + LLM inference)
        2. Index cleaned transcripts in FAISS (TODO)
        3. Map-Reduce summarization (TODO)
        4. Mark meeting as COMPLETED
    """
    print(f"\n🔄 Meeting {meeting_id}: Processing pipeline started")

    try:
        # ──────────────────────────────────────────────
        # STEP 1: Clean transcripts
        # ──────────────────────────────────────────────
        print(f"🧹 Meeting {meeting_id}: Running transcript cleaning...")
        await clean_meeting_transcripts(meeting_id)
        print(f"✅ Meeting {meeting_id}: Cleaning complete.")

        # ──────────────────────────────────────────────
        # STEP 2: Index cleaned transcripts for RAG
        # ──────────────────────────────────────────────
        print(f"🔍 Meeting {meeting_id}: Indexing transcripts for RAG...")
        async with AsyncSessionLocal() as db:
            await index_meeting(meeting_id, db)
        print(f"✅ Meeting {meeting_id}: Indexing complete.")

        # ──────────────────────────────────────────────
        # STEP 3: Hierarchical Summarization
        # ──────────────────────────────────────────────
        print(f"📝 Meeting {meeting_id}: Running summarization...")
        await summarize_meeting(meeting_id)
        print(f"✅ Meeting {meeting_id}: Summarization complete.")
        
        # ──────────────────────────────────────────────
        # STEP 4: Mark meeting as COMPLETED
        # ──────────────────────────────────────────────
        await _update_status(meeting_id, MeetingStatus.COMPLETED)
        print(f"🎉 Meeting {meeting_id}: Pipeline complete → COMPLETED")

        # ──────────────────────────────────────────────
        # STEP 5: Send completion email
        # ──────────────────────────────────────────────
        print(f"📧 Meeting {meeting_id}: Sending completion email...")
        # We await it, but the email service catches its own exceptions
        # so a failed email won't break the pipeline status.
        await send_meeting_completed_email(meeting_id)

    except Exception as e:
        print(f"❌ Meeting {meeting_id}: Pipeline failed: {e}")
        await _update_status(meeting_id, MeetingStatus.FAILED)
        raise


async def _update_status(meeting_id: int, status: MeetingStatus) -> None:
    """Update meeting status in the database."""
    async with AsyncSessionLocal() as db:
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        result = await db.execute(stmt)
        meeting = result.scalar_one_or_none()

        if meeting:
            meeting.status = status
            await db.commit()