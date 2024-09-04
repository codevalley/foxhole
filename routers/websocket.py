from fastapi import APIRouter, WebSocket
from services.websocket import WebSocketManager

router = APIRouter()
manager = WebSocketManager()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time communication.
    Handles connection, message broadcasting, and disconnection.
    """
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Client {client_id}: {data}")
    except Exception:
        await manager.disconnect(client_id)