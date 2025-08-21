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

# Try to import API routers - graceful fallback if they fail
routers_available = False
try:
    from app.api import public, auth, admin
    print("✅ API routers imported successfully")
    routers_available = True
except Exception as e:
    print(f"⚠️ API routers import failed: {e}")
    routers_available = False

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
allowed_origins = ["*"] if settings.environment == "development" else [
    settings.base_url,
    "http://localhost:3000",
    "http://localhost:5173", 
    "http://localhost:5174",
    "https://localhost:3000",
    "https://localhost:5173",
    "https://localhost:5174"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include API routers if available
if routers_available:
    try:
        app.include_router(public.router, tags=["Public"])
        print("✅ Public router included")
    except Exception as e:
        print(f"⚠️ Failed to include public router: {e}")
    
    try:
        app.include_router(auth.router, tags=["Authentication"])
        print("✅ Auth router included")
    except Exception as e:
        print(f"⚠️ Failed to include auth router: {e}")
    
    try:
        app.include_router(admin.router, tags=["Admin"])
        print("✅ Admin router included")
    except Exception as e:
        print(f"⚠️ Failed to include admin router: {e}")
else:
    print("⚠️ API routers not available - running with basic endpoints only")

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
        "database": "available" if database_available else "unavailable",
        "api_routers": "available" if routers_available else "unavailable"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    if settings.environment == "development":
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error",
                "detail": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Starting server on 0.0.0.0:{port}")
    print(f"🌐 PORT environment variable: {os.getenv('PORT', 'NOT SET')}")
    print(f"🔗 Expected external URL: {settings.base_url}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)