"""
RAG (Retrieval-Augmented Generation) endpoints.

POST /rag/query — Query meeting transcripts using semantic search + LLM.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.meeting import Meeting
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGSourceResponse
from app.services.rag_service import search_similar_chunks
from app.services.query_parser import parse_query
from app.ai.ollama_client import ollama
from app.api.deps import get_current_user

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    payload: RAGQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Query the meeting knowledge base.

    1. Parse query for time filters ("last week", "yesterday").
    2. Search for relevant chunks using pgvector.
    3. Generate an answer using Ollama.
    """

    # 1. Parse the query for time references
    parsed = parse_query(payload.query)

    # Use explicit dates from payload if provided, otherwise use parsed dates
    start_date = payload.start_date or parsed.start_date
    end_date = payload.end_date or parsed.end_date

    if start_date:
        print(f"🔍 Time filter: {start_date.date()} → {end_date.date() if end_date else 'now'}")

    # 2. Search for relevant chunks
    chunks = await search_similar_chunks(
        query=payload.query,
        user_id=current_user.id,
        db=db,
        top_k=payload.top_k,
        start_date=start_date,
        end_date=end_date,
        meeting_id=payload.meeting_id,
    )

    if not chunks:
        return RAGQueryResponse(
            answer="I couldn't find any relevant meeting transcripts for that query.",
            sources=[],
        )

    # 3. Format context for the LLM
    context_parts = []
    for chunk in chunks:
        context_parts.append(chunk.cleaned_text or chunk.raw_text)

    context_text = "\n\n---\n\n".join(context_parts)

    # 4. Generate answer using Ollama
    system_prompt = (
        "You are a helpful assistant answering questions about meetings. "
        "Use ONLY the provided context to answer. If the answer isn't in the "
        "context, say you don't have that information. Be concise and factual."
    )

    user_prompt = (
        f"CONTEXT:\n{context_text}\n\n"
        f"QUESTION: {payload.query}\n\n"
        f"ANSWER:"
    )

    try:
        answer = await ollama.generate(user_prompt, system_prompt=system_prompt)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to generate answer: {e}",
        )

    # 5. Build source responses
    sources = []
    for chunk in chunks:
        # Fetch meeting title for context
        meeting_title = None
        if chunk.meeting:
            meeting_title = chunk.meeting.title

        sources.append(
            RAGSourceResponse(
                meeting_id=chunk.meeting_id,
                chunk_id=chunk.chunk_id,
                text=chunk.cleaned_text or chunk.raw_text,
                start_ms=chunk.start_ms,
                end_ms=chunk.end_ms,
                meeting_title=meeting_title,
            )
        )

    return RAGQueryResponse(answer=answer, sources=sources)