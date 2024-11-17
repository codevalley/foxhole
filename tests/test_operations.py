from typing import List, Dict, Any
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.operations import (
    get_user_by_id,
    get_user_by_secret,
    create_user,
    update_user,
    create_person,
    get_person,
    update_person,
    delete_person,
    get_people_for_user,
    create_task,
    get_task,
    update_task,
    delete_task,
    get_tasks_for_user,
    create_topic,
    get_topic,
    update_topic,
    delete_topic,
    get_topics_for_user,
    create_note,
    get_note,
    update_note,
    delete_note,
    get_notes_for_user,
    create_sidekick_thread,
    get_sidekick_thread,
    update_sidekick_thread,
    delete_sidekick_thread,
    purge_database,
)
from app.models import User, Person, Task, Topic, Note, SidekickThread
from app.schemas.sidekick_schema import (
    PersonCreate,
    TaskCreate,
    TopicCreate,
    NoteCreate,
    SidekickThreadCreate,
    PersonContact,
    TaskPeople,
)
import uuid
from datetime import datetime

pytestmark = pytest.mark.asyncio


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(screen_name="testuser", user_secret=User.generate_user_secret())
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_person(db_session: AsyncSession, test_user: User) -> Person:
    contact = PersonContact(email="test@example.com", phone="1234567890")
    person_data = PersonCreate(
        person_id=str(uuid.uuid4()),
        name="Test Person",
        designation="Test Designation",
        relation_type="colleague",
        importance="medium",
        notes="Test notes",
        contact=contact,
    )
    person = await create_person(db_session, person_data, test_user.id)
    return person


@pytest.fixture
async def test_task(db_session: AsyncSession, test_user: User) -> Task:
    people = TaskPeople(
        owner=test_user.id, final_beneficiary=test_user.id, stakeholders=[test_user.id]
    )
    task_data = TaskCreate(
        task_id=str(uuid.uuid4()),
        type="1",
        description="Test Description",
        status="pending",
        actions=["action1", "action2"],
        people=people,
        dependencies=[],
        schedule="2024-03-01",
        priority="medium",
    )
    task = await create_task(db_session, task_data, test_user.id)
    return task


@pytest.fixture
async def test_topic(db_session: AsyncSession, test_user: User) -> Topic:
    topic_data = TopicCreate(
        topic_id=str(uuid.uuid4()),
        name="Test Topic",
        description="Test Description",
        keywords=["test", "topic"],
        related_people=[],
        related_tasks=[],
    )
    topic = await create_topic(db_session, topic_data, test_user.id)
    return topic


