from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_database
from ..services.analytics_service import AnalyticsService
from ..services.campaign_service import CampaignService
from ..utils import is_valid_campaign_id

router = APIRouter()

@router.get("/scan/{campaign_id}")
async def track_scan_and_redirect(
    campaign_id: str,
    request: Request,
    db: AsyncSession = Depends(get_database)
):
    # Validate campaign ID format
    if not is_valid_campaign_id(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Get client IP and user agent
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    # Get campaign to check if it exists and get target URL
    campaign_service = CampaignService(db)
    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    
    if not campaign or not campaign.active or campaign.archived:
        raise HTTPException(status_code=404, detail="Campaign not found or inactive")
    
    # Record the scan asynchronously (don't block the redirect)
    analytics_service = AnalyticsService(db)
    try:
        await analytics_service.record_scan(
            campaign_id=campaign_id,
            ip_address=client_ip,
            user_agent=user_agent
        )
    except Exception as e:
        # Log error but don't block redirect
        print(f"Error recording scan: {e}")
    
    # Redirect to target URL
    return RedirectResponse(url=campaign.target_url, status_code=302)

@router.get("/api/campaigns/{campaign_id}/validate")
async def validate_campaign(
    campaign_id: str,
    db: AsyncSession = Depends(get_database)
):
    if not is_valid_campaign_id(campaign_id):
        return JSONResponse({"exists": False, "access_enabled": False})
    
    campaign_service = CampaignService(db)
    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    
    if not campaign:
        return JSONResponse({"exists": False, "access_enabled": False})
    
    return JSONResponse({
        "exists": True,
        "access_enabled": campaign.client_access_enabled and not campaign.archived,
        "business_name": campaign.business_name if campaign.client_access_enabled else None
    })

@router.get("/api/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    db: AsyncSession = Depends(get_database)
):
    if not is_valid_campaign_id(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    analytics_service = AnalyticsService(db)
    stats = await analytics_service.get_campaign_analytics(campaign_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="Campaign not found or access disabled")
    
    return stats