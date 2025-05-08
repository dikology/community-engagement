from google_auth_oauthlib.flow import Flow
from app.core.config import get_settings
import secrets
from typing import Dict, Any

settings = get_settings()


def create_oauth_flow() -> Flow:
    """Create a Google OAuth flow instance."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ],
        redirect_uri=settings.redirect_uri,
    )


def generate_state() -> str:
    """Generate a secure random state for OAuth flow."""
    return secrets.token_urlsafe(32)


def create_authorization_url(telegram_user_id: str) -> tuple[str, str]:
    """
    Create the Google OAuth authorization URL.

    Args:
        telegram_user_id: The Telegram user ID to associate with this OAuth flow

    Returns:
        tuple: (authorization_url, state)
    """
    flow = create_oauth_flow()
    state = generate_state()

    # Store state with telegram_user_id (this should be implemented with your storage solution)
    # For now, we'll just return the state
    # TODO: Implement state storage

    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent",
    )

    return authorization_url, state


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Exchange the authorization code for tokens.

    Args:
        code: The authorization code from Google

    Returns:
        dict: The token response containing access_token, refresh_token, etc.
    """
    flow = create_oauth_flow()
    flow.fetch_token(code=code)

    # Get the credentials
    credentials = flow.credentials

    # Get user info
    # TODO: Implement user info retrieval

    return {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes,
    }
