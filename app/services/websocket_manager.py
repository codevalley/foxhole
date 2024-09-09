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
        self.active_connections: Dict[WebSocket, User] = {}
        self.message_queue: List[str] = []

    async def connect(self, websocket: WebSocket, user: User) -> None:
        """
        Accept a new WebSocket connection and add it to the active connections.

        Args:
            websocket (WebSocket): The WebSocket connection to accept.
            user (User): The user associated with the connection.
        """
        await websocket.accept()
        self.active_connections[websocket] = user
        print(f"WebSocket connected for user {user.id}")  # Add this line
        logger.info(f"WebSocket connected for user {user.id}")

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Remove a WebSocket connection from the active connections.

        Args:
            websocket (WebSocket): The WebSocket connection to remove.
        """
        if websocket in self.active_connections:
            user = self.active_connections[websocket]
            del self.active_connections[websocket]
            logger.info(f"WebSocket disconnected for user {user.id}")
        else:
            logger.warning(
                "Attempted to disconnect a WebSocket that was not in active connections"
            )

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all active WebSocket connections.

        Args:
            message (str): The message to broadcast.
        """
        self.message_queue.append(message)
        logger.info(f"Broadcasting message: {message}")
        disconnected = []
        for websocket, user in self.active_connections.items():
            try:
                await websocket.send_text(message)
            except RuntimeError:
                logger.error(f"Failed to send message to user {user.id}")
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(websocket)

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

    async def close_all_connections(self) -> None:
        """Close all active WebSocket connections."""
        for websocket in list(self.active_connections.keys()):
            await websocket.close()
            self.disconnect(websocket)
        logger.info("All WebSocket connections closed")
