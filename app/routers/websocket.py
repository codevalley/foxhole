from fastapi import APIRouter, WebSocket, Depends
from app.dependencies import get_current_user_ws
from app.models import User

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, current_user: User = Depends(get_current_user_ws)
) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except Exception:
        await websocket.close()
