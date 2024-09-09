from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, status
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
    """
    Initialize the global WebSocket manager.

    Args:
        manager (WebSocketManager): The WebSocket manager instance to use.
    """
    global websocket_manager
    websocket_manager = manager


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)
) -> None:
    """
    Handle WebSocket connections and messages.

    Args:
        websocket (WebSocket): The WebSocket connection.
        token (str): The authentication token.
        db (AsyncSession): The database session.
    """
    try:
        logger.info(f"WebSocket connection attempt with token: {token}")
        user = await get_current_user_ws(websocket, token, db)
        if user is None:
            logger.error("User not found or invalid token")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if websocket_manager is None:
            logger.error("WebSocketManager is not initialized")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        logger.info(f"User {user.id} connected")
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
            logger.info(f"WebSocket disconnected for user {user.id}")
        except Exception as e:
            logger.error(
                f"Unexpected error in WebSocket connection for user {user.id}: {e}"
            )
        finally:
            await websocket_manager.disconnect(websocket)
            await websocket_manager.broadcast(f"User {user.id} left the chat")
    except SQLAlchemyError as e:
        logger.exception(f"Database error occurred: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
    except Exception as e:
        logger.exception(f"Unexpected error occurred: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
