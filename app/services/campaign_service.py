from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from ..models import Campaign, Scan
from ..schemas import CampaignCreate, CampaignUpdate
from ..utils import generate_campaign_id, sanitize_url

class CampaignService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_campaign(self, campaign_data: CampaignCreate) -> Campaign:
        # Generate unique campaign ID
        campaign_id = generate_campaign_id()
        
        # Ensure campaign ID is unique
        while await self.get_campaign_by_id(campaign_id):
            campaign_id = generate_campaign_id()

        campaign = Campaign(
            campaign_id=campaign_id,
            business_name=campaign_data.business_name,
            target_url=sanitize_url(str(campaign_data.target_url)),
            description=campaign_data.description,
            created_at=datetime.utcnow(),
            active=True,
            client_access_enabled=True,
            archived=False
        )

        self.db.add(campaign)
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def get_campaign_by_id(self, campaign_id: str) -> Optional[Campaign]:
        result = await self.db.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        )
        return result.scalar_one_or_none()

    async def get_all_campaigns(self, include_archived: bool = False) -> List[Campaign]:
        query = select(Campaign)
        if not include_archived:
            query = query.where(Campaign.archived == False)
        
        query = query.order_by(desc(Campaign.created_at))
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_campaign(self, campaign_id: str, campaign_data: CampaignUpdate) -> Optional[Campaign]:
        result = await self.db.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return None

        update_data = campaign_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "target_url" and value:
                value = sanitize_url(str(value))
            setattr(campaign, field, value)

        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def archive_campaign(self, campaign_id: str) -> Optional[Campaign]:
        result = await self.db.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return None

        campaign.archived = True
        campaign.archived_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def toggle_client_access(self, campaign_id: str, enabled: bool) -> Optional[Campaign]:
        result = await self.db.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        
        if not campaign:
            return None

        campaign.client_access_enabled = enabled
        
        await self.db.commit()
        await self.db.refresh(campaign)
        return campaign

    async def get_campaign_stats(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        campaign = await self.get_campaign_by_id(campaign_id)
        if not campaign:
            return None

        # Get scan statistics
        total_scans = await self.db.execute(
            select(func.count(Scan.id)).where(Scan.campaign_id == campaign_id)
        )
        total_scans = total_scans.scalar() or 0

        unique_visitors = await self.db.execute(
            select(func.count(func.distinct(Scan.anonymous_user_id))).where(Scan.campaign_id == campaign_id)
        )
        unique_visitors = unique_visitors.scalar() or 0

        # Get recent scans (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        recent_scans = await self.db.execute(
            select(func.count(Scan.id)).where(
                and_(
                    Scan.campaign_id == campaign_id,
                    Scan.timestamp >= seven_days_ago
                )
            )
        )
        recent_scans = recent_scans.scalar() or 0

        return {
            "campaign_id": campaign_id,
            "business_name": campaign.business_name,
            "total_scans": total_scans,
            "unique_visitors": unique_visitors,
            "recent_scans": recent_scans,
            "created_at": campaign.created_at,
            "active": campaign.active,
            "client_access_enabled": campaign.client_access_enabled,
            "archived": campaign.archived
        }

    async def get_admin_dashboard_stats(self) -> Dict[str, Any]:
        # Total campaigns
        total_campaigns = await self.db.execute(select(func.count(Campaign.id)))
        total_campaigns = total_campaigns.scalar() or 0

        # Active campaigns
        active_campaigns = await self.db.execute(
            select(func.count(Campaign.id)).where(
                and_(Campaign.active == True, Campaign.archived == False)
            )
        )
        active_campaigns = active_campaigns.scalar() or 0

        # Total scans across all campaigns
        total_scans = await self.db.execute(select(func.count(Scan.id)))
        total_scans = total_scans.scalar() or 0

        # Scans today
        today = datetime.utcnow().date()
        scans_today = await self.db.execute(
            select(func.count(Scan.id)).where(func.date(Scan.timestamp) == today)
        )
        scans_today = scans_today.scalar() or 0

        # Recent campaigns
        recent_campaigns_result = await self.db.execute(
            select(Campaign).where(Campaign.archived == False)
            .order_by(desc(Campaign.created_at))
            .limit(5)
        )
        recent_campaigns = recent_campaigns_result.scalars().all()

        return {
            "total_campaigns": total_campaigns,
            "active_campaigns": active_campaigns,
            "total_scans": total_scans,
            "scans_today": scans_today,
            "recent_campaigns": [
                {
                    "campaign_id": c.campaign_id,
                    "business_name": c.business_name,
                    "created_at": c.created_at
                }
                for c in recent_campaigns
            ]
        }