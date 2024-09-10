from fastapi import FastAPI
from app.routers import auth, health, websocket
from utils.cache import init_cache, close_cache
from utils.database import reset_database
from app.services.websocket_manager import WebSocketManager

app = FastAPI()


@app.on_event("startup")
async def startup_event() -> None:
    await init_cache()
    await reset_database()  # This will recreate the database
    app.state.websocket_manager = WebSocketManager()
    websocket.init_websocket_manager(app.state.websocket_manager)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_cache()


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(health.router)
app.include_router(websocket.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
