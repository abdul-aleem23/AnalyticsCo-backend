# DEPLOYMENT BACKUP - Removed Code for Railway Testing

This file contains the original code that was temporarily removed to troubleshoot Railway deployment issues.

## Original main.py (app/main.py)

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from .database import create_tables, get_database
from .api import public, auth, admin
from .api.auth import create_initial_admin
from .config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting QR Analytics Platform...")
    
    try:
        # Create database tables
        await create_tables()
        print("Database tables created")
        
        # Create initial admin user if none exists
        async for db in get_database():
            await create_initial_admin(db)
            break
        
        print(f"Application started on {settings.base_url}")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
        print("App will start without database functionality")
    
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

# Include routers
app.include_router(public.router, tags=["Public"])
app.include_router(auth.router, tags=["Authentication"])
app.include_router(admin.router, tags=["Admin"])

@app.get("/")
async def root():
    return {
        "message": "QR Analytics Platform API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    import datetime
    return {"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}

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
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
```

## Current Minimal Version (backend/main.py)

```python
from fastapi import FastAPI
import os

app = FastAPI(title="QR Analytics Platform")

@app.get("/")
async def root():
    return {"message": "Hello Railway!", "port": os.getenv("PORT", "8000")}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
```

## Components to Restore After Deployment Works

1. **Database Integration**:
   - Import database modules
   - Add lifespan function for database initialization
   - Include database dependency injection

2. **API Routers**:
   - `public.router` - Public endpoints
   - `auth.router` - Authentication endpoints  
   - `admin.router` - Admin endpoints

3. **Middleware**:
   - CORS configuration
   - Global exception handler

4. **Configuration**:
   - Settings import and usage
   - Environment-specific configurations

5. **Error Handling**:
   - Comprehensive exception handling
   - Development vs production error responses

## Environment Variables Needed

```
SECRET_KEY=<32-char-hex-string>
BASE_URL=https://analyticsco-backend-production.up.railway.app
ENVIRONMENT=production
ADMIN_EMAIL=admin@yourcompany.com
ADMIN_PASSWORD=<secure-password>
COMPANY_NAME=Your Company Name
PRIVACY_EMAIL=privacy@yourcompany.com
DATABASE_URL=sqlite+aiosqlite:///./app.db
```

## Next Steps After Minimal Deployment Works

1. Add back database functionality gradually
2. Re-enable API routers one by one
3. Add back middleware and error handling
4. Test each component before adding the next
5. Finally add PostgreSQL database service in Railway