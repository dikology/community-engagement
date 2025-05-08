from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.api.v1 import api_router

settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend service for the Community Engagement Bot that connects Telegram with Google Sheets",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Community Engagement Bot API is running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}
