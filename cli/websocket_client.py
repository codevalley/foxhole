import asyncio
import json
import websockets
from ui import print_message
from cli.config import Config
from typing import Optional


class WebSocketClient:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.task: Optional[asyncio.Task] = None

    async def connect(self, token: str) -> None:
        uri = f"ws://{self.config.WEBSOCKET_HOST}/ws?token={token}"  # noqa : E231
        self.ws = await websockets.connect(uri)
        self.task = asyncio.create_task(self.receive_messages())

    async def disconnect(self) -> None:
        if self.ws:
            await self.ws.close()
        if self.task:
            self.task.cancel()

    async def send_message(
        self, message_type: str, content: str, recipient_id: Optional[str] = None
    ) -> None:
        if not self.ws:
            print_message("Not connected to WebSocket", "error")
            return
        message = {"type": message_type, "content": content}
        if recipient_id:
            message["recipient_id"] = recipient_id
        await self.ws.send(json.dumps(message))

    async def receive_messages(self) -> None:
        try:
            while self.ws:
                message = await self.ws.recv()
                data = json.loads(message)
                sender = data.get("sender", {}).get("screen_name", "Unknown")
                content = data.get("content", "")
                message_type = data.get("type", "")

                if message_type == "broadcast":
                    print_message(content, "info", sender)
                elif message_type == "personal":
                    print_message(content, "info", f"DM from {sender}")
                elif message_type == "system":
                    print_message(content, "info", "SYSTEM")
        except websockets.exceptions.ConnectionClosed:
            print_message("WebSocket connection closed", "error")
        except asyncio.CancelledError:
            pass
