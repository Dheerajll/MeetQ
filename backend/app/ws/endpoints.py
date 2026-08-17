"""
WebSocket route definitions.
"""
from fastapi import APIRouter, WebSocket

from app.ws.lma_handler import handle_lma_connection

router = APIRouter()


@router.websocket("/ws/lma/{meeting_id}")
async def lma_websocket(websocket: WebSocket, meeting_id: int):
    """
    WebSocket endpoint for LMA to stream transcript chunks.
    
    Connect with:
        ws://localhost:8000/ws/lma/{meeting_id}?token=<lma_token>
    """
    await handle_lma_connection(websocket, meeting_id)