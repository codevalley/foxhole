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
import logging

logger = logging.getLogger(__name__)

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL, echo=False, future=True
)

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


async def check_and_create_tables() -> None:
    """
    Check if database exists and create tables if they don't exist.
    Does not drop or recreate tables if they already exist.
    """
    try:
        db_file = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
        db_dir = os.path.dirname(db_file)

        # Ensure the data directory exists
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
            logger.info(f"Created database directory: {db_dir}")

        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables checked/created successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


async def reset_database() -> None:
    # Delete the existing database file
    db_file = settings.DATABASE_URL.replace("sqlite+aiosqlite:///", "")
    if os.path.exists(db_file):
        os.remove(db_file)
        print(f"Deleted existing database file: {db_file}")

    # Create new tables
    await check_and_create_tables()


# Function to initialize the database
async def init_db() -> None:
    await reset_database()


# Run database initialization
# asyncio.run(init_db())
