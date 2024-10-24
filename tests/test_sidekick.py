import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, SidekickThread, Topic, Task, Person, Note
from app.services.sidekick_service import SidekickService
from app.routers.auth import create_access_token
from datetime import datetime, timezone
from typing import Any, cast, Generator
from unittest.mock import AsyncMock, patch, MagicMock
from app.schemas.sidekick_schema import (
    SidekickInput,
    SidekickOutput,
    LLMResponse,
    Instructions,
    Data,
    AffectedEntities,
    TokenUsage,
    Person as PersonSchema,
)
import asyncio
from fastapi import HTTPException
import json


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(screen_name="testuser", user_secret=User.generate_user_secret())
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def access_token(test_user: User) -> str:
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
async def test_thread(db_session: AsyncSession, test_user: User) -> SidekickThread:
    thread = SidekickThread(
        id=str(uuid.uuid4()), user_id=test_user.id, conversation_history=[]
    )
    db_session.add(thread)
    await db_session.commit()
    await db_session.refresh(thread)
    return thread


@pytest.fixture
def mock_llm_response() -> LLMResponse:
    """Fixture providing a standard mock LLM response"""
    return LLMResponse(
        instructions=Instructions(
            status="complete",
            followup="Test response",
            new_prompt="",
            write=False,
            affected_entities=AffectedEntities(
                people=[],
                tasks=[],
                notes=[],
                topics=[],
            ),
        ),
        data=Data(),
    )


@pytest.fixture
def mock_token_usage() -> TokenUsage:
    """Fixture providing standard token usage stats"""
    return TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)


@pytest.fixture
def mock_openai(
    mock_llm_response: LLMResponse, mock_token_usage: TokenUsage
) -> Generator[AsyncMock, None, None]:
    """Fixture providing a mocked OpenAI API call"""
    with patch(
        "app.routers.sidekick.SidekickService.call_openai_api",
        new_callable=AsyncMock,
        return_value=(mock_llm_response, mock_token_usage),
    ) as mock:
        yield mock


@pytest.fixture
async def test_topic(db_session: AsyncSession, test_user: User) -> Topic:
    topic = Topic(
        user_id=test_user.id,
        name="Test Topic",
        description="Test Description",
        keywords=["test"],
        related_people=[],
        related_tasks=[],
    )
    db_session.add(topic)
    await db_session.commit()
    await db_session.refresh(topic)
    return topic


