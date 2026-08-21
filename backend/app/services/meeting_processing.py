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
        # STEP 2: Index cleaned transcripts in FAISS
        # ──────────────────────────────────────────────
        # TODO: Add FAISS indexing here for RAG-based retrieval.
        #
        # What will happen:
        #   1. Fetch all cleaned_text chunks for this meeting
        #   2. Generate embeddings (e.g., sentence-transformers)
        #   3. Store in FAISS index with metadata (meeting_id, chunk_id, speaker)
        #   4. Persist index for later Q&A / retrieval
        #
        # from app.services.rag.indexer import index_meeting_transcripts
        # await index_meeting_transcripts(meeting_id)
        #
        print(f"📌 Meeting {meeting_id}: [FAISS indexing — TODO]")

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