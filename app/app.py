"""
Main FastAPI application configuration and router setup.
"""

from fastapi import FastAPI
from app.routers import auth, health, websocket, files  # Added 'files' import
from utils.cache import init_cache, close_cache
from app.services.websocket_manager import WebSocketManager
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit_info import RateLimitInfoMiddleware
from app.middleware.error_handler import (
    validation_exception_handler,
    generic_exception_handler,
)
from app.core.logging_config import setup_logging
from fastapi.exceptions import RequestValidationError

app = FastAPI()

# Setup logging
setup_logging()

# Add RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitInfoMiddleware)


@app.on_event("startup")
async def startup_event() -> None:
    await init_cache()
    # await reset_database()  # This will recreate the database
    app.state.websocket_manager = WebSocketManager()
    websocket.init_websocket_manager(app.state.websocket_manager)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_cache()


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(health.router, tags=["health"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(
    files.router, prefix="/files", tags=["files"]
)  # Included 'files' router

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the Foxhole Backend API"}


if __name__ == "__main__":
    import uvicorn

    # Run the application with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
