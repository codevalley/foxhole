from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from app.dependencies import get_current_user_ws
from app.services.websocket_manager import WebSocketManager
import logging
from sqlalchemy.exc import SQLAlchemyError
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from utils.user_utils import get_user_info
from pydantic import BaseModel, Field
from app.core.rate_limit import limiter


router = APIRouter()
logger = logging.getLogger(__name__)

websocket_manager: Optional[WebSocketManager] = None


class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages."""

    type: str = Field(..., description="Type of the message")
    content: str = Field(..., description="Content of the message")
    recipient_id: Optional[str] = Field(
        None, description="Recipient ID for personal messages"
    )


def init_websocket_manager(manager: WebSocketManager) -> None:
    """Initialize the global WebSocketManager."""
    global websocket_manager
    websocket_manager = manager


@router.websocket("/ws")
@limiter.exempt
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)
) -> None:
    """
    WebSocket endpoint for real-time communication.
    """
    try:
        if websocket_manager is None:
            logger.error("WebSocketManager is not initialized")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        try:
            user = await get_current_user_ws(websocket, token, db)
        except SQLAlchemyError as e:
            logger.error(f"Database error occurred: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        if user is None:
            logger.error("User not found or invalid token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_info = get_user_info(user)
        await websocket.accept()
        await websocket_manager.connect(websocket, user_info)

        try:
            await websocket_manager.broadcast_system_message(
                f"{user_info.screen_name} has joined the chat",
                exclude_user=user_info.id,
            )

            while True:
                raw_data = await websocket.receive_json()
                try:
                    data = WebSocketMessage(**raw_data)
                    logger.debug(
                        f"Received WebSocket message from {user_info.screen_name} ({user_info.id}): {data}"
                    )
                    await websocket_manager.handle_message(user_info.id, data.dict())
                except ValueError as e:
                    logger.warning(f"Invalid message format: {e}")
                    await websocket.send_json({"error": "Invalid message format"})
        except WebSocketDisconnect:
            logger.info(
                f"WebSocket disconnected for user {user_info.screen_name} ({user_info.id})"
            )
        finally:
            await websocket_manager.disconnect(user_info.id)
            await websocket_manager.broadcast_system_message(
                f"{user_info.screen_name} has left the chat"
            )
    except Exception as e:
        logger.exception(f"Unexpected error occurred: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
