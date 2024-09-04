from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    """
    Initializes the database by creating all tables defined in the models.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    """
    Dependency function to get a database session.
    Yields an async session that can be used in FastAPI route handlers.
    """
    async with AsyncSessionLocal() as session:
        yield session

async def close_db():
    """
    Closes the database connection pool.
    """
    await engine.dispose()