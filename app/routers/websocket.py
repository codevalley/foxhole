from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Query,
    status,
)
from app.dependencies import get_current_user_ws
from app.services.websocket_manager import WebSocketManager
import logging
from sqlalchemy.exc import SQLAlchemyError
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)

websocket_manager: Optional[WebSocketManager] = None


def init_websocket_manager(manager: WebSocketManager) -> None:
    global websocket_manager
    websocket_manager = manager


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)
) -> None:
    user = await get_current_user_ws(websocket, token, db)
    if user is None:
        return  # The connection has already been closed in get_current_user_ws

    if websocket_manager is None:
        logger.error("WebSocketManager is not initialized")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    try:
        await websocket_manager.connect(websocket, user)
        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message from {user.id}: {data}")
                await websocket_manager.broadcast(f"User {user.id}: {data}")
                await websocket_manager.send_personal_message(
                    f"Message sent: {data}", websocket
                )
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)
            logger.debug(f"WebSocket disconnected for user {user.id}")
            await websocket_manager.broadcast(f"User {user.id} left the chat")
    except SQLAlchemyError:
        logger.exception("Database error occurred")
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error"
        )
