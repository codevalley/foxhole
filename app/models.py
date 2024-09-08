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

    id = Column(String, primary_key=True, index=True)
    screen_name = Column(String, index=True)

    @staticmethod
    def generate_user_id() -> str:
        return str(uuid.uuid4())

    def __repr__(self) -> str:
        return f"<User(id={self.id}, screen_name={self.screen_name or 'anon_user'})>"
