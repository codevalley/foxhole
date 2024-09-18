"""
Main FastAPI application configuration and router setup.
"""

from fastapi import FastAPI
from app.routers import auth, files, websocket, health
from app.services.websocket_manager import WebSocketManager
from typing import Dict
import logging
from fastapi.exceptions import RequestValidationError
from app.middleware.error_handler import (
    validation_exception_handler,
    generic_exception_handler,
)

app = FastAPI()
logger = logging.getLogger(__name__)

# Create WebSocketManager instance
app.state.websocket_manager = WebSocketManager()

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(websocket.router)
app.include_router(health.router)

# Pass WebSocketManager instance to websocket router
websocket.init_websocket_manager(app.state.websocket_manager)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the Foxhole Backend API"}


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8000)
