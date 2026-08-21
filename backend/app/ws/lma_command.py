"""
LMA Command Service.

Sends commands to the LMA daemon through the control WebSocket.
The LMA daemon must already be connected to /ws/lma/control
for commands to be delivered.

Only one command exists: join_meeting.
The LMA manages the meeting lifecycle on its own after receiving it.
"""

from __future__ import annotations

from app.ws.manager import manager


async def send_join_meeting_command(
    user_id: int,
    meeting_id: int,
    meeting_url: str,
    language: str,
) -> dict:
    """
    Send a 'join_meeting' command to the LMA daemon.

    The command is sent through the existing control WebSocket connection.
    No new connection is created — we reuse the one the daemon established.

    Args:
        user_id: The user who owns the meeting (used to find control connection)
        meeting_id: The backend meeting ID
        meeting_url: The meeting URL to join
        language: The meeting language for transcription

    Returns:
        dict with 'success' bool and 'detail' message
    """
    control_key = f"lma_control_{user_id}"

    # Check if LMA daemon is connected
    if not manager.is_connected(control_key):
        print(f"❌ LMA daemon not connected for user {user_id}")
        return {
            "success": False,
            "detail": "LMA daemon is not connected. Start it with: lma daemon",
        }

    # Build the command
    command = {
        "type": "join_meeting",
        "meeting_id": meeting_id,
        "meeting_url": meeting_url,
        "language": language,
    }

    # Send through existing connection
    try:
        await manager.send_message(control_key, command)
        print(f"📤 Sent join_meeting command to LMA (meeting_id={meeting_id})")
        return {
            "success": True,
            "detail": f"Command sent to LMA daemon for meeting {meeting_id}",
        }
    except Exception as e:
        print(f"❌ Failed to send command to LMA: {e}")
        return {
            "success": False,
            "detail": f"Failed to send command: {e}",
        }


def is_lma_connected(user_id: int) -> bool:
    """
    Check if the LMA daemon is connected for a given user.
    Useful for the API to return early with a helpful error message.
    """
    control_key = f"lma_control_{user_id}"
    return manager.is_connected(control_key)