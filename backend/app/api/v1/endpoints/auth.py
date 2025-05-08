from fastapi import APIRouter, HTTPException
from app.core.config import get_settings
from app.core.oauth import create_authorization_url, exchange_code_for_tokens
from app.models.user import UserMapping, OAuthState
from datetime import datetime, timedelta
import httpx
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# Temporary in-memory storage (replace with proper database storage)
oauth_states: dict[str, OAuthState] = {}
user_mappings: dict[str, UserMapping] = {}


@router.get("/link")
async def initiate_oauth(telegram_user_id: str):
    """
    Initiates the OAuth flow for linking a Telegram user with their Google account.

    Args:
        telegram_user_id: The Telegram user ID to link with Google account
    """
    logger.info(f"Starting OAuth flow for Telegram user: {telegram_user_id}")

    # Generate authorization URL and state
    auth_url, state = create_authorization_url(telegram_user_id)
    logger.info(f"Generated OAuth URL with state: {state}")

    # Store state information
    oauth_state = OAuthState(
        state=state,
        telegram_user_id=telegram_user_id,
        expires_at=datetime.utcnow()
        + timedelta(minutes=10),  # State expires in 10 minutes
    )
    oauth_states[state] = oauth_state
    logger.info(f"Stored OAuth state for user {telegram_user_id}")

    return {
        "authorization_url": auth_url,
        "state": state,
        "expires_at": oauth_state.expires_at.isoformat(),
    }


# Note: This endpoint will be mounted at /oauth/callback in main.py
@router.get("/callback")
async def oauth_callback(code: str, state: str):
    """
    Handles the OAuth callback from Google.

    Args:
        code: The authorization code from Google
        state: The state parameter to verify the request
    """
    logger.info(f"Received OAuth callback with state: {state}")

    # Verify state
    if state not in oauth_states:
        logger.error(f"Invalid state parameter: {state}")
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    oauth_state = oauth_states[state]
    logger.info(f"Found OAuth state for user: {oauth_state.telegram_user_id}")

    # Check if state has expired
    if datetime.utcnow() > oauth_state.expires_at:
        logger.error(f"State has expired for user: {oauth_state.telegram_user_id}")
        del oauth_states[state]
        raise HTTPException(status_code=400, detail="State has expired")

    # Check if state has already been used
    if oauth_state.is_used:
        logger.error(f"State already used for user: {oauth_state.telegram_user_id}")
        raise HTTPException(status_code=400, detail="State has already been used")

    # Mark state as used
    oauth_state.is_used = True

    try:
        # Exchange code for tokens
        logger.info("Exchanging code for tokens")
        tokens = await exchange_code_for_tokens(code)

        # Get user info from Google
        logger.info("Fetching user info from Google")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            user_info = response.json()
            logger.info(f"Retrieved user info for email: {user_info.get('email')}")

        # Create or update user mapping
        user_mapping = UserMapping(
            telegram_user_id=oauth_state.telegram_user_id,
            google_email=user_info["email"],
            last_used_at=datetime.utcnow(),
        )
        user_mappings[oauth_state.telegram_user_id] = user_mapping
        logger.info(
            f"Created user mapping for Telegram user {oauth_state.telegram_user_id}"
        )

        return {
            "status": "success",
            "message": "Successfully linked Telegram account with Google account",
            "email": user_info["email"],
        }

    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to complete OAuth flow: {str(e)}"
        )
    finally:
        # Clean up used state
        del oauth_states[state]
        logger.info(f"Cleaned up OAuth state for user: {oauth_state.telegram_user_id}")
