import logging
from fastapi import WebSocket
from typing import Dict, List
import asyncio
from app.schemas.user_schema import UserInfo

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: Dict[WebSocket, UserInfo] = {}
        self.message_queue: List[str] = []
        self._lock = asyncio.Lock()
        self._disconnect_event = asyncio.Event()

    async def connect(self, websocket: WebSocket, user_info: UserInfo) -> None:
        try:
            await websocket.accept()
            async with self._lock:
                self.active_connections[websocket] = user_info
            logger.info(
                f"WebSocket connected for user {user_info.screen_name} ({user_info.id}). Total connections: {len(self.active_connections)}"
            )
        except Exception as e:
            logger.error(
                f"Error accepting WebSocket connection for user {user_info.screen_name} ({user_info.id}): {str(e)}",
                exc_info=True,
            )
            raise

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            if websocket in self.active_connections:
                user_info = self.active_connections.pop(websocket)
                logger.info(
                    f"WebSocket disconnected for user {user_info.screen_name} ({user_info.id}). Remaining connections: {len(self.active_connections)}"
                )
            else:
                logger.warning(
                    "Attempted to disconnect a WebSocket that was not in active connections"
                )

        try:
            await websocket.close()
        except RuntimeError as e:
            if "Unexpected ASGI message 'websocket.close'" in str(e):
                logger.warning(
                    "WebSocket was already closed or in the process of closing"
                )
            else:
                logger.error(f"Error closing WebSocket: {str(e)}", exc_info=True)
        except Exception as e:
            logger.error(f"Error closing WebSocket: {str(e)}", exc_info=True)

        if not self.active_connections:
            self._disconnect_event.set()

    async def broadcast(self, message: str) -> None:
        self.message_queue.append(message)
        logger.info(f"Broadcasting message: {message}")
        async with self._lock:
            disconnected = []
            for websocket, user_info in self.active_connections.items():
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.error(
                        f"Error sending message to user {user_info.screen_name} ({user_info.id}): {str(e)}",
                        exc_info=True,
                    )
                    disconnected.append(websocket)

            for websocket in disconnected:
                await self.disconnect(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket) -> None:
        try:
            await websocket.send_text(message)
            logger.info(f"Sent personal message: {message}")
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}", exc_info=True)
            await self.disconnect(websocket)

    async def close_all_connections(self) -> None:
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
        await self.close_all_connections()

    async def wait_for_disconnect(self, timeout: float = 5.0) -> None:
        try:
            await asyncio.wait_for(self._disconnect_event.wait(), timeout)
            logger.info("Disconnect event received")
        except asyncio.TimeoutError:
            logger.warning("Timeout waiting for WebSocket disconnect")
        finally:
            self._disconnect_event.clear()

    def get_last_message(self) -> str:
        return self.message_queue[-1] if self.message_queue else ""
