from sqlalchemy import Column, String
from utils.database import Base

class User(Base):
    __tablename__ = "users"

    # Use the userID as the primary key
    user_id = Column(String, primary_key=True, index=True)
    
    # Additional fields can be added here in the future
    # For example:
    # email = Column(String, unique=True, index=True)
    # created_at = Column(DateTime, default=datetime.utcnow)