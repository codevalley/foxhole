from fastapi import FastAPI
from app.routers import auth, health, websocket, sidekick, files
from utils.cache import init_cache, close_cache
from app.services.websocket_manager import WebSocketManager
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.rate_limit_info import RateLimitInfoMiddleware
from utils.database import check_and_create_tables
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter
from app.middleware.error_handler import (
    validation_exception_handler,
    generic_exception_handler,
)
from fastapi.exceptions import RequestValidationError
import logging
from app.core.config import settings

# Configure logging at application startup


def setup_logging() -> None:
    # Set the root logger level
    logging.getLogger().setLevel(settings.LOG_LEVEL)

    # Configure the format
    formatter = logging.Formatter(settings.LOG_FORMAT)

    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    console_handler.setFormatter(formatter)

    # Remove any existing handlers and add our console handler
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Set specific loggers to ERROR level only
    logging.getLogger("uvicorn.access").setLevel(logging.ERROR)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)
    logging.getLogger("fastapi").setLevel(logging.ERROR)


app = FastAPI()

# Setup logging before anything else
setup_logging()

# Add middlewares
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitInfoMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.on_event("startup")
async def startup_event() -> None:
    await init_cache()
    await check_and_create_tables()
    app.state.websocket_manager = WebSocketManager()
    websocket.init_websocket_manager(app.state.websocket_manager)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_cache()


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(health.router, tags=["health"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(sidekick.router, prefix="/api/v1/sidekick", tags=["sidekick"])

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the Foxhole Backend API"}


if __name__ == "__main__":
    import uvicorn

    # Run the application with Uvicorn
    uvicorn.run(
        "main:app", host="0.0.0.0", port=8000, log_level=settings.LOG_LEVEL.lower()
    )
