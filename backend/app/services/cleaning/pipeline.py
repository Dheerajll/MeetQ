"""
Main cleaning pipeline orchestration.

Coordinates:
- English chunks → code-based overlap removal
- Nepali/mixed chunks → dynamic batching → LLM inference
- Database storage of cleaned results
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.transcript import TranscriptChunk
from app.services.cleaning.text_utils import is_english_chunk
from app.services.cleaning.overlap import clean_english_chunk
from app.services.cleaning.llm_inference import infer_batch
from app.services.cleaning.batching import group_chunks_into_batches


# ============================================================
# In-memory cleaning (for testing)
# ============================================================

async def clean_chunks_in_memory(chunks_data: list[dict]) -> list[str]:
    """
    Clean chunks without database.
    
    English: code-based overlap removal (sequential, no LLM).
    Nepali/mixed: dynamic batching → LLM inference.
    
    Args:
        chunks_data: List of dicts with 'chunk_id' and 'raw_text' keys.
        
    Returns:
        List of cleaned texts in the same order as input.
    """
    print(f"\n🧹 Cleaning {len(chunks_data)} chunks...")

    # Initialize results array
    results = [None] * len(chunks_data)
    mixed_indices = []
    prev_english_raw: str | None = None

    # Pass 1: Process English chunks immediately, collect mixed chunk indices
    for idx, chunk in enumerate(chunks_data):
        chunk_id = chunk["chunk_id"]
        raw_text = chunk["raw_text"]

        if is_english_chunk(raw_text):
            print(f"  Chunk {chunk_id}: English → code overlap removal")
            cleaned = clean_english_chunk(
                raw_text=raw_text,
                prev_english_raw=prev_english_raw,
            )
            results[idx] = cleaned
            prev_english_raw = raw_text
        else:
            mixed_indices.append(idx)
            prev_english_raw = None  # Reset English chain

    # Pass 2: Process all mixed chunks with dynamic batching
    if mixed_indices:
        mixed_chunks = [chunks_data[i] for i in mixed_indices]
        print(f"\n  📦 {len(mixed_chunks)} Nepali/mixed chunks → dynamic batching")

        # Group into batches
        batches = group_chunks_into_batches(mixed_chunks)
        print(f"  📦 Grouped into {len(batches)} batch(es)")

        # Process each batch
        batch_offset = 0
        for batch_idx, batch in enumerate(batches):
            print(f"\n  --- Batch {batch_idx + 1}/{len(batches)} ({len(batch)} chunks) ---")

            cleaned_texts = await infer_batch(batch)

            for i, cleaned in enumerate(cleaned_texts):
                results[mixed_indices[batch_offset + i]] = cleaned

            batch_offset += len(batch)

    return results


# ============================================================
# Database cleaning (production)
# ============================================================

async def clean_meeting_transcripts(meeting_id: int) -> None:
    """
    Main cleaning pipeline for a meeting.
    
    Fetches chunks from DB, cleans them, and stores cleaned_text back.
    """
    print(f"\n🧹 Starting transcript cleaning for meeting {meeting_id}...")

    async with AsyncSessionLocal() as db:
        # Fetch all chunks for this meeting
        stmt = (
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == meeting_id)
            .order_by(TranscriptChunk.chunk_id)
        )
        result = await db.execute(stmt)
        chunks = result.scalars().all()

        if not chunks:
            print(f"⚠️ No chunks found for meeting {meeting_id}")
            return

        print(f"📝 Found {len(chunks)} chunks")

        # Prepare data for cleaning
        chunks_data = [
            {"chunk_id": c.chunk_id, "raw_text": c.raw_text or ""}
            for c in chunks
        ]

        # Run cleaning pipeline
        cleaned_results = await clean_chunks_in_memory(chunks_data)

        # Store cleaned text back to database
        for i, chunk in enumerate(chunks):
            chunk.cleaned_text = cleaned_results[i]

        await db.commit()
        print(f"✓ Saved {len(chunks)} cleaned chunks")