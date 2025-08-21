import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/qr_analytics")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    base_url: str = os.getenv("BASE_URL", "http://localhost:8000")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@example.com")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin123")
    
    company_name: str = os.getenv("COMPANY_NAME", "Your Marketing Agency")
    privacy_email: str = os.getenv("PRIVACY_EMAIL", "privacy@example.com")
    
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    class Config:
        env_file = ".env"

settings = Settings()