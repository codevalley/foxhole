from sqlalchemy.orm import declarative_base, Mapped
from sqlalchemy import Column, String
import secrets

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = Column(String, primary_key=True, index=True)
    screen_name: Mapped[str] = Column(String, index=True, nullable=True)

    @classmethod
    def generate_user_id(cls) -> str:
        return secrets.token_urlsafe(16)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, screen_name={self.screen_name or 'anon_user'})>"
