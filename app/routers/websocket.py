from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_manager import WebSocketManager
from app.routers.auth import get_current_user  # Updated import
from app.models import User

router = APIRouter()
manager = WebSocketManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, current_user: User = Depends(get_current_user)
) -> None:
    """
    WebSocket endpoint for real-time communication.
    Handles connection, message broadcasting, and disconnection.
    Requires authentication.
    """
    await manager.connect(websocket, current_user)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message from {current_user.username}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"User {current_user.username} disconnected")
