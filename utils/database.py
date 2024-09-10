from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from app.core.config import settings
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from app.models import Base  # Import Base from models
import os

engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with get_session() as session:
        yield session


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def reset_database() -> None:
    # Delete the existing database file
    if os.path.exists(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")):
        os.remove(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", ""))

    # Create new tables
    await create_tables()
