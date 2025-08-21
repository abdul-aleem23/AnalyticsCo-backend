import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from ..config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def generate_campaign_id() -> str:
    return secrets.token_urlsafe(10)[:14]

def generate_anonymous_user_id(ip_address: str, user_agent: str, timestamp: datetime) -> str:
    data = f"{ip_address}:{user_agent}:{timestamp.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def verify_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None

def hash_user_agent(user_agent: str) -> str:
    return hashlib.sha256(user_agent.encode()).hexdigest()[:64]