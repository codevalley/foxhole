import uuid
from sqlalchemy import String, ForeignKey, JSON, Enum
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from typing import List, Dict, Any, Optional

Base: Any = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    screen_name: Mapped[str] = mapped_column(String, index=True)
    user_secret: Mapped[str] = mapped_column(String, unique=True, index=True)

    sidekick_threads: Mapped[List["SidekickThread"]] = relationship(
        "SidekickThread", back_populates="user"
    )
    people: Mapped[List["Person"]] = relationship("Person", back_populates="user")
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="user")
    topics: Mapped[List["Topic"]] = relationship("Topic", back_populates="user")
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="user")

    def __init__(
        self, screen_name: str, user_secret: str, id: Optional[str] = None
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.screen_name = screen_name
        self.user_secret = user_secret

    def __repr__(self) -> str:
        return f"<User(id={self.id}, screen_name={self.screen_name or 'anon_user'})>"

    @staticmethod
    def generate_user_secret() -> str:
        return str(uuid.uuid4())


class Task(Base):
    __tablename__ = "tasks"

    task_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(Enum("1", "2", "3", "4", name="task_type_enum"))
    description: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(
        Enum("active", "pending", "completed", name="task_status_enum")
    )
    actions: Mapped[List[str]] = mapped_column(JSON)
    people: Mapped[Dict[str, Any]] = mapped_column(JSON)
    dependencies: Mapped[List[str]] = mapped_column(JSON)
    schedule: Mapped[str] = mapped_column(String)
    priority: Mapped[str] = mapped_column(
        Enum("high", "medium", "low", name="priority_enum")
    )

    user: Mapped["User"] = relationship("User", back_populates="tasks")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class Person(Base):
    __tablename__ = "people"

    person_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    designation: Mapped[str] = mapped_column(String)
    relation_type: Mapped[str] = mapped_column(String)
    importance: Mapped[str] = mapped_column(
        Enum("high", "medium", "low", name="importance_enum"), default="medium"
    )
    notes: Mapped[str] = mapped_column(String)
    contact: Mapped[Dict[str, str]] = mapped_column(JSON)

    user: Mapped["User"] = relationship("User", back_populates="people")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class Topic(Base):
    __tablename__ = "topics"

    topic_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String)
    keywords: Mapped[List[str]] = mapped_column(JSON)
    related_people: Mapped[List[str]] = mapped_column(JSON)
    related_tasks: Mapped[List[str]] = mapped_column(JSON)

    user: Mapped["User"] = relationship("User", back_populates="topics")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class Note(Base):
    __tablename__ = "notes"

    note_id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[str] = mapped_column(String)
    updated_at: Mapped[str] = mapped_column(String)
    related_people: Mapped[List[str]] = mapped_column(JSON)
    related_tasks: Mapped[List[str]] = mapped_column(JSON)
    related_topics: Mapped[List[str]] = mapped_column(JSON)

    user: Mapped["User"] = relationship("User", back_populates="notes")

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


class SidekickThread(Base):
    __tablename__ = "sidekick_threads"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    conversation_history: Mapped[List[Dict[str, str]]] = mapped_column(JSON)

    user: Mapped["User"] = relationship("User", back_populates="sidekick_threads")

    def __init__(
        self, id: str, user_id: str, conversation_history: List[Dict[str, str]]
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.conversation_history = conversation_history
