from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional
from uuid import UUID

class CampaignCreate(BaseModel):
    business_name: str
    target_url: HttpUrl
    description: Optional[str] = None

class CampaignUpdate(BaseModel):
    business_name: Optional[str] = None
    target_url: Optional[HttpUrl] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    client_access_enabled: Optional[bool] = None

class CampaignResponse(BaseModel):
    id: UUID
    campaign_id: str
    business_name: str
    target_url: str
    description: Optional[str]
    created_at: datetime
    active: bool
    client_access_enabled: bool
    archived: bool
    archived_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class CampaignStats(BaseModel):
    total_scans: int
    unique_visitors: int
    recent_scans: int
    top_cities: list[dict]
    device_breakdown: dict
    daily_scans: list[dict]