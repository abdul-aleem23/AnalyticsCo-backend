from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class ScanCreate(BaseModel):
    campaign_id: str
    ip_address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    device_type: Optional[str] = None
    user_agent: Optional[str] = None

class ScanResponse(BaseModel):
    id: str
    campaign_id: str
    anonymous_user_id: str
    timestamp: datetime
    city: Optional[str]
    country: Optional[str]
    device_type: Optional[str]
    
    class Config:
        from_attributes = True

class AnalyticsData(BaseModel):
    campaign_id: str
    total_scans: int
    unique_visitors: int
    scans_today: int
    scans_this_week: int
    recent_activity: List[ScanResponse]
    geographic_data: List[Dict[str, Any]]
    device_breakdown: Dict[str, int]
    hourly_data: List[Dict[str, Any]]
    daily_data: List[Dict[str, Any]]

class ExportRequest(BaseModel):
    campaign_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_raw_data: bool = True