@pytest.fixture
async def test_note(db_session: AsyncSession, test_user: User) -> Note:
    current_time = datetime.now().isoformat()
    note_data = NoteCreate(
        note_id=str(uuid.uuid4()),
        content="Test Note Content",
        created_at=current_time,
        updated_at=current_time,
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    note = await create_note(db_session, note_data, test_user.id)
    return note


@pytest.fixture
async def test_sidekick_thread(
    db_session: AsyncSession, test_user: User
) -> SidekickThread:
    thread_data = SidekickThreadCreate(
        user_id=test_user.id,
        conversation_history=[{"role": "user", "content": "Test message"}],
    )
    thread = await create_sidekick_thread(db_session, thread_data)
    return thread


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


# Person Tests
async def test_create_person(db_session: AsyncSession, test_user: User) -> None:
    contact = PersonContact(email="new@example.com", phone="9876543210")
    person_data = PersonCreate(
        person_id=str(uuid.uuid4()),
        name="New Person",
        designation="New Designation",
        relation_type="friend",
        importance="high",
        notes="New notes",
        contact=contact,
    )
    person = await create_person(db_session, person_data, test_user.id)

    assert person is not None
    assert person.name == "New Person"
    assert person.designation == "New Designation"
    assert person.relation_type == "friend"
    assert person.importance == "high"
    assert person.notes == "New notes"
    contact_dict = person.contact
    assert contact_dict["email"] == "new@example.com"
    assert contact_dict["phone"] == "9876543210"


async def test_get_person(db_session: AsyncSession, test_person: Person) -> None:
    person = await get_person(db_session, test_person.person_id)
    assert person is not None
    assert person.name == test_person.name
    assert person.designation == test_person.designation
    assert person.relation_type == test_person.relation_type
    assert person.importance == test_person.importance
    assert person.notes == test_person.notes
    contact_dict = person.contact
    assert contact_dict["email"] == test_person.contact["email"]
    assert contact_dict["phone"] == test_person.contact["phone"]


async def test_get_person_not_found(db_session: AsyncSession) -> None:
    non_existent_id = str(uuid.uuid4())
    person = await get_person(db_session, non_existent_id)
    assert person is None


async def test_update_person(db_session: AsyncSession, test_person: Person) -> None:
    updated_data = PersonCreate(
        person_id=test_person.person_id,
        name="Updated Person",
        designation="Updated Designation",
        relation_type="colleague",
        importance="medium",
        notes="Updated notes",
        contact=PersonContact(email="updated@example.com", phone="5555555555"),
    )
    person = await update_person(db_session, test_person.person_id, updated_data)

    assert person is not None
    assert person.name == "Updated Person"
    assert person.designation == "Updated Designation"
    assert person.relation_type == "colleague"
    assert person.importance == "medium"
    assert person.notes == "Updated notes"
    contact_dict = person.contact
    assert contact_dict["email"] == "updated@example.com"
    assert contact_dict["phone"] == "5555555555"


async def test_delete_person(db_session: AsyncSession, test_person: Person) -> None:
    success = await delete_person(db_session, test_person.person_id)
    assert success is True

    # Verify person was deleted
    deleted_person = await get_person(db_session, test_person.person_id)
    assert deleted_person is None


async def test_get_people_for_user(db_session: AsyncSession, test_user: User) -> None:
    contact1 = PersonContact(email="person1@example.com", phone="1111111111")
    person_data1 = PersonCreate(
        person_id=str(uuid.uuid4()),
        name="Person 1",
        designation="Designation 1",
        relation_type="friend",
        importance="high",
        notes="Notes 1",
        contact=contact1,
    )
    contact2 = PersonContact(email="person2@example.com", phone="2222222222")
    person_data2 = PersonCreate(
        person_id=str(uuid.uuid4()),
        name="Person 2",
        designation="Designation 2",
        relation_type="colleague",
        importance="medium",
        notes="Notes 2",
        contact=contact2,
    )

    await create_person(db_session, person_data1, test_user.id)
    await create_person(db_session, person_data2, test_user.id)

    people = await get_people_for_user(db_session, test_user.id)
    assert len(people) >= 2  # Could be more if other tests created people
    assert any(p.name == "Person 1" for p in people)
    assert any(p.name == "Person 2" for p in people)


# Task Tests
async def test_create_task(db_session: AsyncSession, test_user: User) -> None:
    people = TaskPeople(
        owner=test_user.id, final_beneficiary=test_user.id, stakeholders=[test_user.id]
    )
    task_data = TaskCreate(
        task_id=str(uuid.uuid4()),
        type="2",
        description="New Description",
        status="active",
        actions=["new_action1", "new_action2"],
        people=people,
        dependencies=[],
        schedule="2024-03-02",
        priority="high",
    )
    task = await create_task(db_session, task_data, test_user.id)

    assert task is not None
    assert task.type == "2"
    assert task.description == "New Description"
    assert task.status == "active"
    assert task.priority == "high"
    assert task.actions == ["new_action1", "new_action2"]
    people_dict = task.people
    assert people_dict["owner"] == test_user.id


async def test_get_task(db_session: AsyncSession, test_task: Task) -> None:
    task = await get_task(db_session, test_task.task_id)
    assert task is not None
    assert task.type == test_task.type
    assert task.description == test_task.description
    assert task.status == test_task.status
    assert task.priority == test_task.priority
    assert task.actions == test_task.actions
    people_dict = task.people
    assert people_dict["owner"] == test_task.people["owner"]


async def test_get_task_not_found(db_session: AsyncSession) -> None:
    non_existent_id = str(uuid.uuid4())
    task = await get_task(db_session, non_existent_id)
    assert task is None


async def test_update_task(db_session: AsyncSession, test_task: Task) -> None:
    updated_data = TaskCreate(
        task_id=test_task.task_id,
        type="3",
        description="Updated Description",
        status="completed",
        actions=["updated_action1", "updated_action2"],
        people=TaskPeople(
            owner=test_task.people["owner"],
            final_beneficiary=test_task.people["final_beneficiary"],
            stakeholders=test_task.people["stakeholders"],
        ),
        dependencies=[],
        schedule="2024-03-03",
        priority="low",
    )
    task = await update_task(db_session, test_task.task_id, updated_data)

    assert task is not None
    assert task.type == "3"
    assert task.description == "Updated Description"
    assert task.status == "completed"
    assert task.priority == "low"


async def test_delete_task(db_session: AsyncSession, test_task: Task) -> None:
    success = await delete_task(db_session, test_task.task_id)
    assert success is True

    # Verify task was deleted
    deleted_task = await get_task(db_session, test_task.task_id)
    assert deleted_task is None


async def test_get_tasks_for_user(db_session: AsyncSession, test_user: User) -> None:
    # Create first task
    await create_task(
        db_session,
        TaskCreate(
            task_id=str(uuid.uuid4()),
            type="1",
            description="Task 1 Description",
            status="pending",
            actions=["task1_action1", "task1_action2"],
            people=TaskPeople(
                owner=test_user.id,
                final_beneficiary=test_user.id,
                stakeholders=[test_user.id],
            ),
            dependencies=[],
            schedule="2024-03-04",
            priority="medium",
        ),
        test_user.id,
    )

    # Create second task
    await create_task(
        db_session,
        TaskCreate(
            task_id=str(uuid.uuid4()),
            type="1",
            description="Task 2 Description",
            status="active",
            actions=["task2_action1", "task2_action2"],
            people=TaskPeople(
                owner=test_user.id,
                final_beneficiary=test_user.id,
                stakeholders=[test_user.id],
            ),
            dependencies=[],
            schedule="2024-03-05",
            priority="high",
        ),
        test_user.id,
    )

    # Get tasks
    tasks = await get_tasks_for_user(db_session, test_user.id)

    # Verify results
    assert len(tasks) == 2
    task1_found = False
    task2_found = False
    for task in tasks:
        if task.description == "Task 1 Description":
            task1_found = True
            assert task.status == "pending"
            assert task.priority == "medium"
        elif task.description == "Task 2 Description":
            task2_found = True
            assert task.status == "active"
            assert task.priority == "high"

    assert task1_found and task2_found


# Topic Tests
async def test_create_topic(db_session: AsyncSession, test_user: User) -> None:
    topic_data = TopicCreate(
        topic_id=str(uuid.uuid4()),
        name="New Topic",
        description="New Description",
        keywords=["new", "topic"],
        related_people=[],
        related_tasks=[],
    )
    topic = await create_topic(db_session, topic_data, test_user.id)

    assert topic is not None
    assert topic.name == "New Topic"
    assert topic.description == "New Description"
    assert topic.keywords == ["new", "topic"]


async def test_get_topic(db_session: AsyncSession, test_topic: Topic) -> None:
    topic = await get_topic(db_session, test_topic.topic_id)
    assert topic is not None
    assert topic.name == test_topic.name
    assert topic.description == test_topic.description
    assert topic.keywords == test_topic.keywords


async def test_get_topic_not_found(db_session: AsyncSession) -> None:
    non_existent_id = str(uuid.uuid4())
    topic = await get_topic(db_session, non_existent_id)
    assert topic is None


async def test_update_topic(db_session: AsyncSession, test_topic: Topic) -> None:
    updated_data = TopicCreate(
        topic_id=test_topic.topic_id,
        name="Updated Topic",
        description="Updated Description",
        keywords=["updated", "topic"],
        related_people=[],
        related_tasks=[],
    )
    topic = await update_topic(db_session, test_topic.topic_id, updated_data)

    assert topic is not None
    assert topic.name == "Updated Topic"
    assert topic.description == "Updated Description"
    assert topic.keywords == ["updated", "topic"]


async def test_delete_topic(db_session: AsyncSession, test_topic: Topic) -> None:
    success = await delete_topic(db_session, test_topic.topic_id)
    assert success is True

    # Verify topic was deleted
    deleted_topic = await get_topic(db_session, test_topic.topic_id)
    assert deleted_topic is None


async def test_get_topics_for_user(db_session: AsyncSession, test_user: User) -> None:
    topic_data1 = TopicCreate(
        topic_id=str(uuid.uuid4()),
        name="Topic 1",
        description="Topic 1 Description",
        keywords=["topic1", "keyword1"],
        related_people=[],
        related_tasks=[],
    )
    topic_data2 = TopicCreate(
        topic_id=str(uuid.uuid4()),
        name="Topic 2",
        description="Topic 2 Description",
        keywords=["topic2", "keyword2"],
        related_people=[],
        related_tasks=[],
    )

    await create_topic(db_session, topic_data1, test_user.id)
    await create_topic(db_session, topic_data2, test_user.id)

    topics = await get_topics_for_user(db_session, test_user.id)
    assert len(topics) >= 2  # Could be more if other tests created topics
    assert any(t.name == "Topic 1" for t in topics)
    assert any(t.name == "Topic 2" for t in topics)


# Note Tests
async def test_create_note(db_session: AsyncSession, test_user: User) -> None:
    from datetime import datetime

    current_time = datetime.now().isoformat()
    note_data = NoteCreate(
        note_id=str(uuid.uuid4()),
        content="New Note Content",
        created_at=current_time,
        updated_at=current_time,
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    note = await create_note(db_session, note_data, test_user.id)

    assert note is not None
    assert note.content == "New Note Content"
    assert note.created_at == current_time
    assert note.updated_at == current_time


async def test_get_note(db_session: AsyncSession, test_note: Note) -> None:
    note = await get_note(db_session, test_note.note_id)
    assert note is not None
    assert note.content == test_note.content
    assert note.created_at == test_note.created_at
    assert note.updated_at == test_note.updated_at


async def test_get_note_not_found(db_session: AsyncSession) -> None:
    non_existent_id = str(uuid.uuid4())
    note = await get_note(db_session, non_existent_id)
    assert note is None


async def test_update_note(db_session: AsyncSession, test_note: Note) -> None:
    current_time = datetime.now().isoformat()
    updated_data = NoteCreate(
        note_id=test_note.note_id,
        content="Updated Note Content",
        created_at=test_note.created_at,
        updated_at=current_time,
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    note = await update_note(db_session, test_note.note_id, updated_data)

    assert note is not None
    assert note.content == "Updated Note Content"
    assert note.created_at == test_note.created_at
    assert note.updated_at == current_time
    assert note.related_people == []
    assert note.related_tasks == []
    assert note.related_topics == []


async def test_delete_note(db_session: AsyncSession, test_note: Note) -> None:
    success = await delete_note(db_session, test_note.note_id)
    assert success is True

    # Verify note was deleted
    deleted_note = await get_note(db_session, test_note.note_id)
    assert deleted_note is None


async def test_get_notes_for_user(db_session: AsyncSession, test_user: User) -> None:
    note_data1 = NoteCreate(
        note_id=str(uuid.uuid4()),
        content="Note 1 Content",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    note_data2 = NoteCreate(
        note_id=str(uuid.uuid4()),
        content="Note 2 Content",
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )

    await create_note(db_session, note_data1, test_user.id)
    await create_note(db_session, note_data2, test_user.id)

    notes = await get_notes_for_user(db_session, test_user.id)
    assert len(notes) >= 2  # Could be more if other tests created notes
    assert any(n.content == "Note 1 Content" for n in notes)
    assert any(n.content == "Note 2 Content" for n in notes)


# SidekickThread Tests
async def test_create_sidekick_thread(
    db_session: AsyncSession, test_user: User
) -> None:
    thread_data = SidekickThreadCreate(
        user_id=test_user.id,
        conversation_history=[{"role": "user", "content": "Test message"}],
    )
    thread = await create_sidekick_thread(db_session, thread_data)

    assert thread is not None
    assert thread.user_id == test_user.id
    assert thread.conversation_history == [{"role": "user", "content": "Test message"}]


async def test_get_sidekick_thread(
    db_session: AsyncSession, test_sidekick_thread: SidekickThread
) -> None:
    thread = await get_sidekick_thread(db_session, test_sidekick_thread.id)
    assert thread is not None
    assert thread.user_id == test_sidekick_thread.user_id
    assert thread.conversation_history == test_sidekick_thread.conversation_history


async def test_get_sidekick_thread_not_found(db_session: AsyncSession) -> None:
    non_existent_id = str(uuid.uuid4())
    thread = await get_sidekick_thread(db_session, non_existent_id)
    assert thread is None


async def test_update_sidekick_thread(
    db_session: AsyncSession, test_sidekick_thread: SidekickThread
) -> None:
    new_history = [
        {"role": "user", "content": "Test message"},
        {"role": "assistant", "content": "Test response"},
    ]

    thread = await update_sidekick_thread(
        db_session, test_sidekick_thread.id, new_history
    )

    assert thread is not None
    assert thread.user_id == test_sidekick_thread.user_id
    assert thread.conversation_history == new_history


async def test_delete_sidekick_thread(
    db_session: AsyncSession, test_sidekick_thread: SidekickThread
) -> None:
    success = await delete_sidekick_thread(db_session, test_sidekick_thread.id)
    assert success is True

    # Verify thread was deleted
    deleted_thread = await get_sidekick_thread(db_session, test_sidekick_thread.id)
    assert deleted_thread is None


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
    async def mock_execute(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "execute", mock_execute)
    user = await get_user_by_secret(db_session, "some_secret")
    assert user is None


async def test_create_user_error(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)
    new_user = await create_user(db_session, "erroruser")
    assert new_user is None


async def test_update_user_error(
    db_session: AsyncSession, test_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)
    updated_user = await update_user(db_session, test_user, screen_name="erroruser")
    assert updated_user is None


# Error handling tests for Person operations
async def test_create_person_error(
    db_session: AsyncSession, test_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    person_data = PersonCreate(
        person_id=str(uuid.uuid4()),
        name="Test Person",
        designation="Test Designation",
        relation_type="colleague",
        importance="medium",
        notes="Test notes",
        contact=PersonContact(email="test@example.com", phone="1234567890"),
    )
    try:
        await create_person(db_session, person_data, test_user.id)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


async def test_create_task_error(
    db_session: AsyncSession, test_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    task_data = TaskCreate(
        task_id=str(uuid.uuid4()),
        type="1",
        description="Test Description",
        status="pending",
        actions=["action1", "action2"],
        people=TaskPeople(
            owner=test_user.id,
            final_beneficiary=test_user.id,
            stakeholders=[test_user.id],
        ),
        dependencies=[],
        schedule="2024-03-01",
        priority="medium",
    )
    try:
        await create_task(db_session, task_data, test_user.id)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


async def test_create_sidekick_thread_error(
    db_session: AsyncSession, test_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    thread_data = SidekickThreadCreate(
        user_id=test_user.id,
        conversation_history=[{"role": "user", "content": "Test message"}],
    )
    try:
        await create_sidekick_thread(db_session, thread_data)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


# Error handling tests for Task operations
async def test_update_task_error(
    db_session: AsyncSession, test_task: Task, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    updated_data = TaskCreate(
        task_id=test_task.task_id,
        type="3",
        description="Updated Description",
        status="completed",
        actions=["updated_action1", "updated_action2"],
        people=TaskPeople(
            owner=test_task.people["owner"],
            final_beneficiary=test_task.people["final_beneficiary"],
            stakeholders=test_task.people["stakeholders"],
        ),
        dependencies=[],
        schedule="2024-03-03",
        priority="low",
    )
    try:
        await update_task(db_session, test_task.task_id, updated_data)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


# Error handling tests for Topic operations
async def test_update_topic_error(
    db_session: AsyncSession, test_topic: Topic, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    updated_data = TopicCreate(
        topic_id=test_topic.topic_id,
        name="Updated Topic",
        description="Updated Description",
        keywords=["updated", "topic"],
        related_people=[],
        related_tasks=[],
    )
    try:
        await update_topic(db_session, test_topic.topic_id, updated_data)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


# Error handling tests for Note operations
async def test_update_note_error(
    db_session: AsyncSession, test_note: Note, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    updated_data = NoteCreate(
        note_id=test_note.note_id,
        content="Updated Content",
        created_at=test_note.created_at,
        updated_at=datetime.now().isoformat(),
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    try:
        await update_note(db_session, test_note.note_id, updated_data)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


# Error handling tests for SidekickThread operations
async def test_update_sidekick_thread_error(
    db_session: AsyncSession,
    test_sidekick_thread: SidekickThread,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def mock_commit(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "commit", mock_commit)

    new_history = [
        {"role": "user", "content": "Test message"},
        {"role": "assistant", "content": "Test response"},
    ]
    try:
        await update_sidekick_thread(db_session, test_sidekick_thread.id, new_history)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


# Database purge tests
async def test_purge_database(db_session: AsyncSession, test_user: User) -> None:
    # Create test data
    contact = PersonContact(email="test@example.com", phone="1234567890")
    person_data = PersonCreate(
        person_id=str(uuid.uuid4()),
        name="Test Person",
        designation="Test Designation",
        relation_type="colleague",
        importance="medium",
        notes="Test notes",
        contact=contact,
    )
    await create_person(db_session, person_data, test_user.id)

    task_data = TaskCreate(
        task_id=str(uuid.uuid4()),
        type="1",
        description="Test Description",
        status="pending",
        actions=["action1", "action2"],
        people=TaskPeople(
            owner=test_user.id,
            final_beneficiary=test_user.id,
            stakeholders=[test_user.id],
        ),
        dependencies=[],
        schedule="2024-03-01",
        priority="medium",
    )
    await create_task(db_session, task_data, test_user.id)

    topic_data = TopicCreate(
        topic_id=str(uuid.uuid4()),
        name="Test Topic",
        description="Test Description",
        keywords=["test", "topic"],
        related_people=[],
        related_tasks=[],
    )
    await create_topic(db_session, topic_data, test_user.id)

    current_time = datetime.now().isoformat()
    note_data = NoteCreate(
        note_id=str(uuid.uuid4()),
        content="Test Content",
        created_at=current_time,
        updated_at=current_time,
        related_people=[],
        related_tasks=[],
        related_topics=[],
    )
    await create_note(db_session, note_data, test_user.id)

    thread_data = SidekickThreadCreate(
        user_id=test_user.id,
        conversation_history=[{"role": "user", "content": "Test message"}],
    )
    await create_sidekick_thread(db_session, thread_data)

    # Verify data exists before purge
    people = await get_people_for_user(db_session, test_user.id)
    assert len(people) > 0
    tasks = await get_tasks_for_user(db_session, test_user.id)
    assert len(tasks) > 0
    topics = await get_topics_for_user(db_session, test_user.id)
    assert len(topics) > 0
    notes = await get_notes_for_user(db_session, test_user.id)
    assert len(notes) > 0

    # Purge database
    await purge_database(db_session)

    # Verify all data is deleted
    people_after = await get_people_for_user(db_session, test_user.id)
    assert len(people_after) == 0
    tasks_after = await get_tasks_for_user(db_session, test_user.id)
    assert len(tasks_after) == 0
    topics_after = await get_topics_for_user(db_session, test_user.id)
    assert len(topics_after) == 0
    notes_after = await get_notes_for_user(db_session, test_user.id)
    assert len(notes_after) == 0


async def test_purge_database_error(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def mock_execute(*args: Any, **kwargs: Any) -> None:
        raise Exception("Database error")

    monkeypatch.setattr(db_session, "execute", mock_execute)

    try:
        await purge_database(db_session)
        assert False, "Expected an exception"
    except Exception as e:
        assert str(e) == "Database error"


# Edge cases
async def test_update_sidekick_thread_with_empty_history(
    db_session: AsyncSession, test_sidekick_thread: SidekickThread
) -> None:
    new_conversation_history: List[Dict[str, str]] = []
    thread = await update_sidekick_thread(
        db_session, test_sidekick_thread.id, new_conversation_history
    )
    assert thread is not None
    assert len(thread.conversation_history) == 0


async def test_create_person_with_empty_fields(
    db_session: AsyncSession, test_user: User
) -> None:
    person_data = PersonCreate(
        person_id=str(uuid.uuid4()),
        name="",  # Empty name is allowed
        designation="",  # Empty designation is allowed
        relation_type="friend",  # Must be a non-empty string
        importance="medium",  # Must be one of "high", "medium", "low"
        notes="",  # Empty notes is allowed
        contact=PersonContact(email="", phone=""),  # Empty contact fields are allowed
    )
    person = await create_person(db_session, person_data, test_user.id)
    assert person is not None
    assert person.name == ""
    assert person.designation == ""
    assert person.relation_type == "friend"
    assert person.importance == "medium"
    assert person.notes == ""
    contact_dict = person.contact
    assert contact_dict["email"] == ""
    assert contact_dict["phone"] == ""


async def test_create_task_with_invalid_status(
    db_session: AsyncSession, test_user: User
) -> None:
    task_data = TaskCreate(
        task_id=str(uuid.uuid4()),
        type="1",  # Must be one of "1", "2", "3", "4"
        description="Test Description",
        status="pending",  # Must be one of "active", "pending", "completed"
        actions=["action1", "action2"],
        people=TaskPeople(
            owner=test_user.id,
            final_beneficiary=test_user.id,
            stakeholders=[test_user.id],
        ),
        dependencies=[],
        schedule="2024-03-01",
        priority="medium",  # Must be one of "high", "medium", "low"
    )
    task = await create_task(db_session, task_data, test_user.id)
    assert task is not None
    assert task.type == "1"
    assert task.description == "Test Description"
    assert task.status == "pending"
    assert task.actions == ["action1", "action2"]
    assert task.people["owner"] == test_user.id
    assert task.schedule == "2024-03-01"
    assert task.priority == "medium"


async def test_create_note_with_complex_metadata(
    db_session: AsyncSession, test_user: User
) -> None:
    current_time = datetime.now().isoformat()
    note_data = NoteCreate(
        note_id=str(uuid.uuid4()),
        content="Test Content",
        created_at=current_time,
        updated_at=current_time,
        related_people=[test_user.id],
        related_tasks=["task1", "task2"],
        related_topics=["topic1", "topic2"],
    )
    note = await create_note(db_session, note_data, test_user.id)
    assert note is not None
    assert note.content == "Test Content"
    assert note.created_at == current_time
    assert note.updated_at == current_time
    assert note.related_people == [test_user.id]
    assert note.related_tasks == ["task1", "task2"]
    assert note.related_topics == ["topic1", "topic2"]
