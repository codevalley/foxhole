from fastapi import FastAPI
from app.routers import websocket, files
from app.dependencies import get_storage_service

app = FastAPI()

# Dependency injection for storage service
app.dependency_overrides[get_storage_service] = get_storage_service

# Include routers
app.include_router(websocket.router)
app.include_router(files.router, prefix="/files")

@app.get("/")
async def root():
    """
    Root endpoint for the API.
    
    Returns:
        dict: A welcome message.
    """
    return {"message": "Welcome to the Foxhole Backend API"}