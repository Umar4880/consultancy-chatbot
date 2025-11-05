from dotenv import load_dotenv
from pathlib import Path

# Load .env file with absolute path
env_path = Path(r"C:\Users\ranau\OneDrive\Desktop\genaipractice\fewshort_consultancy_cahtboat\.env")
print(f"MAIN DEBUG: Loading .env from: {env_path}")
print(f"MAIN DEBUG: .env exists: {env_path.exists()}")
load_dotenv(dotenv_path=env_path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

from src.api.routes import router
# Initialize FastAPI app
app = FastAPI(
    title="Consultancy Chatbot API",
    description="Professional chatbot with consultant and documentation writer modes",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Mount static files (UI)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )