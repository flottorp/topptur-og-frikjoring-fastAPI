from sqlalchemy import Boolean, Column, Integer, String, DateTime, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Member(Base):
    __tablename__ = "members"

    telephone_number = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    tf_valid = Column(Boolean, nullable=False)
    tf_valid_until = Column(Date, nullable=True)
    ntnui_valid = Column(Boolean, nullable=False)
    ntnui_valid_until = Column(Date, nullable=True)
    last_synced = Column(DateTime, default=datetime.utcnow)
    


class MemberSchema:
    """Pydantic schema for member API responses"""
    
    def __init__(self, telephone_number: str, name: str, email: str, tf_valid: bool, tf_valid_until: str, ntnui_valid: bool, ntnui_valid_until: str, last_synced: datetime):
        self.telephone_number = telephone_number
        self.name = name
        self.email = email
        self.tf_valid = tf_valid
        self.tf_valid_until = tf_valid_until
        self.ntnui_valid = ntnui_valid
        self.ntnui_valid_until = ntnui_valid_until
        self.last_synced = last_synced