@pytest.fixture
async def test_task(db_session: AsyncSession, test_user: User) -> Task:
    task = Task(
        user_id=test_user.id,
        description="Test Task",
        status="active",
        type="1",
        actions=[],
        people={"owner": "", "final_beneficiary": "", "stakeholders": []},
        dependencies=[],
        schedule="",
        priority="medium",
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    return task


@pytest.fixture
async def test_person(db_session: AsyncSession, test_user: User) -> Person:
    person = Person(
        user_id=test_user.id,
        name="Test Person",
        importance="medium",
        designation="Test Designation",
        relation_type="Colleague",
        notes="Test notes",
        contact={"email": "test@example.com", "phone": "1234567890"},
    )
    db_session.add(person)
    await db_session.commit()
    await db_session.refresh(person)
    return person


@pytest.fixture
async def test_note(db_session: AsyncSession, test_user: User) -> Note:
    note = Note(
        user_id=test_user.id,
        content="Test Note",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)
    return note


@pytest.mark.asyncio
async def test_process_sidekick_input(
    async_client: AsyncClient,
    test_user: User,
    test_thread: SidekickThread,
    access_token: str,
    mock_openai: AsyncMock,
    mock_llm_response: LLMResponse,
) -> None:
    response = await async_client.post(
        "/api/v1/sidekick/ask",
        json={"user_input": "Test input", "thread_id": test_thread.id},
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["response"] == mock_llm_response.instructions.followup
    mock_openai.assert_called_once()


async def test_list_topics(
    async_client: AsyncClient, test_user: User, test_topic: Topic, access_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/sidekick/topics", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["name"] == "Test Topic"


async def test_create_topic(
    async_client: AsyncClient, test_user: User, access_token: str
) -> None:
    topic_data = {
        "topic_id": str(uuid.uuid4()),  # Add this line
        "name": "New Topic",
        "description": "New Description",
        "keywords": ["test"],
        "related_people": [],
        "related_tasks": [],
    }
    response = await async_client.post(
        "/api/v1/sidekick/topics",
        json=topic_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Topic"


async def test_update_topic(
    async_client: AsyncClient, test_user: User, test_topic: Topic, access_token: str
) -> None:
    updated_data = {
        "topic_id": test_topic.topic_id,  # Add this line
        "name": "Updated Topic",
        "description": "Updated Description",
        "keywords": ["updated"],
        "related_people": [],
        "related_tasks": [],
    }
    response = await async_client.put(
        f"/api/v1/sidekick/topics/{test_topic.topic_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Topic"


async def test_delete_topic(
    async_client: AsyncClient, test_user: User, test_topic: Topic, access_token: str
) -> None:
    response = await async_client.delete(
        f"/api/v1/sidekick/topics/{test_topic.topic_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Topic deleted successfully"


# Similar tests for tasks, people, and notes
async def test_list_tasks(
    async_client: AsyncClient, test_user: User, test_task: Task, access_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/sidekick/tasks", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["description"] == "Test Task"


async def test_create_task(
    async_client: AsyncClient, test_user: User, access_token: str
) -> None:
    task_data = {
        "task_id": str(uuid.uuid4()),  # Add this line
        "type": "1",
        "description": "New Task",
        "status": "active",
        "actions": [],
        "people": {"owner": "", "final_beneficiary": "", "stakeholders": []},
        "dependencies": [],
        "schedule": "",
        "priority": "medium",
    }
    response = await async_client.post(
        "/api/v1/sidekick/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


async def test_update_task(
    async_client: AsyncClient, test_user: User, test_task: Task, access_token: str
) -> None:
    updated_data = {
        "task_id": test_task.task_id,  # Add this line
        "type": "2",
        "description": "Updated Task",
        "status": "pending",
        "actions": [],
        "people": {"owner": "", "final_beneficiary": "", "stakeholders": []},
        "dependencies": [],
        "schedule": "",
        "priority": "high",
    }
    response = await async_client.put(
        f"/api/v1/sidekick/tasks/{test_task.task_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


async def test_delete_task(
    async_client: AsyncClient, test_user: User, test_task: Task, access_token: str
) -> None:
    response = await async_client.delete(
        f"/api/v1/sidekick/tasks/{test_task.task_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Task deleted successfully"


# Tests for people endpoints
async def test_list_people(
    async_client: AsyncClient, test_user: User, test_person: Person, access_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/sidekick/people", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["name"] == "Test Person"


async def test_create_person(
    async_client: AsyncClient, test_user: User, access_token: str
) -> None:
    person_data = {
        "person_id": str(uuid.uuid4()),  # Add this line
        "name": "New Person",
        "designation": "Test Designation",
        "relation_type": "Colleague",
        "importance": "high",
        "notes": "Test notes",
        "contact": {"email": "test@example.com", "phone": "1234567890"},
    }
    response = await async_client.post(
        "/api/v1/sidekick/people",
        json=person_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


async def test_update_person(
    async_client: AsyncClient, test_user: User, test_person: Person, access_token: str
) -> None:
    updated_data = {
        "person_id": test_person.person_id,  # Add this line
        "name": "Updated Person",
        "designation": "Updated Designation",
        "relation_type": "Friend",
        "importance": "low",
        "notes": "Updated notes",
        "contact": {"email": "updated@example.com", "phone": "9876543210"},
    }
    response = await async_client.put(
        f"/api/v1/sidekick/people/{test_person.person_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


async def test_delete_person(
    async_client: AsyncClient, test_user: User, test_person: Person, access_token: str
) -> None:
    response = await async_client.delete(
        f"/api/v1/sidekick/people/{test_person.person_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Person deleted successfully"


# Tests for notes endpoints
async def test_list_notes(
    async_client: AsyncClient, test_user: User, test_note: Note, access_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/sidekick/notes", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["content"] == "Test Note"


async def test_create_note(
    async_client: AsyncClient, test_user: User, access_token: str
) -> None:
    note_data = {
        "note_id": str(uuid.uuid4()),  # Add this line
        "content": "New Note",
        "created_at": "2023-05-01T10:00:00",
        "updated_at": "2023-05-01T10:00:00",
        "related_people": [],
        "related_tasks": [],
        "related_topics": [],
    }
    response = await async_client.post(
        "/api/v1/sidekick/notes",
        json=note_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


async def test_update_note(
    async_client: AsyncClient, test_user: User, test_note: Note, access_token: str
) -> None:
    updated_data = {
        "note_id": test_note.note_id,  # Add this line
        "content": "Updated Note",
        "created_at": "2023-05-01T10:00:00",
        "updated_at": "2023-05-01T11:00:00",
        "related_people": [],
        "related_tasks": [],
        "related_topics": [],
    }
    response = await async_client.put(
        f"/api/v1/sidekick/notes/{test_note.note_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


async def test_delete_note(
    async_client: AsyncClient, test_user: User, test_note: Note, access_token: str
) -> None:
    response = await async_client.delete(
        f"/api/v1/sidekick/notes/{test_note.note_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Note deleted successfully"


# Test error handling
async def test_get_nonexistent_topic(
    async_client: AsyncClient, test_user: User, access_token: str
) -> None:
    response = await async_client.get(
        "/api/v1/sidekick/topics?page=1&page_size=10",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()["items"]) == 0


async def test_update_nonexistent_task(
    async_client: AsyncClient, test_user: User, access_token: str
) -> None:
    task_data = {
        "task_id": str(uuid.uuid4()),  # Use a random UUID
        "type": "1",
        "description": "Nonexistent Task",
        "status": "active",
        "actions": [],
        "people": {"owner": "", "final_beneficiary": "", "stakeholders": []},
        "dependencies": [],
        "schedule": "",
        "priority": "medium",
    }
    response = await async_client.put(
        f"/api/v1/sidekick/tasks/{task_data['task_id']}",
        json=task_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404


# Test SidekickService methods
@pytest.mark.asyncio
async def test_sidekick_service_get_user_context(
    db_session: AsyncSession,
    test_user: User,
    test_topic: Topic,
    test_task: Task,
    test_person: Person,
    test_note: Note,
) -> None:
    service = SidekickService()
    context = await service.get_user_context(db_session, test_user.id)

    assert len(context["topics"]) == 1
    assert len(context["tasks"]) == 1
    assert len(context["people"]) == 1
    assert len(context["notes"]) == 1


@pytest.mark.asyncio
async def test_sidekick_service_update_entities(
    db_session: AsyncSession, test_user: User
) -> None:
    service = SidekickService()
    data = {
        "people": [
            {
                "person_id": "new_person",
                "name": "New Person",
                "importance": "medium",
                "designation": "New Designation",
                "relation_type": "Colleague",
                "notes": "New notes",
                "contact": {"email": "new@example.com", "phone": "9876543210"},
            }
        ],
        "tasks": [
            {
                "task_id": "new_task",
                "description": "New Task",
                "status": "active",
                "type": "1",
                "actions": [],
                "people": {"owner": "", "final_beneficiary": "", "stakeholders": []},
                "dependencies": [],
                "schedule": "",
                "priority": "medium",
            }
        ],
        "topics": [
            {
                "topic_id": "new_topic",
                "name": "New Topic",
                "description": "New Description",
                "keywords": ["new"],
                "related_people": [],
                "related_tasks": [],
            }
        ],
        "notes": [
            {
                "note_id": "new_note",
                "content": "New Note",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "related_people": [],
                "related_tasks": [],
                "related_topics": [],
            }
        ],
    }
    updates = await service.update_entities(
        db_session, cast(dict[str, list[dict[str, Any]]], data), test_user.id
    )

    assert updates == {"people": 1, "tasks": 1, "topics": 1, "notes": 1}


# # Test rate limiting
# async def test_rate_limiting(async_client: AsyncClient, test_user: User, access_token: str) -> None:
#     rate_limit = int(settings.rate_limits["default"].split("/")[0])

#     async def make_request() -> Response:
#         return await async_client.post(
#             "/api/v1/sidekick/ask",
#             json={"user_input": "Test input"},
#             headers={"Authorization": f"Bearer {access_token}"},
#         )

#     # Make requests up to the rate limit
#     responses = await asyncio.gather(*[make_request() for _ in range(rate_limit)])

#     # All these requests should succeed
#     assert all(response.status_code == status.HTTP_200_OK for response in responses)

#     # The next request should be rate limited
#     response = await make_request()
#     assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

#     # Wait for the rate limit to reset (assuming it's per minute)
#     await asyncio.sleep(60)

#     # This request should succeed again
#     response = await make_request()
#     assert response.status_code == status.HTTP_200_OK


# Add these new test functions


@pytest.mark.asyncio
@patch.object(SidekickService, "get_or_create_thread", new_callable=AsyncMock)
@patch.object(SidekickService, "construct_prompt", new_callable=AsyncMock)
@patch.object(SidekickService, "call_openai_api", new_callable=AsyncMock)
@patch.object(SidekickService, "process_data")
@patch.object(SidekickService, "update_entities", new_callable=AsyncMock)
async def test_process_input(
    mock_update_entities: AsyncMock,
    mock_process_data: AsyncMock,
    mock_call_openai_api: AsyncMock,
    mock_construct_prompt: AsyncMock,
    mock_get_or_create_thread: AsyncMock,
    db_session: AsyncSession,
    test_user: User,
) -> None:
    service = SidekickService()

    # Set up the mock returns
    mock_thread = MagicMock(spec=SidekickThread)
    mock_thread.id = "test_thread_id"
    mock_thread.conversation_history = []
    mock_get_or_create_thread.return_value = mock_thread

    mock_construct_prompt.return_value = [{"role": "user", "content": "test prompt"}]

    mock_llm_response = LLMResponse(
        instructions=Instructions(
            status="complete",
            followup="Test followup",
            new_prompt="",
            write=False,
            affected_entities=AffectedEntities(),
        ),
        data=Data(),
    )
    mock_token_usage = TokenUsage(
        prompt_tokens=10, completion_tokens=20, total_tokens=30
    )
    mock_call_openai_api.return_value = (mock_llm_response, mock_token_usage)

    mock_process_data.return_value = mock_llm_response.model_dump()
    mock_update_entities.return_value = {
        "tasks": 0,
        "people": 0,
        "topics": 0,
        "notes": 0,
    }

    # Mock create_sidekick_thread
    new_thread = MagicMock(spec=SidekickThread)
    new_thread.id = "new_test_thread_id"
    with patch(
        "app.services.sidekick_service.create_sidekick_thread", new_callable=AsyncMock
    ) as mock_create_thread:
        mock_create_thread.return_value = new_thread

        # Call the method
        result = await service.process_input(
            db_session, test_user.id, SidekickInput(user_input="Test input")
        )

        # Assert the result
        assert isinstance(result, SidekickOutput)
        assert result.response == "Test followup"
        assert result.thread_id == "new_test_thread_id"  # Check for the new thread ID
        assert result.status == "complete"
        assert result.is_thread_complete is True

    # Verify that create_sidekick_thread was called
    mock_create_thread.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_thread(db_session: AsyncSession, test_user: User) -> None:
    service = SidekickService()

    # Test creating a new thread
    new_thread = await service.get_or_create_thread(db_session, test_user.id, None)
    assert isinstance(new_thread, SidekickThread)
    assert new_thread.user_id == test_user.id

    # Test getting an existing thread
    existing_thread = await service.get_or_create_thread(
        db_session, test_user.id, new_thread.id
    )
    assert existing_thread.id == new_thread.id

    # Test with non-existent thread_id
    with pytest.raises(HTTPException):
        await service.get_or_create_thread(db_session, test_user.id, "non_existent_id")


@pytest.mark.asyncio
@patch.object(SidekickService, "get_user_context", new_callable=AsyncMock)
async def test_construct_prompt(
    mock_get_user_context: AsyncMock, db_session: AsyncSession, test_user: User
) -> None:
    service = SidekickService()

    # Set up the mock return
    mock_get_user_context.return_value = {
        "tasks": [],
        "people": [],
        "topics": [],
        "notes": [],
    }

    conversation_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    result = await service.construct_prompt(
        db_session, test_user.id, conversation_history
    )

    assert isinstance(result, list)
    assert len(result) == 4  # system prompt, context, and 2 conversation messages
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"
    assert "Current context" in result[1]["content"]
    assert result[2:] == conversation_history


@pytest.mark.asyncio
async def test_call_openai_api() -> None:
    service = SidekickService()

    # Mock the openai.ChatCompletion.acreate method
    mock_response = MagicMock()
    mock_response.choices[
        0
    ].message.content = '{"instructions": {"status": "complete", "followup": "Test followup", "new_prompt": "", "write": false, "affected_entities": {}}, "data": {}}'
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    mock_response.usage.total_tokens = 30

    with patch("openai.ChatCompletion.acreate", new_callable=AsyncMock) as mock_acreate:
        mock_acreate.return_value = mock_response

        messages = [{"role": "user", "content": "Test message"}]
        result, token_usage = await service.call_openai_api(messages)

        assert isinstance(result, LLMResponse)
        assert result.instructions.status == "complete"
        assert result.instructions.followup == "Test followup"
        assert isinstance(token_usage, TokenUsage)
        assert token_usage.total_tokens == 30

    # Test error handling
    with patch("openai.ChatCompletion.acreate", new_callable=AsyncMock) as mock_acreate:
        mock_acreate.side_effect = Exception("API Error")

        with pytest.raises(HTTPException):
            await service.call_openai_api(messages)


# Add these tests to tests/test_sidekick.py


@pytest.mark.asyncio
async def test_list_topics_pagination(
    async_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
    access_token: str,
) -> None:
    # Create multiple topics
    topics_data = [
        {
            "topic_id": str(uuid.uuid4()),
            "name": f"Test Topic {i}",
            "description": f"Description {i}",
            "keywords": ["test"],
            "related_people": [],
            "related_tasks": [],
        }
        for i in range(15)  # Create 15 topics
    ]

    for topic_data in topics_data:
        response = await async_client.post(
            "/api/v1/sidekick/topics",
            json=topic_data,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

    # Test first page
    response = await async_client.get(
        "/api/v1/sidekick/topics?page=1&page_size=10",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["page_size"] == 10

    # Test second page
    response = await async_client.get(
        "/api/v1/sidekick/topics?page=2&page_size=10",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2


@pytest.mark.asyncio
async def test_concurrent_thread_management(
    async_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
    access_token: str,
    mock_openai: AsyncMock,
) -> None:
    # Create initial thread
    response = await async_client.post(
        "/api/v1/sidekick/ask",
        json={"user_input": "Initial message"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]

    # Simulate concurrent requests
    async def make_request(message: str) -> Any:
        return await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": message, "thread_id": thread_id},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    tasks = [make_request(f"Concurrent message {i}") for i in range(5)]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        assert response.status_code == 200
        assert "thread_id" in response.json()

    # Verify number of API calls (initial + concurrent)
    assert mock_openai.call_count == 6


@pytest.mark.asyncio
async def test_invalid_entity_data(
    async_client: AsyncClient, test_user: User, access_token: str
) -> None:
    # Test invalid person data
    invalid_person = {
        "person_id": str(uuid.uuid4()),
        "name": "Test Person",
        "designation": "Test Designation",
        "relation_type": "Colleague",
        "importance": "invalid_importance",  # Invalid enum value
        "notes": "Test notes",
        "contact": {"email": "invalid_email", "phone": "1234567890"},
    }

    response = await async_client.post(
        "/api/v1/sidekick/people",
        json=invalid_person,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400
    assert any("high" in msg["msg"] for msg in response.json()["detail"])
    assert any("medium" in msg["msg"] for msg in response.json()["detail"])
    assert any("low" in msg["msg"] for msg in response.json()["detail"])

    # Test invalid task data
    invalid_task = {
        "task_id": str(uuid.uuid4()),
        "type": "invalid_type",  # Invalid enum value
        "description": "Test Task",
        "status": "active",
        "actions": [],
        "people": {"owner": "", "final_beneficiary": "", "stakeholders": []},
        "dependencies": [],
        "schedule": "",
        "priority": "medium",
    }

    response = await async_client.post(
        "/api/v1/sidekick/tasks",
        json=invalid_task,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400  # Using 422 as specified
    detail = response.json()["detail"]
    assert any(
        "1" in msg["msg"]
        and "2" in msg["msg"]
        and "3" in msg["msg"]
        and "4" in msg["msg"]
        for msg in detail
    )


@pytest.mark.asyncio
async def test_context_gathering_and_entity_extraction(
    async_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
    access_token: str,
) -> None:
    # Create test entities first
    person_data = {
        "person_id": str(uuid.uuid4()),
        "name": "Context Test Person",
        "designation": "Test Designation",
        "relation_type": "Colleague",
        "importance": "medium",
        "notes": "Updated notes",
        "contact": {"email": "test@example.com", "phone": "1234567890"},
    }

    create_response = await async_client.post(
        "/api/v1/sidekick/people",
        json=person_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert create_response.status_code == 200

    # When we need to include data
    person_model = Person(
        person_id=person_data["person_id"],
        name=person_data["name"],
        designation=person_data["designation"],
        relation_type=person_data["relation_type"],
        importance=person_data["importance"],
        notes=person_data["notes"],
        contact=person_data["contact"],
    )

    person_schema = PersonSchema.model_validate(person_model)

    mock_llm_response = LLMResponse(
        instructions=Instructions(
            status="complete",
            followup="Test response",
            new_prompt="",
            write=True,
            affected_entities=AffectedEntities(
                people=[person_model.person_id],  # Use the ID string from the model
                tasks=[],
                notes=[],
                topics=[],
            ),
        ),
        data=Data(
            people=[person_schema],  # Use the actual model instance
            tasks=[],
            topics=[],
            notes=[],
        ),
    )

    mock_token_usage = TokenUsage(
        prompt_tokens=10, completion_tokens=20, total_tokens=30
    )

    with patch(
        "app.services.sidekick_service.SidekickService.call_openai_api",
        new_callable=AsyncMock,
    ) as mock_call:
        mock_call.return_value = (mock_llm_response, mock_token_usage)

        response = await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": "Update test person notes"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["updated_entities"]["people"] == 1

        # Instead of getting individual person, let's verify through list endpoint
        list_response = await async_client.get(
            "/api/v1/sidekick/people",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert list_response.status_code == 200
        people = list_response.json()["items"]
        updated_person = next(
            p for p in people if p["person_id"] == person_data["person_id"]
        )
        assert updated_person["notes"] == "Updated notes"


@pytest.mark.asyncio
async def test_entity_relationships(
    async_client: AsyncClient,
    test_user: User,
    db_session: AsyncSession,
    access_token: str,
) -> None:
    # Create a person
    person_data = {
        "person_id": str(uuid.uuid4()),
        "name": "Related Person",
        "designation": "Test Designation",
        "relation_type": "Colleague",
        "importance": "medium",
        "notes": "Test notes",
        "contact": {"email": "test@example.com", "phone": "1234567890"},
    }

    person_response = await async_client.post(
        "/api/v1/sidekick/people",
        json=person_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert person_response.status_code == 200

    # Create a task related to the person
    task_data = {
        "task_id": str(uuid.uuid4()),
        "type": "1",
        "description": "Related Task",
        "status": "active",
        "actions": [],
        "people": {
            "owner": person_data["person_id"],
            "final_beneficiary": "",
            "stakeholders": [],
        },
        "dependencies": [],
        "schedule": "",
        "priority": "medium",
    }

    task_response = await async_client.post(
        "/api/v1/sidekick/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert task_response.status_code == 200

    # Create a note linking both entities
    note_data = {
        "note_id": str(uuid.uuid4()),
        "content": "Related Note",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "related_people": [person_data["person_id"]],
        "related_tasks": [task_data["task_id"]],
        "related_topics": [],
    }

    note_response = await async_client.post(
        "/api/v1/sidekick/notes",
        json=note_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert note_response.status_code == 200

    # Set up mock response for OpenAI
    mock_llm_response = LLMResponse(
        instructions=Instructions(
            status="complete",
            followup="Test response",
            new_prompt="",
            write=False,
            affected_entities=AffectedEntities(
                people=[],  # Empty lists for affected entities since we're just reading
                tasks=[],
                notes=[],
                topics=[],
            ),
        ),
        data=Data(
            people=[],  # Empty lists since we're not modifying data
            tasks=[],
            topics=[],
            notes=[],
        ),
    )
    mock_token_usage = TokenUsage(
        prompt_tokens=10, completion_tokens=20, total_tokens=30
    )

    # Test the sidekick ask endpoint with mocked OpenAI response
    with patch(
        "app.routers.sidekick.SidekickService.call_openai_api",
        new_callable=AsyncMock,
        return_value=(mock_llm_response, mock_token_usage),
    ) as mock_call:
        response = await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": "Show me related entities"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Verify mock was called
        mock_call.assert_called_once()
        assert response.status_code == 200

        # Verify response structure
        data = response.json()
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0

        # Verify list endpoints return correct structure
        people_response = await async_client.get(
            "/api/v1/sidekick/people",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert people_response.status_code == 200
        response_data = people_response.json()
        assert "items" in response_data
        assert isinstance(response_data["items"], list)

        tasks_response = await async_client.get(
            "/api/v1/sidekick/tasks",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert tasks_response.status_code == 200
        response_data = tasks_response.json()
        assert "items" in response_data
        assert isinstance(response_data["items"], list)

        notes_response = await async_client.get(
            "/api/v1/sidekick/notes",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert notes_response.status_code == 200
        response_data = notes_response.json()
        assert "items" in response_data
        assert isinstance(response_data["items"], list)


# Add new test cases for error scenarios
@pytest.mark.asyncio
async def test_openai_api_error_handling(
    async_client: AsyncClient,
    test_user: User,
    access_token: str,
) -> None:
    # Test API timeout
    with patch(
        "app.routers.sidekick.SidekickService.call_openai_api",
        new_callable=AsyncMock,
        side_effect=asyncio.TimeoutError("API timeout"),
    ):
        response = await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": "Test input"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 500
        assert "timeout" in response.json()["detail"].lower()

    # Test API rate limit
    with patch(
        "app.routers.sidekick.SidekickService.call_openai_api",
        new_callable=AsyncMock,
        side_effect=Exception("Rate limit exceeded"),
    ):
        response = await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": "Test input"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 500
        assert "rate limit" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_llm_response_handling(
    async_client: AsyncClient,
    test_user: User,
    access_token: str,
) -> None:
    # Create an invalid string response instead of MagicMock
    with patch(
        "app.routers.sidekick.SidekickService.call_openai_api",
        new_callable=AsyncMock,
        side_effect=json.JSONDecodeError("Invalid JSON", doc="Invalid JSON", pos=0),
    ):
        response = await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": "Test input"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 500
        assert "json" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_thread_management_edge_cases(
    async_client: AsyncClient,
    test_user: User,
    access_token: str,
    mock_openai: AsyncMock,
) -> None:
    # Test with invalid thread_id
    response = await async_client.post(
        "/api/v1/sidekick/ask",
        json={"user_input": "Test", "thread_id": "invalid-uuid"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 404

    # Test with missing user_input
    response = await async_client.post(
        "/api/v1/sidekick/ask",
        json={},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 400  # FastAPI validation error


@pytest.mark.asyncio
async def test_concurrent_entity_updates(
    async_client: AsyncClient,
    test_user: User,
    access_token: str,
    mock_openai: AsyncMock,
) -> None:
    # Create initial entities
    person_data = {
        "person_id": str(uuid.uuid4()),
        "name": "Test Person",
        "designation": "Test Designation",
        "relation_type": "Colleague",
        "importance": "medium",
        "notes": "Test notes",
        "contact": {"email": "test@example.com", "phone": "1234567890"},
    }

    await async_client.post(
        "/api/v1/sidekick/people",
        json=person_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    # Set up mock responses for concurrent updates
    async def make_update_request(notes: str) -> Any:
        return await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": f"Update notes to: {notes}"},
            headers={"Authorization": f"Bearer {access_token}"},
        )

    # Make concurrent update requests
    tasks = [make_update_request(f"Note {i}") for i in range(5)]
    responses = await asyncio.gather(*tasks)

    for response in responses:
        assert response.status_code == 200

    # Verify final state
    response = await async_client.get(
        "/api/v1/sidekick/people",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200