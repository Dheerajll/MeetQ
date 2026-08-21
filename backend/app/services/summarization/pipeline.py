"""
Summarization pipeline orchestrator.

Thin coordinator that calls each module in sequence:
    0. Type detection
    1-2. Hierarchical summarization
    3. Overview generation
    4. Structured extraction
    5. Store in DB
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.transcript import TranscriptChunk
from app.models.summary import MeetingSummary
from app.services.summarization.type_detector import detect_meeting_type
from app.services.summarization.hierarchical import run_hierarchical
from app.services.summarization.overview import generate_overview
from app.services.summarization.extractor import extract_structured_info


async def summarize_meeting(meeting_id: int) -> None:
    """
    Full summarization pipeline.
    Fetches cleaned chunks, runs hierarchical summarization,
    generates overview, extracts structured info, stores in DB.
    """
    print(f"\n📝 Summarizing meeting {meeting_id}...")

    # Fetch cleaned chunks
    chunk_texts = await _fetch_chunks(meeting_id)
    if not chunk_texts:
        return

    print(f"📝 {len(chunk_texts)} chunks to summarize")

    # Step 0: Detect meeting type
    print(f"\n  [0/4] Detecting meeting type...")
    meeting_type = await detect_meeting_type(chunk_texts[:3])
    print(f"  → {meeting_type}")

    # Steps 1-2: Hierarchical summarization
    print(f"\n  [1/4] Hierarchical summarization...")
    reduced_summary = await run_hierarchical(chunk_texts)

    # Step 3: Generate overview paragraph
    print(f"\n  [2/4] Generating overview...")
    overview = await generate_overview(reduced_summary)

    # Step 4: Extract structured info
    print(f"\n  [3/4] Extracting structured info...")
    extracted = await extract_structured_info(overview)

    # Step 5: Store in DB
    print(f"\n  [4/4] Saving to DB...")
    await _save_summary(meeting_id, meeting_type, overview, extracted)

    print(f"✅ Meeting {meeting_id}: Done!")


async def _fetch_chunks(meeting_id: int) -> list[str]:
    """Fetch cleaned chunk texts from DB."""
    async with AsyncSessionLocal() as db:
        stmt = (
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == meeting_id)
            .order_by(TranscriptChunk.chunk_id)
        )
        result = await db.execute(stmt)
        chunks = result.scalars().all()

    if not chunks:
        print(f"⚠️ No chunks found for meeting {meeting_id}")
        return []

    texts = [c.cleaned_text or c.raw_text for c in chunks]
    return [t for t in texts if t.strip()]


async def _save_summary(
    meeting_id: int,
    meeting_type: str,
    overview: str,
    extracted: dict,
) -> None:
    """Store or update the summary in the database."""
    async with AsyncSessionLocal() as db:
        stmt = select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.meeting_type = meeting_type
            existing.overview = overview
            existing.key_topics = extracted["key_topics"]
            existing.decisions = extracted["decisions"]
            existing.action_items = extracted["action_items"]
        else:
            summary = MeetingSummary(
                meeting_id=meeting_id,
                meeting_type=meeting_type,
                overview=overview,
                key_topics=extracted["key_topics"],
                decisions=extracted["decisions"],
                action_items=extracted["action_items"],
            )
            db.add(summary)

        await db.commit()