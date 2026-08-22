"""
RAG Service using pgvector.

No FAISS. No files. Vectors live in PostgreSQL alongside the chunks.
Embeddings are generated via Ollama (no local model loading).
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
    """
    stmt = (
        select(TranscriptChunk)
        .where(TranscriptChunk.meeting_id == meeting_id)
        .where(TranscriptChunk.cleaned_text.isnot(None))
        .order_by(TranscriptChunk.chunk_id)
    )
    result = await db.execute(stmt)
    chunks = result.scalars().all()

    if not chunks:
        print(f"⚠️ No cleaned chunks to index for meeting {meeting_id}")
        return

    # Generate embeddings via Ollama (batch call)
    texts = [c.cleaned_text for c in chunks]
    vectors = await get_embeddings(texts)

    # Store vectors back into the chunks
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
) -> list[TranscriptChunk]:
    """
    Search for chunks most similar to the query.
    Uses pgvector's cosine distance operator.
    Filters by time range if provided by the query parser.
    """
    # Embed the query via Ollama
    query_vector = await get_single_embedding(query)

    if not query_vector:
        return []

    # Base SQL query
    stmt = (
        select(TranscriptChunk)
        .join(Meeting, TranscriptChunk.meeting_id == Meeting.id)
        .where(Meeting.user_id == user_id)
        .where(TranscriptChunk.embedding.isnot(None))
    )

    # ──────────────────────────────────────────────
    # TIME FILTERS (Derived from natural language)
    # ──────────────────────────────────────────────
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