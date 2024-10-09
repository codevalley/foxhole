from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from typing import List, Dict, Any
import uuid

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
    sidekick_contexts: Mapped[List["SidekickContext"]] = relationship(
        "SidekickContext", back_populates="user"
    )

    def __init__(
        self, screen_name: str, user_secret: str, id: str | None = None
    ) -> None:
        self.id = id or str(uuid.uuid4())
        self.screen_name = screen_name
        self.user_secret = user_secret

    def __repr__(self) -> str:
        return f"<User(id={self.id}, screen_name={self.screen_name or 'anon_user'})>"

    @staticmethod
    def generate_user_secret() -> str:
        return str(uuid.uuid4())


# Update SidekickThread and SidekickContext models similarly
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


class SidekickContext(Base):
    __tablename__ = "sidekick_contexts"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    context_type: Mapped[str] = mapped_column(String)
    data: Mapped[List[Dict[str, Any]]] = mapped_column(JSON)

    user: Mapped["User"] = relationship("User", back_populates="sidekick_contexts")

    def __init__(
        self, id: str, user_id: str, context_type: str, data: List[Dict[str, Any]]
    ) -> None:
        self.id = id
        self.user_id = user_id
        self.context_type = context_type
        self.data = data
