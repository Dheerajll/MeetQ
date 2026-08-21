"""
Handles the LMA WebSocket lifecycle:
- Authentication
- Receiving transcript chunks
- Saving to database
- Sending ACKs
- Triggering processing pipeline on disconnect
"""
import asyncio
import json
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.models.lma_token import LMAToken
from app.models.meeting import Meeting, MeetingStatus
from app.models.transcript import TranscriptChunk
from app.services.meeting_processing import start_processing
from app.ws.manager import manager


async def handle_lma_connection(websocket: WebSocket, meeting_id: int):
    """Main handler for LMA WebSocket connections."""

    # 1. Extract and validate token BEFORE accepting
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    async with AsyncSessionLocal() as db:
        # Validate LMA Token
        stmt = select(LMAToken).where(
            LMAToken.token == token,
            LMAToken.is_active == True
        )
        result = await db.execute(stmt)
        lma_token = result.scalar_one_or_none()

        if not lma_token:
            await websocket.close(code=4003, reason="Invalid or revoked token")
            return

        # Validate Meeting ownership
        stmt = select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == lma_token.user_id
        )
        result = await db.execute(stmt)
        meeting = result.scalar_one_or_none()

        if not meeting:
            await websocket.close(code=4004, reason="Meeting not found or access denied")
            return

        # Update status to RECORDING if PENDING
        if meeting.status == MeetingStatus.PENDING:
            meeting.status = MeetingStatus.RECORDING
            meeting.started_at = datetime.now(timezone.utc)
            await db.commit()
            print(f"🔴 Meeting {meeting_id} status → RECORDING")

    # 2. Accept and register connection
    await manager.connect(meeting_id, websocket)
    print(f"✅ LMA connected for meeting {meeting_id}")

    # 3. Listen loop
    try:
        while True:
            data = await websocket.receive_text()

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_message(meeting_id, {
                    "status": "error",
                    "detail": "Invalid JSON"
                })
                continue

            # Handle handshake
            if payload.get("type") == "handshake":
                await manager.send_message(meeting_id, {"status": "handshake_ack"})
                continue

            # Handle keepalive pings
            if payload.get("type") == "ping":
                await manager.send_message(meeting_id, {"status": "pong"})
                continue

            # Save chunk to DB
            async with AsyncSessionLocal() as db:
                chunk = TranscriptChunk(
                    meeting_id=meeting_id,
                    chunk_id=payload.get("chunk_id"),
                    raw_text=payload.get("raw_text", ""),
                    cleaned_text=None,
                    confidence=payload.get("confidence", 0.0),
                    language=payload.get("language", "en"),
                    start_ms=payload.get("start_ms", 0),
                    end_ms=payload.get("end_ms", 0),
                    reason=payload.get("reason", "unknown"),
                )
                db.add(chunk)
                await db.commit()

            # Send ACK back to LMA
            await manager.send_message(meeting_id, {
                "status": "ack",
                "chunk_id": payload.get("chunk_id")
            })
            print(f"💾 Saved chunk {payload.get('chunk_id')} for meeting {meeting_id}")

    except WebSocketDisconnect:
        print(f"❌ LMA disconnected from meeting {meeting_id}")
        manager.disconnect(meeting_id)

        # Transition to PROCESSING
        async with AsyncSessionLocal() as db:
            stmt = select(Meeting).where(Meeting.id == meeting_id)
            result = await db.execute(stmt)
            meeting = result.scalar_one_or_none()

            if meeting and meeting.status == MeetingStatus.RECORDING:
                meeting.status = MeetingStatus.PROCESSING
                meeting.ended_at = datetime.now(timezone.utc)
                await db.commit()
                print(f"⏹️ Meeting {meeting_id} status → PROCESSING")

        # Fire processing pipeline in background (non-blocking)
        asyncio.create_task(start_processing(meeting_id))