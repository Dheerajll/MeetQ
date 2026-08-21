"""
LMA Control WebSocket.

Persistent connection between the LMA daemon and the backend.
The LMA daemon connects here and waits for commands.
When the backend needs to start a meeting, it sends a command
through this connection via the ConnectionManager.

Connection key: "lma_control_{user_id}"

Lifecycle:
    1. LMA daemon connects with token
    2. Backend registers connection
    3. LMA waits for commands (sends ping/pong keepalive)
    4. Backend sends "join_meeting" command
    5. LMA sends "command_ack" back
    6. LMA disconnects to run the meeting
    7. After meeting ends, LMA reconnects (loop restarts)
"""

import json
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.lma_token import LMAToken
from app.ws.manager import manager


async def handle_lma_control(websocket: WebSocket):
    """
    Handle the LMA daemon's control WebSocket connection.

    The LMA daemon connects here and waits for commands.
    Only one control connection per user is allowed.
    """

    # ──────────────────────────────────────────────
    # 1. Authenticate via token
    # ──────────────────────────────────────────────
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    async with AsyncSessionLocal() as db:
        stmt = select(LMAToken).where(
            LMAToken.token == token,
            LMAToken.is_active == True,
        )
        result = await db.execute(stmt)
        lma_token = result.scalar_one_or_none()

        if not lma_token:
            await websocket.close(code=4003, reason="Invalid or revoked token")
            return

    user_id = lma_token.user_id
    control_key = f"lma_control_{user_id}"

    # ──────────────────────────────────────────────
    # 2. Accept and register connection
    # ──────────────────────────────────────────────
    await websocket.accept()

    # If there's an existing control connection for this user, close it
    if manager.is_connected(control_key):
        old_ws = manager.active_connections.get(control_key)
        if old_ws:
            try:
                await old_ws.close(code=4000, reason="Replaced by new connection")
            except Exception:
                pass

    manager.active_connections[control_key] = websocket
    print(f"🔌 LMA daemon connected (user_id={user_id})")

    # ──────────────────────────────────────────────
    # 3. Listen loop
    # ──────────────────────────────────────────────
    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "status": "error",
                    "detail": "Invalid JSON",
                })
                continue

            msg_type = payload.get("type")

            # Handle keepalive ping from LMA daemon
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            # Handle command acknowledgment from LMA daemon
            if msg_type == "command_ack":
                command = payload.get("command", "unknown")
                meeting_id = payload.get("meeting_id")
                status = payload.get("status", "unknown")
                print(
                    f"📩 LMA ack: command={command}, "
                    f"meeting_id={meeting_id}, status={status}"
                )
                continue

            # Handle status updates from LMA daemon
            if msg_type == "status":
                print(f"[LMA Control] Status: {payload.get('status')}")
                continue

            # Unknown message type
            print(f"[LMA Control] Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        print(f"❌ LMA daemon disconnected (user_id={user_id})")
        manager.active_connections.pop(control_key, None)