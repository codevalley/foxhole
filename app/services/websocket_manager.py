import logging
from fastapi import WebSocket
from app.models import User
from typing import Dict, List
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.
    """

    def __init__(self) -> None:
        """Initialize the WebSocketManager with an empty dictionary of connections."""
        self.active_connections: Dict[WebSocket, User] = {}
        self.message_queue: List[str] = []
        self._lock = asyncio.Lock()
        self._disconnect_event = asyncio.Event()

    async def connect(self, websocket: WebSocket, user: User) -> None:
        """
        Accept a new WebSocket connection and add it to the active connections.

        Args:
            websocket (WebSocket): The WebSocket connection to accept.
            user (User): The user associated with the connection.
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections[websocket] = user
        logger.info(
            f"WebSocket connected for user {user.id}. Total connections: {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Disconnect a WebSocket connection and remove it from active connections.

        Args:
            websocket (WebSocket): The WebSocket connection to disconnect.
        """
        async with self._lock:
            if websocket in self.active_connections:
                user = self.active_connections.pop(websocket)
                logger.info(
                    f"WebSocket disconnected for user {user.id}. Remaining connections: {len(self.active_connections)}"
                )
            else:
                logger.warning(
                    "Attempted to disconnect a WebSocket that was not in active connections"
                )

        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"Error closing WebSocket: {e}")

        if not self.active_connections:
            self._disconnect_event.set()

    async def close_all_connections(self) -> None:
        """Close all active WebSocket connections."""
        logger.info(
            f"Closing all connections. Active connections before: {len(self.active_connections)}"
        )
        async with self._lock:
            for websocket in list(self.active_connections.keys()):
                await self.disconnect(websocket)
        logger.info(
            f"All connections closed. Active connections after: {len(self.active_connections)}"
        )

    async def cleanup(self) -> None:
        """Perform cleanup operations, including closing all connections."""
        await self.close_all_connections()

    async def wait_for_disconnect(self, timeout: float = 5.0) -> None:
        """
        Wait for the disconnect event to be set or until the timeout is reached.

        Args:
            timeout (float): The maximum time to wait for the disconnect event.
        """
        try:
            await asyncio.wait_for(self._disconnect_event.wait(), timeout)
            logger.info("Disconnect event received")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for WebSocket disconnect")
        finally:
            self._disconnect_event.clear()

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all active WebSocket connections.

        Args:
            message (str): The message to broadcast.
        """
        self.message_queue.append(message)
        logger.info(f"Broadcasting message: {message}")
        async with self._lock:
            disconnected = []
            for websocket, user in self.active_connections.items():
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user.id}: {e}")
                    disconnected.append(websocket)

            for websocket in disconnected:
                await self.disconnect(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        """
        Send a personal message to a specific WebSocket connection.

        Args:
            message (str): The message to send.
            websocket (WebSocket): The WebSocket connection to send the message to.
        """
        try:
            await websocket.send_text(message)
            logger.info(f"Sent personal message: {message}")
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            await self.disconnect(websocket)

    def get_last_message(self) -> str:
        """
        Get the last message sent in the broadcast queue.

        Returns:
            str: The last message sent, or an empty string if no messages have been sent.
        """
        return self.message_queue[-1] if self.message_queue else ""
