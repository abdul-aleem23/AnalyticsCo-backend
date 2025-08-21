from sqlalchemy import Column, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base
import uuid

class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String(14), unique=True, nullable=False, index=True)
    business_name = Column(String(255), nullable=False)
    target_url = Column(Text, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    active = Column(Boolean, default=True)
    client_access_enabled = Column(Boolean, default=True)
    archived = Column(Boolean, default=False)
    archived_at = Column(DateTime, nullable=True)