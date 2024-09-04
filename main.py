from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager
from routers import health, auth, websocket
from utils.logging import setup_logging
from utils.error_handlers import setup_error_handlers
from utils.database import init_db, close_db
from utils.cache import init_cache, close_cache

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown processes.
    """
    # Startup
    setup_logging()
    await init_db()
    await init_cache()
    yield
    # Shutdown
    await close_db()
    await close_cache()

app = FastAPI(lifespan=lifespan)

# Set up routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(websocket.router)

# Set up error handlers
setup_error_handlers(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)