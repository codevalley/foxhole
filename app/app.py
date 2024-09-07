"""
Main FastAPI application configuration and router setup.
"""
from fastapi import FastAPI
from app.routers import websocket, files, health, auth  # Updated import
from app.dependencies import get_storage_service
from typing import Dict

app = FastAPI()

# Dependency injection for storage service
app.dependency_overrides[get_storage_service] = get_storage_service

# Include routers
app.include_router(websocket.router)
app.include_router(files.router, prefix="/files")
app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to the Foxhole Backend API"}
