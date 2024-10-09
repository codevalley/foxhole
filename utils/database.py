from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from app.core.config import settings
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from app.models import Base
import os


engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
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
    print("Database tables created successfully")


async def reset_database() -> None:
    # Delete the existing database file
    db_file = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Deleted existing database file: {db_file}")

    # Create new tables
    await create_tables()


# Function to initialize the database
async def init_db() -> None:
    await reset_database()


# Run database initialization
# asyncio.run(init_db())
