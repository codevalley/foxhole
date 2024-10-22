import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, SidekickThread, Topic, Task, Person, Note
from app.services.sidekick_service import SidekickService
from unittest.mock import patch
from app.routers.auth import create_access_token
from datetime import datetime
from typing import Any, cast


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
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)
    return note


async def test_process_sidekick_input(
    async_client: AsyncClient,
    test_user: User,
    test_thread: SidekickThread,
    access_token: str,
) -> None:
    with patch.object(SidekickService, "process_input") as mock_process_input:
        mock_process_input.return_value = {
            "response": "Test response",
            "thread_id": test_thread.id,
            "status": "complete",
            "new_prompt": None,
            "is_thread_complete": True,
            "updated_entities": {"tasks": 0, "people": 0, "topics": 0, "notes": 0},
            "token_usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }

        response = await async_client.post(
            "/api/v1/sidekick/ask",
            json={"user_input": "Test input", "thread_id": test_thread.id},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        assert response.status_code == 200
        assert response.json()["response"] == "Test response"
        assert response.json()["thread_id"] == test_thread.id


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
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
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
