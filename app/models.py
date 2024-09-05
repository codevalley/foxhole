from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    # Additional fields can be added here
    # For example:
    # created_at = Column(DateTime, default=datetime.utcnow)
    # is_active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"