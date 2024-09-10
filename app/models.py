from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base
import uuid
from typing import Any

Base: Any = declarative_base()


class User(Base):
    """
    User model representing the users table in the database.
    """

    __tablename__ = "users"

    id: str = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True
    )
    screen_name: str = Column(String, index=True)
    user_secret: str = Column(String, unique=True, index=True)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, screen_name={self.screen_name or 'anon_user'})>"

    @staticmethod
    def generate_user_secret() -> str:
        return str(uuid.uuid4())
