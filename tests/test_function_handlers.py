"""
Unit tests for OpenAI function handlers.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.function_handlers import (
    GetPeopleHandler,
    GetTasksHandler,
    GetTopicsHandler,
    GetNotesHandler,
    FUNCTION_HANDLERS,
)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock database session"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def user_id() -> str:
    """Sample user ID for tests"""
    return "test_user_123"


class TestGetPeopleHandler:
    @pytest.mark.asyncio
    async def test_get_people_no_params(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "person_id": "p1",
                    "name": "John Doe",
                    "designation": "Engineer",
                    "relation_type": "colleague",
                    "importance": "high",
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetPeopleHandler(mock_db, user_id)

        # Act
        result = await handler.handle({})

        # Assert
        assert result["total"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["name"] == "John Doe"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_people_with_filters(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "person_id": "p1",
                    "name": "John Doe",
                    "designation": "Engineer",
                    "relation_type": "colleague",
                    "importance": "high",
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetPeopleHandler(mock_db, user_id)

        # Act
        result = await handler.handle({"name": "John", "importance": "high"})

        # Assert
        assert result["total"] == 1
        assert result["results"][0]["importance"] == "high"
        mock_db.execute.assert_called_once()


class TestGetTasksHandler:
    @pytest.mark.asyncio
    async def test_get_tasks_no_params(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "task_id": "t1",
                    "type": "1",
                    "description": "Test task",
                    "status": "active",
                    "priority": "high",
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetTasksHandler(mock_db, user_id)

        # Act
        result = await handler.handle({})

        # Assert
        assert result["total"] == 1
        assert result["results"][0]["task_id"] == "t1"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_tasks_with_filters(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "task_id": "t1",
                    "type": "1",
                    "description": "Test task",
                    "status": "active",
                    "priority": "high",
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetTasksHandler(mock_db, user_id)

        # Act
        result = await handler.handle({"status": "active", "priority": "high"})

        # Assert
        assert result["total"] == 1
        assert result["results"][0]["status"] == "active"
        mock_db.execute.assert_called_once()


class TestGetTopicsHandler:
    @pytest.mark.asyncio
    async def test_get_topics_no_params(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "topic_id": "top1",
                    "name": "Test Topic",
                    "description": "Test description",
                    "keywords": ["test", "topic"],
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetTopicsHandler(mock_db, user_id)

        # Act
        result = await handler.handle({})

        # Assert
        assert result["total"] == 1
        assert result["results"][0]["topic_id"] == "top1"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_topics_with_filters(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "topic_id": "top1",
                    "name": "Test Topic",
                    "description": "Test description",
                    "keywords": ["test", "topic"],
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetTopicsHandler(mock_db, user_id)

        # Act
        result = await handler.handle({"keyword": "test", "name": "Test Topic"})

        # Assert
        assert result["total"] == 1
        assert "test" in result["results"][0]["keywords"]
        mock_db.execute.assert_called_once()


class TestGetNotesHandler:
    @pytest.mark.asyncio
    async def test_get_notes_no_params(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "note_id": "n1",
                    "content": "Test note",
                    "related_topics": ["top1"],
                    "related_people": ["p1"],
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetNotesHandler(mock_db, user_id)

        # Act
        result = await handler.handle({})

        # Assert
        assert result["total"] == 1
        assert result["results"][0]["note_id"] == "n1"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_notes_with_filters(self, mock_db, user_id):
        # Arrange
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            MagicMock(
                to_dict=lambda: {
                    "note_id": "n1",
                    "content": "Test note",
                    "related_topics": ["top1"],
                    "related_people": ["p1"],
                }
            )
        ]
        mock_db.execute.return_value = mock_result
        handler = GetNotesHandler(mock_db, user_id)

        # Act
        result = await handler.handle({"query": "Test", "related_topic": "top1"})

        # Assert
        assert result["total"] == 1
        assert "top1" in result["results"][0]["related_topics"]
        mock_db.execute.assert_called_once()


class TestFunctionRegistry:
    def test_all_handlers_registered(self):
        """Test that all required handlers are in the registry"""
        expected_handlers = {
            "get_people": GetPeopleHandler,
            "get_tasks": GetTasksHandler,
            "get_topics": GetTopicsHandler,
            "get_notes": GetNotesHandler,
        }
        assert FUNCTION_HANDLERS == expected_handlers

    @pytest.mark.asyncio
    async def test_handler_instantiation(self, mock_db, user_id):
        """Test that all handlers can be instantiated and called"""
        for handler_class in FUNCTION_HANDLERS.values():
            handler = handler_class(mock_db, user_id)
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_db.execute.return_value = mock_result

            result = await handler.handle({})
            assert "results" in result
            assert "total" in result
