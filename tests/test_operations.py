import pytest
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.operations import (
    get_user_by_id,
    get_user_by_secret,
    create_user,
    update_user,
)
from app.models import User
import uuid

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(screen_name="testuser", user_secret=User.generate_user_secret())
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def test_get_user_by_id(db_session: AsyncSession, test_user: User) -> None:
    user = await get_user_by_id(db_session, test_user.id)
    assert user is not None
    assert user.id == test_user.id
    assert user.screen_name == test_user.screen_name


async def test_get_user_by_id_not_found(db_session: AsyncSession) -> None:
    non_existent_id = str(uuid.uuid4())
    user = await get_user_by_id(db_session, non_existent_id)
    assert user is None


async def test_get_user_by_secret(db_session: AsyncSession, test_user: User) -> None:
    user = await get_user_by_secret(db_session, test_user.user_secret)
    assert user is not None
    assert user.id == test_user.id
    assert user.screen_name == test_user.screen_name


async def test_get_user_by_secret_not_found(db_session: AsyncSession) -> None:
    non_existent_secret = User.generate_user_secret()
    user = await get_user_by_secret(db_session, non_existent_secret)
    assert user is None


async def test_create_user(db_session: AsyncSession) -> None:
    new_user = await create_user(db_session, "newuser")
    assert new_user is not None
    assert new_user.screen_name == "newuser"
    assert new_user.user_secret is not None

    # Verify the user was actually created in the database
    created_user = await get_user_by_id(db_session, new_user.id)
    assert created_user is not None
    assert created_user.screen_name == "newuser"


async def test_update_user(db_session: AsyncSession, test_user: User) -> None:
    updated_user = await update_user(db_session, test_user, screen_name="updateduser")
    assert updated_user is not None
    assert updated_user.id == test_user.id
    assert updated_user.screen_name == "updateduser"

    # Verify the user was actually updated in the database
    db_user = await get_user_by_id(db_session, test_user.id)
    assert db_user is not None
    assert db_user.screen_name == "updateduser"


async def test_update_user_no_changes(
    db_session: AsyncSession, test_user: User
) -> None:
    updated_user = await update_user(db_session, test_user)
    assert updated_user is not None
    assert updated_user.id == test_user.id
    assert updated_user.screen_name == test_user.screen_name


async def test_update_user_invalid_field(
    db_session: AsyncSession, test_user: User
) -> None:
    updated_user = await update_user(
        db_session, test_user, id="new_id", user_secret="new_secret"
    )
    assert updated_user is not None
    assert updated_user.id == test_user.id
    assert updated_user.user_secret == test_user.user_secret


# Error cases
async def test_get_user_by_id_error(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_execute(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "execute", mock_execute)
    user = await get_user_by_id(db_session, "some_id")
    assert user is None


async def test_get_user_by_secret_error(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_execute(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "execute", mock_execute)
    user = await get_user_by_secret(db_session, "some_secret")
    assert user is None


async def test_create_user_error(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)
    new_user = await create_user(db_session, "erroruser")
    assert new_user is None


async def test_update_user_error(
    db_session: AsyncSession, test_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)
    updated_user = await update_user(db_session, test_user, screen_name="erroruser")
    assert updated_user is None
