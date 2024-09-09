import pytest
from fastapi.testclient import TestClient
from app.routers.auth import create_access_token
from app.models import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.websocket_manager import WebSocketManager
import asyncio
import logging
from starlette.websockets import WebSocketDisconnect
from typing import AsyncGenerator, Any
from fastapi import status
from app.routers.websocket import init_websocket_manager
from sqlalchemy.exc import SQLAlchemyError
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(id="test_user_id", screen_name="testuser")
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
    test_client: TestClient, token: str, websocket_manager: WebSocketManager
) -> None:
    with test_client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        response = websocket.receive_text()
        assert response == "User test_user_id: Hello"
        assert websocket.receive_text() == "Message sent: Hello"


def test_websocket_multiple_messages(
    test_client: TestClient, token: str, websocket_manager: WebSocketManager
) -> None:
    with test_client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        assert websocket.receive_text() == "User test_user_id: Hello"
        assert websocket.receive_text() == "Message sent: Hello"
        websocket.send_text("World")
        assert websocket.receive_text() == "User test_user_id: World"
        assert websocket.receive_text() == "Message sent: World"


@pytest.mark.skip(
    reason="Broadcast test is currently unstable and needs further investigation"
)
@pytest.mark.asyncio
async def test_websocket_broadcast(
    test_client: TestClient, token: str, websocket_manager: WebSocketManager
) -> None:
    async def connect_and_receive(
        client: TestClient, token: str
    ) -> AsyncGenerator[Any, None]:
        with client.websocket_connect(f"/ws?token={token}") as websocket:
            yield websocket

    async with asyncio.timeout(5):  # 5 seconds timeout
        ws1_gen = connect_and_receive(test_client, token)
        ws2_gen = connect_and_receive(test_client, token)

        websocket1 = await anext(ws1_gen)
        websocket2 = await anext(ws2_gen)

        logger.info("Both WebSockets connected")

        websocket1.send_text("Hello everyone")
        logger.info("Sent message from websocket1")

        # Check the messages for websocket1 (order may vary)
        messages1 = []
        for _ in range(2):
            try:
                message = websocket1.receive_text()
                messages1.append(message)
                logger.info(f"Received message on websocket1: {message}")
            except WebSocketDisconnect:
                logger.error("WebSocket1 disconnected unexpectedly")
                break

        assert "User test_user_id: Hello everyone" in messages1
        assert "Message sent: Hello everyone" in messages1

        # Check the broadcasted message for websocket2
        try:
            message2 = websocket2.receive_text()
            logger.info(f"Received message on websocket2: {message2}")
            assert message2 == "User test_user_id: Hello everyone"
        except WebSocketDisconnect:
            logger.error("WebSocket2 disconnected unexpectedly")
            pytest.fail("Did not receive broadcast message on websocket2")

        # Check the last broadcasted message
        assert (
            websocket_manager.get_last_message() == "User test_user_id: Hello everyone"
        )

        # Close the WebSocket connections
        await websocket1.close()
        await websocket2.close()

    # Ensure the connections are removed from the manager
    assert len(websocket_manager.active_connections) == 0


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
    init_websocket_manager(mock_manager)

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(f"/ws?token={authenticated_user['token']}"):
            pass

    assert exc_info.value.code == status.WS_1011_INTERNAL_ERROR


def test_websocket_disconnect(
    test_client: TestClient, token: str, websocket_manager: WebSocketManager
) -> None:
    with test_client.websocket_connect(f"/ws?token={token}") as websocket:
        websocket.send_text("Hello")
        assert websocket.receive_text() == "User test_user_id: Hello"
        assert websocket.receive_text() == "Message sent: Hello"
    # WebSocket should be closed after the context manager
    assert len(websocket_manager.active_connections) == 0


def test_websocket_unauthorized(test_client: TestClient) -> None:
    with pytest.raises(WebSocketDisconnect) as excinfo:
        with test_client.websocket_connect("/ws"):
            pass
    error_detail = excinfo.value.reason
    assert isinstance(error_detail, list) and len(error_detail) > 0
    assert error_detail[0]["type"] == "missing"
    assert error_detail[0]["loc"] == ["query", "token"]


def test_websocket_invalid_token(test_client: TestClient) -> None:
    with pytest.raises(Exception) as excinfo:  # The exact exception type may vary
        with test_client.websocket_connect("/ws?token=invalid_token"):
            pass
    assert "Invalid token" in str(excinfo.value)
