"""
WebSocket route definitions.
"""
from fastapi import APIRouter, WebSocket

from app.ws.lma_handler import handle_lma_connection
from app.ws.lma_control import handle_lma_control  # ← NEW

router = APIRouter()

# ──────────────────────────────────────────────
# Control channel (MUST be before {meeting_id})
# ──────────────────────────────────────────────
@router.websocket("/ws/lma/control")
async def lma_control_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for LMA daemon control channel.

    The LMA daemon connects here and stays connected,
    waiting for commands from the backend.

    Connect with:
        ws://localhost:8000/ws/lma/control?token=<lma_token>
    """
    await handle_lma_control(websocket)


@router.websocket("/ws/lma/{meeting_id}")
async def lma_websocket(websocket: WebSocket, meeting_id: int):
    """
    WebSocket endpoint for LMA to stream transcript chunks.
    
    Connect with:
        ws://localhost:8000/ws/lma/{meeting_id}?token=<lma_token>
    """
    await handle_lma_connection(websocket, meeting_id)
