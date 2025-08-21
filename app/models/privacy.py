from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from ..database import Base
import uuid

class PrivacyRequest(Base):
    __tablename__ = "privacy_requests"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255))
    request_type = Column(String(50))  # 'access', 'delete', 'export'
    anonymous_user_id = Column(String(64))
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)