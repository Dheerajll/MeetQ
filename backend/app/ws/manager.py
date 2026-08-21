"""
WebSocket Connection Manager.
Tracks active WebSocket connections.

Supports two types of keys:
- int (meeting_id): Data channel for chunk streaming
- str ("lma_control_{user_id}"): Control channel for daemon commands
"""

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # key can be int (meeting_id) or str (control channel)
        self.active_connections: dict[int | str, WebSocket] = {}

    async def connect(self, key: int | str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[key] = websocket

    def disconnect(self, key: int | str):
        self.active_connections.pop(key, None)

    def is_connected(self, key: int | str) -> bool:
        """Check if a connection exists for the given key."""
        return key in self.active_connections

    async def send_message(self, key: int | str, message: dict):
        """Send a JSON message to a specific connection."""
        ws = self.active_connections.get(key)
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