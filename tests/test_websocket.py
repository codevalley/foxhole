import pytest
from fastapi.testclient import TestClient
from app.routers.auth import create_access_token
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.websocket_manager import WebSocketManager
import asyncio
import logging
from starlette.websockets import WebSocketDisconnect
from typing import Any
from fastapi import status
from app.routers.websocket import init_websocket_manager
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import patch, MagicMock, AsyncMock
import uuid

logger = logging.getLogger(__name__)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(id=str(uuid.uuid4()), screen_name="testuser")
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
def token(test_user: User) -> str:
    return create_access_token({"sub": test_user.id})


@pytest.fixture
def websocket_manager() -> WebSocketManager:
    return WebSocketManager()


def test_websocket_connection(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        response = websocket.receive_text()
        assert response == f"User {test_user.id}: Hello"
        assert websocket.receive_text() == "Message sent: Hello"


def test_websocket_multiple_messages(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    with client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        assert websocket.receive_text() == f"User {test_user.id}: Hello"
        assert websocket.receive_text() == "Message sent: Hello"
        websocket.send_text("World")
        assert websocket.receive_text() == f"User {test_user.id}: World"
        assert websocket.receive_text() == "Message sent: World"


@pytest.mark.asyncio
async def test_websocket_disconnect(
    client: TestClient, token: str, websocket_manager: WebSocketManager, test_user: User
) -> None:
    real_websocket_manager = WebSocketManager()
    init_websocket_manager(real_websocket_manager)

    async def connection_task() -> None:
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            websocket.send_text("Hello")
            messages = []

            for _ in range(2):
                message = websocket.receive_text()
                messages.append(message)

            assert len(messages) == 2, f"Expected 2 messages, got {len(messages)}"
            assert (
                messages[0] == f"User {test_user.id}: Hello"
            ), f"Unexpected response: {messages[0]}"
            assert (
                messages[1] == "Message sent: Hello"
            ), f"Unexpected response: {messages[1]}"

    async def disconnect_task() -> None:
        await asyncio.sleep(1)  # Give some time for the connection to be established
        await real_websocket_manager.close_all_connections()

    await asyncio.gather(connection_task(), disconnect_task())

    # Wait for the disconnect event with a timeout
    await real_websocket_manager.wait_for_disconnect(timeout=2.0)

    assert len(real_websocket_manager.active_connections) == 0, (
        f"WebSocket connection not closed properly. "
        f"Active connections: {real_websocket_manager.active_connections}"
    )


@pytest.mark.asyncio
async def test_websocket_endpoint_uninitialized_manager(
    client: TestClient,
    authenticated_user: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.routers.websocket.websocket_manager", None)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws?token={authenticated_user['token']}"):
            pass

    assert exc_info.value.code == status.WS_1011_INTERNAL_ERROR


@pytest.mark.asyncio
async def test_websocket_endpoint_sqlalchemy_error(
    client: TestClient,
    authenticated_user: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_manager = MagicMock(spec=WebSocketManager)
    mock_manager.connect.side_effect = SQLAlchemyError("Database error")
    mock_manager.active_connections = {}
    mock_manager.disconnect = AsyncMock()

    with patch("app.routers.websocket.websocket_manager", mock_manager):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect(f"/ws?token={authenticated_user['token']}"):
                pass

        assert exc_info.value.code == status.WS_1011_INTERNAL_ERROR

    mock_manager.disconnect.assert_not_called()


def test_websocket_unauthorized(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws"):
            pass
    error_detail = excinfo.value.reason
    assert isinstance(error_detail, list) and len(error_detail) > 0
    assert error_detail[0]["type"] == "missing"
    assert error_detail[0]["loc"] == ["query", "token"]


def test_websocket_invalid_token(client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with client.websocket_connect("/ws?token=invalid_token"):
            pass
    assert excinfo.value.code == status.WS_1008_POLICY_VIOLATION
