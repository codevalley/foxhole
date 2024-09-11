from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
from app.dependencies import get_current_user_ws
from app.services.websocket_manager import WebSocketManager
import logging
from sqlalchemy.exc import SQLAlchemyError
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from utils.user_utils import get_user_info

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
    try:
        logger.info(f"WebSocket connection attempt with token: {token}")
        user = await get_current_user_ws(websocket, token, db)
        if user is None:
            logger.error("User not found or invalid token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_info = get_user_info(user)

        if websocket_manager is None:
            logger.error("WebSocketManager is not initialized")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        logger.info(f"User {user_info.screen_name} ({user_info.id}) connected")
        await websocket_manager.connect(websocket, user_info)

        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(
                    f"Received WebSocket message from {user_info.screen_name} ({user_info.id}): {data}"
                )

                # Send acknowledgment
                await websocket.send_text("ACK: Message received")

                await websocket_manager.broadcast(f"{user_info.screen_name}: {data}")
        except WebSocketDisconnect as e:
            logger.info(
                f"WebSocket disconnected for user {user_info.screen_name} ({user_info.id}). Code: {e.code}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error in WebSocket connection for user {user_info.screen_name} ({user_info.id}): {str(e)}",
                exc_info=True,
            )
        finally:
            logger.info(
                f"Cleaning up connection for user {user_info.screen_name} ({user_info.id})"
            )
            await websocket_manager.disconnect(websocket)
            await websocket_manager.broadcast(f"{user_info.screen_name} left the chat")
    except SQLAlchemyError as e:
        logger.exception(f"Database error occurred: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    except Exception as e:
        logger.exception(f"Unexpected error occurred: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
