"""
Test cleaning service on REAL meeting data from the database.

Usage:
    python test_real_cleaning.py              # Interactive (asks for meeting ID)
    python test_real_cleaning.py 14           # Direct (uses meeting ID 14)
    python test_real_cleaning.py 14 --dry-run # Preview without saving to DB
"""

import asyncio
import sys
import time

sys.path.insert(0, ".")


async def main():
    # Parse arguments
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    if args:
        meeting_id = int(args[0])
    else:
        meeting_id = int(input("Enter meeting ID to clean: "))

    print(f"\n{'=' * 70}")
    print(f"🚀 CLEANING PIPELINE TEST — Meeting {meeting_id}")
    print(f"{'=' * 70}")

    if dry_run:
        print("📋 MODE: DRY RUN (preview only, no DB writes)")
        await run_dry_run(meeting_id)
    else:
        print("📋 MODE: FULL PIPELINE (cleans and saves to DB)")
        await run_full_pipeline(meeting_id)


async def run_full_pipeline(meeting_id: int):
    """Run the full cleaning pipeline (reads from DB, cleans, saves back)."""
    from app.services.cleaning import clean_meeting_transcripts

    start_time = time.time()
    await clean_meeting_transcripts(meeting_id)
    elapsed = time.time() - start_time

    print(f"\n⏱️  Total cleaning time: {elapsed:.2f}s")

    # Display results
    await display_results(meeting_id)


async def run_dry_run(meeting_id: int):
    """Preview cleaning without saving to DB (uses clean_chunks_in_memory)."""
    from app.core.database import AsyncSessionLocal
    from app.models.transcript import TranscriptChunk
    from app.services.cleaning import clean_chunks_in_memory
    from sqlalchemy import select

    # Fetch chunks from DB (read-only)
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
        return

    print(f"📝 Found {len(chunks)} chunks")

    # Prepare data for in-memory cleaning
    chunks_data = [
        {"chunk_id": c.chunk_id, "raw_text": c.raw_text or ""}
        for c in chunks
    ]

    # Run cleaning WITHOUT saving to DB
    start_time = time.time()
    cleaned_results = await clean_chunks_in_memory(chunks_data)
    elapsed = time.time() - start_time

    print(f"\n⏱️  Total cleaning time: {elapsed:.2f}s")

    # Display results
    print(f"\n{'=' * 70}")
    print("DRY RUN RESULTS (not saved to DB)")
    print(f"{'=' * 70}")

    for i, chunk in enumerate(chunks):
        print(f"\n  [Chunk {chunk.chunk_id}] (start: {chunk.start_ms}ms, end: {chunk.end_ms}ms)")
        print(f"  RAW:     {chunk.raw_text[:150]}...")
        print(f"  CLEANED: {cleaned_results[i][:150]}...")
        print(f"  ---")

    print(f"\n  Total chunks: {len(chunks)}")
    print("📋 Dry run complete. No changes saved to DB.")


async def display_results(meeting_id: int):
    """Display chunk-by-chunk results from the database."""
    from app.core.database import AsyncSessionLocal
    from app.models.transcript import TranscriptChunk
    from sqlalchemy import select

    print(f"\n{'=' * 70}")
    print("CHUNK-BY-CHUNK RESULTS (stored in DB)")
    print(f"{'=' * 70}")

    async with AsyncSessionLocal() as db:
        stmt = (
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == meeting_id)
            .order_by(TranscriptChunk.chunk_id)
        )
        result = await db.execute(stmt)
        chunks = result.scalars().all()

        for chunk in chunks:
            raw_preview = chunk.raw_text[:120] + "..." if len(chunk.raw_text) > 120 else chunk.raw_text
            cleaned_preview = chunk.cleaned_text[:120] + "..." if chunk.cleaned_text and len(chunk.cleaned_text) > 120 else (chunk.cleaned_text or "(not cleaned)")

            print(f"\n  [Chunk {chunk.chunk_id}] ({chunk.start_ms}ms → {chunk.end_ms}ms)")
            print(f"  RAW:     {raw_preview}")
            print(f"  CLEANED: {cleaned_preview}")
            print(f"  {'─' * 60}")

    print(f"\n  Total chunks: {len(chunks)}")
    print(f"✅ Cleaning complete. Results saved to DB.")


if __name__ == "__main__":
    asyncio.run(main())