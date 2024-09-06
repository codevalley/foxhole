from fastapi import WebSocket
from app.models import User
from typing import Dict


class WebSocketManager:
    def __init__(self) -> None:
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user: User) -> None:
        await websocket.accept()
        self.active_connections[user.id] = websocket

    def disconnect(self, websocket: WebSocket) -> None:
        user_id = next(
            (uid for uid, ws in self.active_connections.items() if ws == websocket),
            None,
        )
        if user_id:
            del self.active_connections[user_id]

    async def broadcast(self, message: str) -> None:
        for connection in self.active_connections.values():
            await connection.send_text(message)
