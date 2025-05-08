from fastapi import APIRouter, Request
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/link")
async def initiate_oauth(request: Request):
    """
    Initiates the OAuth flow for linking a Telegram user with their Google account.
    """
    # TODO: Implement state generation and storage
    # TODO: Generate Google OAuth URL
    return {"message": "OAuth flow not yet implemented", "status": "in_progress"}


@router.get("/callback")
async def oauth_callback(code: str, state: str):
    """
    Handles the OAuth callback from Google.
    """
    # TODO: Implement OAuth callback handling
    # TODO: Verify state
    # TODO: Exchange code for tokens
    # TODO: Store user mapping
    return {"message": "OAuth callback not yet implemented", "status": "in_progress"}
