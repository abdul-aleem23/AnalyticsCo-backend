from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
from ..models import Campaign, Scan
from ..utils import generate_anonymous_user_id, parse_device_type, get_city_from_ip, get_country_from_ip

class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_scan(
        self,
        campaign_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[Scan]:
        # Check if campaign exists and is active
        result = await self.db.execute(
            select(Campaign).where(
                and_(Campaign.campaign_id == campaign_id, Campaign.active == True, Campaign.archived == False)
            )
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            return None

        # Generate anonymous user ID
        timestamp = datetime.utcnow()
        anonymous_user_id = generate_anonymous_user_id(ip_address or "unknown", user_agent or "unknown", timestamp)
        
        # Parse device type
        device_type = parse_device_type(user_agent or "")
        
        # Skip location data for now to avoid blocking HTTP requests
        # TODO: Implement proper async geolocation or use a background task
        city = None
        country = None
        
        # Create scan record
        scan = Scan(
            campaign_id=campaign_id,
            anonymous_user_id=anonymous_user_id,
            timestamp=timestamp,
            ip_address=ip_address,
            city=city,
            country=country,
            device_type=device_type,
            user_agent_hash=user_agent[:64] if user_agent else None
        )
        
        self.db.add(scan)
        await self.db.commit()
        await self.db.refresh(scan)
        
        return scan

    async def get_campaign_analytics(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        # Verify campaign exists and client access is enabled
        result = await self.db.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign or not campaign.client_access_enabled:
            return None

        # Get basic stats
        total_scans = await self._get_total_scans(campaign_id)
        unique_visitors = await self._get_unique_visitors(campaign_id)
        scans_today = await self._get_scans_today(campaign_id)
        scans_this_week = await self._get_scans_this_week(campaign_id)
        
        # Get recent activity (last 10 scans)
        recent_activity = await self._get_recent_activity(campaign_id, limit=10)
        
        # Get geographic breakdown
        geographic_data = await self._get_geographic_breakdown(campaign_id)
        
        # Get device breakdown
        device_breakdown = await self._get_device_breakdown(campaign_id)
        
        # Get daily data for charts (last 30 days)
        daily_data = await self._get_daily_scan_data(campaign_id, days=30)
        
        # Get hourly data for today
        hourly_data = await self._get_hourly_scan_data(campaign_id)

        return {
            "campaign_id": campaign_id,
            "business_name": campaign.business_name,
            "target_url": campaign.target_url,
            "created_at": campaign.created_at,
            "total_scans": total_scans,
            "unique_visitors": unique_visitors,
            "scans_today": scans_today,
            "scans_this_week": scans_this_week,
            "recent_activity": recent_activity,
            "geographic_data": geographic_data,
            "device_breakdown": device_breakdown,
            "daily_data": daily_data,
            "hourly_data": hourly_data
        }

    async def _get_total_scans(self, campaign_id: str) -> int:
        result = await self.db.execute(
            select(func.count(Scan.id)).where(Scan.campaign_id == campaign_id)
        )
        return result.scalar() or 0

    async def _get_unique_visitors(self, campaign_id: str) -> int:
        result = await self.db.execute(
            select(func.count(func.distinct(Scan.anonymous_user_id))).where(Scan.campaign_id == campaign_id)
        )
        return result.scalar() or 0

    async def _get_scans_today(self, campaign_id: str) -> int:
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        result = await self.db.execute(
            select(func.count(Scan.id)).where(
                and_(
                    Scan.campaign_id == campaign_id,
                    Scan.timestamp >= today_start,
                    Scan.timestamp < today_end
                )
            )
        )
        return result.scalar() or 0

    async def _get_scans_this_week(self, campaign_id: str) -> int:
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await self.db.execute(
            select(func.count(Scan.id)).where(
                and_(
                    Scan.campaign_id == campaign_id,
                    Scan.timestamp >= week_ago
                )
            )
        )
        return result.scalar() or 0

    async def _get_recent_activity(self, campaign_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(Scan).where(Scan.campaign_id == campaign_id)
            .order_by(desc(Scan.timestamp))
            .limit(limit)
        )
        scans = result.scalars().all()
        
        return [
            {
                "timestamp": scan.timestamp,
                "city": scan.city,
                "country": scan.country,
                "device_type": scan.device_type
            }
            for scan in scans
        ]

    async def _get_geographic_breakdown(self, campaign_id: str) -> List[Dict[str, Any]]:
        result = await self.db.execute(
            select(Scan.city, func.count(Scan.id).label('count'))
            .where(and_(Scan.campaign_id == campaign_id, Scan.city.isnot(None)))
            .group_by(Scan.city)
            .order_by(desc('count'))
            .limit(10)
        )
        
        return [
            {"city": row.city, "count": row.count}
            for row in result.all()
        ]

    async def _get_device_breakdown(self, campaign_id: str) -> Dict[str, int]:
        result = await self.db.execute(
            select(Scan.device_type, func.count(Scan.id).label('count'))
            .where(Scan.campaign_id == campaign_id)
            .group_by(Scan.device_type)
        )
        
        return {row.device_type or "unknown": row.count for row in result.all()}

    async def _get_daily_scan_data(self, campaign_id: str, days: int = 30) -> List[Dict[str, Any]]:
        try:
            start_datetime = datetime.utcnow() - timedelta(days=days)
            
            # Get all scans within the date range
            result = await self.db.execute(
                select(Scan.timestamp)
                .where(
                    and_(
                        Scan.campaign_id == campaign_id,
                        Scan.timestamp >= start_datetime
                    )
                )
                .order_by(Scan.timestamp)
            )
            
            scans = result.scalars().all()
            
            # Group by date in Python to avoid database-specific date functions
            daily_counts = {}
            for scan in scans:
                date_key = scan.date().isoformat()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1
            
            # Convert to sorted list
            return [
                {"date": date, "count": count}
                for date, count in sorted(daily_counts.items())
            ]
            
        except Exception as e:
            # Return empty data if there's an error
            print(f"Error getting daily scan data: {e}")
            return []

    async def _get_hourly_scan_data(self, campaign_id: str) -> List[Dict[str, Any]]:
        try:
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            # Get all scans from today
            result = await self.db.execute(
                select(Scan.timestamp)
                .where(
                    and_(
                        Scan.campaign_id == campaign_id,
                        Scan.timestamp >= today_start,
                        Scan.timestamp < today_end
                    )
                )
                .order_by(Scan.timestamp)
            )
            
            scans = result.scalars().all()
            
            # Group by hour in Python
            hourly_counts = {}
            for scan in scans:
                hour = scan.hour
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
            
            # Convert to sorted list
            return [
                {"hour": hour, "count": count}
                for hour, count in sorted(hourly_counts.items())
            ]
            
        except Exception as e:
            # Return empty data if there's an error
            print(f"Error getting hourly scan data: {e}")
            return []