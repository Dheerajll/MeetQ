# Transcript schemas for request/response validation
# TranscriptChunkPayload schema for what LMA sends via WebSocket
"""
Pydantic schemas for TranscriptChunk payloads.

TranscriptChunkReceive: what the LMA sends via WebSocket.
TranscriptChunkResponse: what the backend returns to the frontend.
"""
from datetime import datetime
from pydantic import BaseModel


class TranscriptChunkReceive(BaseModel):
    """
    Schema for receiving a transcript chunk from the LMA.
    This matches the TranscriptChunk dataclass in the LMA package.
    """
    chunk_id: int
    raw_text: str
    confidence: float
    language: str
    start_ms: int
    end_ms: int
    reason: str
    forced: bool


class TranscriptChunkResponse(BaseModel):
    """Schema for returning transcript data to the frontend."""
    id: int
    meeting_id: int
    chunk_id: int
    raw_text: str
    cleaned_text: str | None
    confidence: float
    language: str
    start_ms: int
    end_ms: int
    reason: str
    received_at: datetime

    model_config = {"from_attributes": True}