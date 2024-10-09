from fastapi import FastAPI
from app.routers import auth, health, websocket, sidekick
from utils.cache import init_cache, close_cache
from app.services.websocket_manager import WebSocketManager
from app.middleware.request_id import RequestIDMiddleware
from app.core.logging_config import setup_logging
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.rate_limit import limiter
from app.middleware.rate_limit_info import RateLimitInfoMiddleware

app = FastAPI()


# Add RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add RateLimitInfoMiddleware
app.add_middleware(RateLimitInfoMiddleware)


@app.on_event("startup")
async def startup_event() -> None:
    await init_cache()
    # await reset_database()  # This will recreate the database
    # await init_db()
    app.state.websocket_manager = WebSocketManager()
    websocket.init_websocket_manager(app.state.websocket_manager)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_cache()


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(health.router, tags=["health"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(sidekick.router, tags=["sidekick"])

if __name__ == "__main__":
    import uvicorn
    from app.app import app

    # Configure logging
    setup_logging()

    # Run the application with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
