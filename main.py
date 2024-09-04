from fastapi import FastAPI
from app.main import app as core_app  # Import the app from app/main.py
from contextlib import asynccontextmanager
from utils.logging import setup_logging
from utils.error_handlers import setup_error_handlers
from utils.database import init_db, close_db
from utils.cache import init_cache, close_cache
from routers import health, auth, websocket

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

# Apply the lifespan to the imported app
core_app.router.lifespan = lifespan

# Set up routers
core_app.include_router(health.router)
core_app.include_router(auth.router, prefix="/auth", tags=["auth"])
core_app.include_router(websocket.router)

# Set up error handlers
setup_error_handlers(core_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(core_app, host="0.0.0.0", port=8000)