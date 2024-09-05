from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
import secrets

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    screen_name = Column(String, index=True, nullable=True)

    @classmethod
    def generate_user_id(cls):
        return secrets.token_urlsafe(16)

    def __repr__(self):
        return f"<User(id={self.id}, screen_name={self.screen_name or 'anon_user'})>"