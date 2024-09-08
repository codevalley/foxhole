from fastapi import WebSocket
from app.models import User
from typing import Dict


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.
    """

    def __init__(self) -> None:
        """Initialize the WebSocketManager with an empty dictionary of connections."""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user: User) -> None:
        """
        Accept a new WebSocket connection and add it to the active connections.

        Args:
            websocket (WebSocket): The WebSocket connection to accept.
            user (User): The user associated with the connection.
        """
        await websocket.accept()
        self.active_connections[str(user.id)] = websocket

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the active connections.

        Args:
            websocket (WebSocket): The WebSocket connection to remove.
        """
        user_id = next(
            (uid for uid, ws in self.active_connections.items() if ws == websocket),
            None,
        )
        if user_id:
            del self.active_connections[user_id]

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all active WebSocket connections.

        Args:
            message (str): The message to broadcast.
        """
        for connection in self.active_connections.values():
            await connection.send_text(message)
