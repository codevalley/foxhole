from fastapi import WebSocket
from typing import Dict, Any, Optional
import asyncio
from app.schemas.user_schema import UserInfo
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_info: Dict[str, UserInfo] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_info: UserInfo) -> None:
        async with self._lock:
            self.active_connections[user_info.id] = websocket
            self.user_info[user_info.id] = user_info
        logger.info(
            f"WebSocket connected for user {user_info.screen_name} ({user_info.id})"
        )

    async def disconnect(self, user_id: str) -> None:
        async with self._lock:
            if user_id in self.active_connections:
                del self.active_connections[user_id]
                del self.user_info[user_id]
                logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(
        self, sender_id: str, recipient_id: str, message: str
    ) -> None:
        if recipient_id in self.active_connections:
            sender_info = self.user_info.get(
                sender_id, UserInfo(id="system", screen_name="System")
            )
            await self.active_connections[recipient_id].send_json(
                {
                    "type": "personal",
                    "sender": sender_info.model_dump(),
                    "content": message,
                }
            )

    async def broadcast(
        self, sender_id: str, message: str, exclude_user: Optional[str] = None
    ) -> None:
        sender_info = self.user_info.get(
            sender_id, UserInfo(id="system", screen_name="System")
        )
        for user_id, websocket in self.active_connections.items():
            if user_id != exclude_user:
                await websocket.send_json(
                    {
                        "type": "broadcast",
                        "sender": sender_info.model_dump(),
                        "content": message,
                    }
                )

    async def handle_message(self, user_id: str, message: Dict[str, Any]) -> None:
        message_type = message.get("type")
        content = message.get("content")

        if not isinstance(content, str):
            logger.warning(f"Invalid message content type: {type(content)}")
            return

        if message_type == "broadcast":
            await self.broadcast(user_id, content)
        elif message_type == "personal":
            recipient_id = message.get("recipient_id")
            if (
                isinstance(recipient_id, str)
                and recipient_id in self.active_connections
            ):
                await self.send_personal_message(user_id, recipient_id, content)
            else:
                await self.send_personal_message(
                    "system", user_id, f"User {recipient_id} is not connected"
                )
        else:
            logger.warning(f"Unknown message type: {message_type}")

    async def send_system_message(self, user_id: str, message: str) -> None:
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(
                {
                    "type": "system",
                    "sender": {"id": "system", "screen_name": "System"},
                    "content": message,
                }
            )

    async def broadcast_system_message(
        self, message: str, exclude_user: Optional[str] = None
    ) -> None:
        await self.broadcast("system", message, exclude_user=exclude_user)
