"""
WebSocket Connection Manager.

Tracks active WebSocket connections.
Useful for broadcasting messages or sending updates
to specific clients from other parts of the app.
"""
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # meeting_id -> WebSocket connection
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, meeting_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[meeting_id] = websocket

    def disconnect(self, meeting_id: int):
        self.active_connections.pop(meeting_id, None)

    async def send_message(self, meeting_id: int, message: dict):
        """Send a message to a specific meeting's connection."""
        ws = self.active_connections.get(meeting_id)
        if ws:
            await ws.send_json(message)

    async def broadcast(self, message: dict):
        """Send a message to all active connections."""
        for ws in self.active_connections.values():
            await ws.send_json(message)

    @property
    def active_count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()