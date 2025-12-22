from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    membership_status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MemberSchema:
    """Pydantic schema for member API responses"""
    
    def __init__(self, id: int, name: str, email: str, phone: str = None, 
                 membership_status: str = "active"):
        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.membership_status = membership_status
