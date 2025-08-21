from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base
import uuid

class Scan(Base):
    __tablename__ = "scans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    campaign_id = Column(String(14), ForeignKey("campaigns.campaign_id"), nullable=False, index=True)
    anonymous_user_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, server_default=func.now())
    ip_address = Column(String(45))  # IPv6 compatible
    city = Column(String(100))
    country = Column(String(100))
    device_type = Column(String(50))
    user_agent_hash = Column(String(64))
    created_at = Column(DateTime, server_default=func.now(), index=True)
    
    campaign = relationship("Campaign", back_populates="scans")