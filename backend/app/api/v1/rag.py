"""
RAG (Retrieval-Augmented Generation) endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
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
    Query the meeting knowledge base using natural language.
    Time references ("yesterday", "last week") are parsed automatically.
    """

    # 1. Parse the query for time references
    parsed = parse_query(payload.query)

    if parsed.start_date:
        print(f"🔍 Time filter applied: {parsed.start_date.date()} → {parsed.end_date.date()}")
    else:
        print("🔍 No time filter applied (searching all meetings)")

    # 2. Search for relevant chunks
    chunks = await search_similar_chunks(
        query=payload.query,
        user_id=current_user.id,
        db=db,
        top_k=payload.top_k,
        start_date=parsed.start_date,
        end_date=parsed.end_date,
    )

    if not chunks:
        return RAGQueryResponse(
            answer="I couldn't find any relevant meeting transcripts for that query.",
            sources=[],
        )

    # 3. Format context for the LLM
    context_text = "\n\n---\n\n".join([c.cleaned_text or c.raw_text for c in chunks])

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
    sources = [
        RAGSourceResponse(
            meeting_id=c.meeting_id,
            chunk_id=c.chunk_id,
            text=c.cleaned_text or c.raw_text,
            start_ms=c.start_ms,
            end_ms=c.end_ms,
        )
        for c in chunks
    ]

    return RAGQueryResponse(answer=answer, sources=sources)