from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    tf_fee = Column(Integer, nullable=False)
    ntnui_tf_member = Column(Boolean, nullable=False)
    last_synced = Column(DateTime, default=datetime.utcnow)
    


class MemberSchema:
    """Pydantic schema for member API responses"""
    
    def __init__(self, id: int, name: str, email: str, tf_fee: int, ntnui_tf_member: bool, last_synced: datetime):
        self.id = id
        self.name = name
        self.email = email
        self.tf_fee = tf_fee
        self.ntnui_tf_member = ntnui_tf_member
        self.last_synced = last_synced
