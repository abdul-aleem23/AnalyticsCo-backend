from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from ..database import get_database
from ..models import AdminUser
from ..schemas import CampaignCreate, CampaignResponse, CampaignUpdate
from ..services.campaign_service import CampaignService
from ..services.qr_service import QRService
from .auth import get_current_user

router = APIRouter()

@router.get("/admin/dashboard/stats")
async def get_admin_dashboard_stats(
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    campaign_service = CampaignService(db)
    stats = await campaign_service.get_admin_dashboard_stats()
    return stats

@router.get("/admin/campaigns", response_model=List[CampaignResponse])
async def get_all_campaigns(
    include_archived: bool = False,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    campaign_service = CampaignService(db)
    campaigns = await campaign_service.get_all_campaigns(include_archived=include_archived)
    return campaigns

@router.post("/admin/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    campaign_service = CampaignService(db)
    campaign = await campaign_service.create_campaign(campaign_data)
    return campaign

@router.get("/admin/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    campaign_service = CampaignService(db)
    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.put("/admin/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    campaign_service = CampaignService(db)
    campaign = await campaign_service.update_campaign(campaign_id, campaign_data)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.put("/admin/campaigns/{campaign_id}/archive")
async def archive_campaign(
    campaign_id: str,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    campaign_service = CampaignService(db)
    campaign = await campaign_service.archive_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {"message": "Campaign archived successfully", "campaign_id": campaign_id}

@router.put("/admin/campaigns/{campaign_id}/access")
async def toggle_client_access(
    campaign_id: str,
    request_data: dict,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    enabled = request_data.get("client_access_enabled", True)
    
    campaign_service = CampaignService(db)
    campaign = await campaign_service.toggle_client_access(campaign_id, enabled)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {
        "message": f"Client access {'enabled' if enabled else 'disabled'}",
        "campaign_id": campaign_id,
        "client_access_enabled": enabled
    }

@router.get("/admin/campaigns/{campaign_id}/stats")
async def get_campaign_admin_stats(
    campaign_id: str,
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    campaign_service = CampaignService(db)
    stats = await campaign_service.get_campaign_stats(campaign_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return stats

@router.get("/admin/campaigns/{campaign_id}/qr")
async def get_campaign_qr_code(
    campaign_id: str,
    size: int = 300,
    format: str = "PNG",
    current_user: AdminUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    # Verify campaign exists
    campaign_service = CampaignService(db)
    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Generate QR code
    qr_image = QRService.generate_qr_code(campaign_id, size=size, format=format)
    
    media_type = f"image/{format.lower()}"
    filename = f"{campaign_id}_qr.{format.lower()}"
    
    return StreamingResponse(
        qr_image,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )