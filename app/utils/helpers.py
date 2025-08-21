import re
import asyncio
import aiohttp
from typing import Optional
from user_agents import parse

def parse_device_type(user_agent: str) -> str:
    if not user_agent:
        return "unknown"
    
    user_agent_obj = parse(user_agent)
    
    if user_agent_obj.is_mobile:
        return "mobile"
    elif user_agent_obj.is_tablet:
        return "tablet"
    elif user_agent_obj.is_pc:
        return "desktop"
    else:
        return "unknown"

async def get_city_from_ip(ip_address: str) -> Optional[str]:
    if not ip_address or ip_address == "unknown":
        return None
        
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.get(f"http://ip-api.com/json/{ip_address}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data.get("city")
    except Exception:
        # Don't let geolocation errors break the scan recording
        pass
    return None

async def get_country_from_ip(ip_address: str) -> Optional[str]:
    if not ip_address or ip_address == "unknown":
        return None
        
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=2)) as session:
            async with session.get(f"http://ip-api.com/json/{ip_address}") as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "success":
                        return data.get("country")
    except Exception:
        # Don't let geolocation errors break the scan recording
        pass
    return None

# Synchronous fallback functions for backward compatibility
def get_city_from_ip_sync(ip_address: str) -> Optional[str]:
    """Synchronous version that doesn't make HTTP requests to avoid blocking"""
    return None

def get_country_from_ip_sync(ip_address: str) -> Optional[str]:
    """Synchronous version that doesn't make HTTP requests to avoid blocking"""
    return None

def is_valid_campaign_id(campaign_id: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9_-]{14}$', campaign_id))

def sanitize_url(url: str) -> str:
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url