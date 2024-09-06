from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models import Base
from typing import AsyncGenerator, Callable

engine: AsyncEngine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal: Callable[..., AsyncSession] = sessionmaker(  # type: ignore
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def init_db() -> None:
    """
    Initializes the database by creating all tables defined in the models.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get a database session.
    Yields an async session that can be used in FastAPI route handlers.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def close_db() -> None:
    """
    Closes the database connection pool.
    """
    await engine.dispose()
