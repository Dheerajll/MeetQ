"""
Pydantic schemas for the RAG endpoint.
"""

from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    """Payload for querying the RAG system."""
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)


class RAGSourceResponse(BaseModel):
    """A single source chunk returned to the frontend."""
    meeting_id: int
    chunk_id: int
    text: str
    start_ms: int
    end_ms: int

    model_config = {"from_attributes": True}


class RAGQueryResponse(BaseModel):
    """Final response containing the LLM answer and sources."""
    answer: str
    sources: list[RAGSourceResponse]