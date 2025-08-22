from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io
import pandas as pd
from datetime import datetime
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

@router.get("/api/campaigns/{campaign_id}/export")
async def export_campaign_data(
    campaign_id: str,
    db: AsyncSession = Depends(get_database)
):
    if not is_valid_campaign_id(campaign_id):
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Verify campaign exists and access is enabled
    campaign_service = CampaignService(db)
    campaign = await campaign_service.get_campaign_by_id(campaign_id)
    
    if not campaign or not campaign.client_access_enabled or campaign.archived:
        raise HTTPException(status_code=404, detail="Campaign not found or access disabled")
    
    # Get analytics data
    analytics_service = AnalyticsService(db)
    stats = await analytics_service.get_campaign_analytics(campaign_id)
    
    if not stats:
        raise HTTPException(status_code=404, detail="No analytics data found")
    
    # Create Excel file in memory
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Summary sheet
        summary_data = {
            'Metric': [
                'Campaign ID',
                'Business Name', 
                'Total Scans',
                'Unique Visitors',
                'Export Date'
            ],
            'Value': [
                campaign_id,
                campaign.business_name,
                stats.get('total_scans', 0),
                stats.get('unique_visitors', 0),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Daily data sheet
        if 'daily_data' in stats and stats['daily_data']:
            daily_df = pd.DataFrame(stats['daily_data'])
            daily_df.to_excel(writer, sheet_name='Daily Scans', index=False)
        
        # Hourly data sheet  
        if 'hourly_data' in stats and stats['hourly_data']:
            hourly_df = pd.DataFrame(stats['hourly_data'])
            hourly_df.to_excel(writer, sheet_name='Hourly Breakdown', index=False)
        
        # Geographic data sheet
        if 'geographic_data' in stats and stats['geographic_data']:
            geo_df = pd.DataFrame(stats['geographic_data'])
            geo_df.to_excel(writer, sheet_name='Geographic Distribution', index=False)
        
        # Device breakdown sheet
        if 'device_breakdown' in stats and stats['device_breakdown']:
            device_data = [{'Device': k, 'Scans': v} for k, v in stats['device_breakdown'].items()]
            device_df = pd.DataFrame(device_data)
            device_df.to_excel(writer, sheet_name='Device Types', index=False)
        
        # Recent scans sheet (if available)
        if 'recent_activity' in stats and stats['recent_activity']:
            recent_df = pd.DataFrame([
                {
                    'Timestamp': scan.get('timestamp', ''),
                    'City': scan.get('city', 'Unknown'),
                    'Country': scan.get('country', 'Unknown'), 
                    'Device': scan.get('device_type', 'Unknown')
                }
                for scan in stats['recent_activity']
            ])
            recent_df.to_excel(writer, sheet_name='Recent Scans', index=False)
    
    output.seek(0)
    
    # Return as downloadable file
    filename = f"campaign-{campaign_id}-analytics-{datetime.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )