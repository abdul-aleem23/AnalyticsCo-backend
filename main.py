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
    print(f"Starting server on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port)