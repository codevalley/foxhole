import warnings
import pytest
from fastapi.testclient import TestClient
from app.routers.auth import create_access_token
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.websocket_manager import WebSocketManager
import asyncio
import logging
from starlette.websockets import WebSocketDisconnect
from fastapi import status
from app.routers.websocket import init_websocket_manager
from sqlalchemy.exc import SQLAlchemyError
import uuid
from typing import Any
from app.core.constants import SYSTEM_USER_ID  # Add this import


warnings.filterwarnings("ignore", category=DeprecationWarning, module="jose.jwt")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="minio.time")

logger = logging.getLogger(__name__)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user_id = str(uuid.uuid4())
    user = User(id=user_id, screen_name="testuser")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def token(test_user: User) -> str:
    return create_access_token({"sub": test_user.id})


@pytest.fixture
def websocket_manager() -> WebSocketManager:
    return WebSocketManager()


@pytest.mark.asyncio
async def test_websocket_connection(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    init_websocket_manager(websocket_manager)
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_json({"type": "broadcast", "content": "Hello"})
        response = websocket.receive_json()
        assert response["type"] == "broadcast"
        assert response["content"] == "Hello"
        assert response["sender"]["screen_name"] == test_user.screen_name
        assert response["sender"]["id"] == test_user.id  # Ensure sender is the user


@pytest.mark.asyncio
async def test_websocket_disconnect(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    init_websocket_manager(websocket_manager)
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_json({"type": "broadcast", "content": "Hello"})
        websocket.receive_json()

    # Give some time for the disconnect to process
    await asyncio.sleep(0.1)

    assert test_user.id not in websocket_manager.active_connections


@pytest.mark.asyncio
async def test_websocket_personal_message(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    init_websocket_manager(websocket_manager)
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        recipient_id = str(uuid.uuid4())
        websocket.send_json(
            {"type": "personal", "content": "Hello", "recipient_id": recipient_id}
        )
        response = websocket.receive_json()
        assert response["type"] == "personal"
        assert response["content"].startswith("User")
        assert response["sender"]["id"] == SYSTEM_USER_ID  # Correct expectation


@pytest.mark.asyncio
async def test_websocket_multiple_messages(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    init_websocket_manager(websocket_manager)
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        # First broadcast
        websocket.send_json({"type": "broadcast", "content": "Hello"})
        response1 = websocket.receive_json()
        assert response1["type"] == "broadcast"
        assert response1["content"] == "Hello"
        assert response1["sender"]["id"] == test_user.id  # Updated to expect user ID

        # Second broadcast
        websocket.send_json({"type": "broadcast", "content": "World"})
        response2 = websocket.receive_json()
        assert response2["type"] == "broadcast"
        assert response2["content"] == "World"
        assert response2["sender"]["id"] == test_user.id  # Updated to expect user ID


@pytest.mark.asyncio
async def test_websocket_invalid_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws?token=invalid_token"):
            pass
    assert excinfo.value.code == status.WS_1008_POLICY_VIOLATION


@pytest.mark.asyncio
async def test_websocket_uninitialized_manager(
    client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.routers.websocket.websocket_manager", None)
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/ws?token={token}"):
            pass
    assert excinfo.value.code == status.WS_1011_INTERNAL_ERROR


@pytest.mark.asyncio
async def test_websocket_sqlalchemy_error(
    client: TestClient, token: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_get_current_user_ws(*args: Any, **kwargs: Any) -> None:
        raise SQLAlchemyError("Database error")

    monkeypatch.setattr(
        "app.dependencies.get_current_user_ws", mock_get_current_user_ws
    )

    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            # Force the websocket to process the connection
            websocket.send_text("test")
            websocket.receive_text()

    assert excinfo.value.code == status.WS_1011_INTERNAL_ERROR


@pytest.mark.asyncio
async def test_websocket_invalid_json(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    init_websocket_manager(websocket_manager)
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            websocket.send_text("Invalid JSON")
            websocket.receive_json()


def test_websocket_unauthorized(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws"):
            pass
    # Since WebSocketDisconnect.reason is a string, adjust the assertion
    assert excinfo.value.code == status.WS_1008_POLICY_VIOLATION
