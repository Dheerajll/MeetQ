# RAG service
# Handles FAISS vector search + Ollama answer generation for chat queries
"""
RAG Service using pgvector.

No FAISS. No files. Vectors live in PostgreSQL alongside the chunks.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import get_embeddings
from app.models.transcript import TranscriptChunk


async def index_meeting(meeting_id: int, db: AsyncSession) -> None:
    """
    Generate embeddings for all cleaned chunks of a meeting
    and store them in the database.
    
    Called after cleaning completes in the processing pipeline.
    """
    # Fetch cleaned chunks
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

    # Generate embeddings for all chunks at once
    texts = [c.cleaned_text for c in chunks]
    vectors = get_embeddings(texts)  # Returns numpy array (N, 384)

    # Store vectors back into the chunks
    for chunk, vector in zip(chunks, vectors):
        chunk.embedding = vector.tolist()  # Convert numpy to list for pgvector

    await db.commit()
    print(f"✅ Indexed {len(chunks)} chunks for meeting {meeting_id}")


async def search_similar_chunks(
    query: str,
    user_id: int,
    db: AsyncSession,
    top_k: int = 5,
) -> list[TranscriptChunk]:
    """
    Search for chunks most similar to the query.
    
    Uses pgvector's cosine distance operator (<=>).
    Filters to only the user's meetings for privacy.
    """
    # Embed the query
    query_vector = get_embeddings([query])[0]  # Shape: (384,)

    # SQL: Find closest chunks belonging to this user
    # pgvector's <=> operator computes cosine distance
    from app.models.meeting import Meeting
    
    stmt = (
        select(TranscriptChunk)
        .join(Meeting, TranscriptChunk.meeting_id == Meeting.id)
        .where(Meeting.user_id == user_id)
        .where(TranscriptChunk.embedding.isnot(None))
        .order_by(TranscriptChunk.embedding.cosine_distance(query_vector.tolist()))
        .limit(top_k)
    )
    
    result = await db.execute(stmt)
    return list(result.scalars().all())