"""
Test cleaning service on REAL meeting data from the database.
Chunks stay separate — no concatenation.
"""
import asyncio
import sys
sys.path.insert(0, ".")

from app.services.cleaning_service import clean_meeting_transcripts

async def main():
    MEETING_ID = int(input("Enter meeting ID to clean: "))
    
    print(f"\n🚀 Running cleaning pipeline on meeting {MEETING_ID}...")
    await clean_meeting_transcripts(MEETING_ID)
    
    # Print chunk-by-chunk results (kept separate)
    print("\n" + "=" * 70)
    print("CHUNK-BY-CHUNK RESULTS (kept separate for Map-Reduce)")
    print("=" * 70)
    
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.transcript import TranscriptChunk
    
    async with AsyncSessionLocal() as db:
        stmt = (
            select(TranscriptChunk)
            .where(TranscriptChunk.meeting_id == MEETING_ID)
            .order_by(TranscriptChunk.chunk_id)
        )
        result = await db.execute(stmt)
        chunks = result.scalars().all()
        
        for chunk in chunks:
            print(f"\n  [Chunk {chunk.chunk_id}] (start: {chunk.start_ms}ms, end: {chunk.end_ms}ms)")
            print(f"  RAW:     {chunk.raw_text}")
            print(f"  CLEANED: {chunk.cleaned_text if chunk.cleaned_text else '(not cleaned yet)'}")
            print(f"  ---")
    
    print(f"\n  Total chunks: {len(chunks)}")
    print("✅ Done! Chunks stored separately in DB for Map-Reduce.")

if __name__ == "__main__":
    asyncio.run(main())