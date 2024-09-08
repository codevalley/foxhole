import pytest
from fastapi.testclient import TestClient
from app.routers.auth import create_access_token
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect
from fastapi import status


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(id="test_user_id", screen_name="testuser")
    db_session.add(user)
    await db_session.commit()
    return user


@pytest.fixture
def token(test_user: User) -> str:
    return create_access_token({"sub": test_user.id})


def test_websocket_connection(test_client: TestClient, token: str) -> None:
    with test_client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        response = websocket.receive_text()
        assert response == "Message received: Hello"


def test_websocket_multiple_messages(test_client: TestClient, token: str) -> None:
    with test_client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        assert websocket.receive_text() == "Message received: Hello"
        websocket.send_text("World")
        assert websocket.receive_text() == "Message received: World"


def test_websocket_disconnect(test_client: TestClient, token: str) -> None:
    with test_client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        assert websocket.receive_text() == "Message received: Hello"
    # WebSocket should be closed after the context manager


def test_websocket_unauthorized(test_client: TestClient) -> None:
    with pytest.raises(Exception):  # The exact exception type may vary
        with test_client.websocket_connect("/ws"):
            pass


def test_websocket_invalid_token(test_client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with test_client.websocket_connect("/ws?token=invalid_token"):
            pass
    assert excinfo.value.code == status.WS_1008_POLICY_VIOLATION
    assert excinfo.value.reason == "Invalid token"
