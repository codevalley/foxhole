from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
import secrets


class Base(DeclarativeBase):
    pass


class User(Base):
    """
    User model representing the users table in the database.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    screen_name: Mapped[str] = mapped_column(String, index=True, nullable=True)

    @classmethod
    def generate_user_id(cls) -> str:
        return secrets.token_urlsafe(16)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, screen_name={self.screen_name or 'anon_user'})>"
