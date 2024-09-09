import logging
from fastapi import WebSocket
from app.models import User
from typing import Dict, List

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.
    """

    def __init__(self) -> None:
        """Initialize the WebSocketManager with an empty dictionary of connections."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.message_queue: List[str] = []

    async def connect(self, websocket: WebSocket, user: User) -> None:
        """
        Accept a new WebSocket connection and add it to the active connections.

        Args:
            websocket (WebSocket): The WebSocket connection to accept.
            user (User): The user associated with the connection.
        """
        await websocket.accept()
        self.active_connections[str(user.id)] = websocket
        logger.info(f"WebSocket connected for user {user.id}")

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
            logger.info(f"WebSocket disconnected for user {user_id}")

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all active WebSocket connections.

        Args:
            message (str): The message to broadcast.
        """
        self.message_queue.append(message)
        logger.info(f"Broadcasting message: {message}")
        disconnected = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except RuntimeError:
                logger.error(f"Failed to send message to user {user_id}")
                disconnected.append(user_id)

        for user_id in disconnected:
            del self.active_connections[user_id]

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """
        Send a personal message to a specific WebSocket connection.

        Args:
            message (str): The message to send.
            websocket (WebSocket): The WebSocket connection to send the message to.
        """
        await websocket.send_text(message)
        logger.info(f"Sent personal message: {message}")

    def get_last_message(self) -> str:
        """
        Get the last message sent in the broadcast queue.

        Returns:
            str: The last message sent, or an empty string if no messages have been sent.
        """
        return self.message_queue[-1] if self.message_queue else ""
