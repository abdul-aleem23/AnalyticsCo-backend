import re
import requests
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

def get_city_from_ip(ip_address: str) -> Optional[str]:
    try:
        # Using a free IP geolocation service (in production, consider using a paid service)
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("city")
    except Exception:
        pass
    return None

def get_country_from_ip(ip_address: str) -> Optional[str]:
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                return data.get("country")
    except Exception:
        pass
    return None

def is_valid_campaign_id(campaign_id: str) -> bool:
    return bool(re.match(r'^[A-Za-z0-9_-]{14}$', campaign_id))

def sanitize_url(url: str) -> str:
    if not url.startswith(('http://', 'https://')):
        return f'https://{url}'
    return url