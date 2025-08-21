from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import os

# Try to import database components - graceful fallback if they fail
try:
    from app.config import settings
    from app.database import create_tables, get_database
    from app.api.auth import create_initial_admin
    print("✅ Database components imported successfully")
    database_available = True
except Exception as e:
    print(f"⚠️ Database import failed: {e}")
    database_available = False
    # Create minimal settings fallback
    class Settings:
        environment = "production"
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
    settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting QR Analytics Platform...")
    
    if database_available:
        try:
            # Create database tables
            await create_tables()
            print("✅ Database tables created")
            
            # Create initial admin user if none exists
            async for db in get_database():
                await create_initial_admin(db)
                print("✅ Initial admin user checked/created")
                break
            
            print(f"✅ Application started with database on {settings.base_url}")
        except Exception as e:
            print(f"⚠️ Database initialization failed: {e}")
            print("App will continue without database functionality")
    else:
        print("⚠️ Starting without database functionality")
    
    yield
    
    # Shutdown
    print("Shutting down QR Analytics Platform...")

app = FastAPI(
    title="QR Analytics Platform", 
    description="Self-hosted QR code analytics platform for marketing agencies",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [settings.base_url],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "QR Analytics Platform API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.environment,
        "port": os.getenv("PORT", "8000")
    }

@app.get("/health")
async def health_check():
    import datetime
    return {
        "status": "healthy", 
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "environment": settings.environment,
        "database": "available" if database_available else "unavailable"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)