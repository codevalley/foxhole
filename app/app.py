"""
Main FastAPI application configuration and router setup.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from app.routers import websocket, files, health, auth
from app.dependencies import get_current_user_ws
from app.models import User
from typing import Dict
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

# Include routers
app.include_router(websocket.router)
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the Foxhole Backend API"}


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, current_user: User = Depends(get_current_user_ws)
) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        logger.debug("WebSocket disconnected")


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8000)
