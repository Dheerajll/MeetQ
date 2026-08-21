"""
RAG Service using pgvector.

No FAISS. No files. Vectors live in PostgreSQL alongside the chunks.
Embeddings are generated via Ollama (no local model loading).

Supports:
- Indexing meetings for search
- Semantic search with time-range filtering
- Scoping search to a specific meeting
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import get_embeddings, get_single_embedding
from app.models.transcript import TranscriptChunk
from app.models.meeting import Meeting


async def index_meeting(meeting_id: int, db: AsyncSession) -> None:
    """
    Generate embeddings for all cleaned chunks of a meeting
    and store them in the database.

    Called after cleaning completes in the processing pipeline.
    Skips chunks that already have embeddings (idempotent).
    """
    stmt = (
        select(TranscriptChunk)
        .where(TranscriptChunk.meeting_id == meeting_id)
        .where(TranscriptChunk.cleaned_text.isnot(None))
        .where(TranscriptChunk.embedding.is_(None))
        .order_by(TranscriptChunk.chunk_id)
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()

    if not chunks:
        print(f"⚠️ No new chunks to index for meeting {meeting_id}")
        return

    texts = [c.cleaned_text for c in chunks]
    print(f"  Embedding {len(texts)} chunks...")
    vectors = await get_embeddings(texts)

    if len(vectors) != len(chunks):
        print(f"❌ Embedding count mismatch: got {len(vectors)}, expected {len(chunks)}")
        return

    for chunk, vector in zip(chunks, vectors):
        chunk.embedding = vector

    await db.commit()
    print(f"✅ Indexed {len(chunks)} chunks for meeting {meeting_id}")


async def search_similar_chunks(
    query: str,
    user_id: int,
    db: AsyncSession,
    top_k: int = 5,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    meeting_id: int | None = None,
) -> list[TranscriptChunk]:
    """
    Search for chunks most similar to the query.

    Supports filtering by:
    - Time range (based on when the meeting started/created)
    - Specific meeting ID

    Uses pgvector's cosine distance operator for semantic similarity.
    """
    query_vector = await get_single_embedding(query)

    if not query_vector:
        return []

    # Base query
    stmt = (
        select(TranscriptChunk)
        .join(Meeting, TranscriptChunk.meeting_id == Meeting.id)
        .where(Meeting.user_id == user_id)
        .where(TranscriptChunk.embedding.isnot(None))
    )

    # ──────────────────────────────────────────────
    # SCOPE & TIME FILTERS
    # ──────────────────────────────────────────────

    # Filter by specific meeting
    if meeting_id is not None:
        stmt = stmt.where(TranscriptChunk.meeting_id == meeting_id)

    # Filter by time range
    # We check started_at first. If the meeting never started (PENDING/FAILED),
    # fall back to created_at so it doesn't get excluded.
    if start_date is not None:
        stmt = stmt.where(
            (Meeting.started_at >= start_date)
            | ((Meeting.started_at.is_(None)) & (Meeting.created_at >= start_date))
        )

    if end_date is not None:
        stmt = stmt.where(
            (Meeting.started_at <= end_date)
            | ((Meeting.started_at.is_(None)) & (Meeting.created_at <= end_date))
        )

    # ──────────────────────────────────────────────
    # SEMANTIC SEARCH
    # ──────────────────────────────────────────────
    stmt = (
        stmt.order_by(TranscriptChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )

    result = await db.execute(stmt)
    return list(result.scalars().all())