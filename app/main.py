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
    
    # Create database tables
    await create_tables()
    print("Database tables created")
    
    # Create initial admin user if none exists
    async for db in get_database():
        await create_initial_admin(db)
        break
    
    print(f"Application started on {settings.base_url}")
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
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

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