from fastapi import FastAPI
from app.app import app as core_app
from contextlib import asynccontextmanager
from utils.logging import setup_logging
from utils.error_handlers import setup_error_handlers
from utils.database import init_db, close_db
from utils.cache import init_cache, close_cache
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Handles startup and shutdown processes.
    """
    # Startup
    setup_logging()  # Set up logging
    await init_db()
    await init_cache()
    yield
    # Shutdown
    await close_db()
    await close_cache()

# Create the FastAPI app instance
app = FastAPI(lifespan=lifespan)

# Include routers and set up error handlers
app.include_router(core_app.router)
setup_error_handlers(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",  # Use string reference to the app
        host=settings.HOST,
        port=settings.PORT,
        log_level="debug" if settings.DEBUG else "info",
        reload=settings.DEBUG  # Enable auto-reload in debug mode
    )