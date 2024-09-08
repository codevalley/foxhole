"""
Main FastAPI application configuration and router setup.
"""

from fastapi import FastAPI
from app.routers import auth, files, websocket, health
from typing import Dict
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(websocket.router)
app.include_router(health.router)


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the Foxhole Backend API"}


if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.DEBUG)
    uvicorn.run(app, host="0.0.0.0", port=8000)
