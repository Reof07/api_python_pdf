
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from ...db.database import Base



class User(Base):
    """ User model
    
    Args:
        Base (Base): Base clase de SQLAlchemy
        
    Returns:
        class  'models.User': User model
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    hashed_password = Column(String(255))
    refresh_token = Column(String(255), nullable=True) 
    refresh_token_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now())
    updated_at = Column(DateTime, default=datetime.now(), onupdate=datetime.now())