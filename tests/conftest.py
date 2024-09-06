import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from app.models import Base
import asyncio
from httpx import AsyncClient
from fastapi import FastAPI
from main import app as fastapi_app
from app.schemas.user_schema import UserCreate, UserResponse, Token  # noqa: F401
from typing import AsyncGenerator, Generator, Callable  # noqa: F401

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    return create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="session")
async def create_tables(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def db_session(
    engine: AsyncEngine, create_tables: None
) -> AsyncGenerator[AsyncSession, None]:
    async_session: Callable[..., AsyncSession] = sessionmaker(  # type: ignore
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def app(db_session: AsyncSession) -> FastAPI:
    from utils.database import get_db
    from utils.cache import get_cache
    from fakeredis.aioredis import FakeRedis

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[get_cache] = lambda: FakeRedis()

    return fastapi_app


@pytest.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
