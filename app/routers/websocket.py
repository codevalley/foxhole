from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Query,
    HTTPException,
    status,
)
from app.dependencies import get_current_user_ws
import logging
from sqlalchemy.exc import SQLAlchemyError
from utils.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)
) -> None:
    try:
        await get_current_user_ws(token, db)
        await websocket.accept()
        try:
            while True:
                data = await websocket.receive_text()
                logger.debug(f"Received WebSocket message: {data}")
                await websocket.send_text(f"Message received: {data}")
        except WebSocketDisconnect:
            logger.debug("WebSocket disconnected")
    except HTTPException as e:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION, reason=str(e.detail)
        )
    except SQLAlchemyError:
        logger.exception("Database error occurred")
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR, reason="Internal server error"
        )
