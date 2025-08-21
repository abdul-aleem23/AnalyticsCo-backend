from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# Try to import database components - graceful fallback if they fail
try:
    from app.config import settings
    print("✅ Settings imported successfully")
except Exception as e:
    print(f"⚠️ Settings import failed: {e}")
    # Create minimal settings fallback
    class Settings:
        environment = "production"
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
    settings = Settings()

app = FastAPI(
    title="QR Analytics Platform", 
    description="Self-hosted QR code analytics platform for marketing agencies",
    version="1.0.0"
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
        "environment": settings.environment
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)