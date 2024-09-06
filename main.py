from fastapi import FastAPI
from app.routers import auth, health
from utils.database import init_db, close_db
from utils.cache import init_cache, close_cache

app = FastAPI()


@app.on_event("startup")
async def startup_event() -> None:
    await init_db()
    await init_cache()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await close_db()
    await close_cache()


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(health.router)
