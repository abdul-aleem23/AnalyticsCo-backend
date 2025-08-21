from sqlalchemy.orm import relationship
from .campaign import Campaign
from .scan import Scan
from .user import AdminUser
from .privacy import PrivacyRequest

# Add relationship to Campaign model
Campaign.scans = relationship("Scan", back_populates="campaign")

__all__ = ["Campaign", "Scan", "AdminUser", "PrivacyRequest"]