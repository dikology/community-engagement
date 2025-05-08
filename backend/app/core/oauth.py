from google_auth_oauthlib.flow import Flow
from app.core.config import get_settings
import secrets
from typing import Dict, Any, Tuple

settings = get_settings()


def create_oauth_flow(telegram_user_id: str) -> Tuple[Flow, str]:
    """
    Create a Google OAuth flow instance with state.

    Args:
        telegram_user_id: The Telegram user ID to include in the state

    Returns:
        Tuple[Flow, str]: (flow, state)
    """
    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uri": settings.redirect_uri,
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "openid",
        ],
    )

    # Set the redirect URI
    flow.redirect_uri = settings.redirect_uri

    # Generate a state that includes the telegram_user_id
    state = f"{telegram_user_id}:{secrets.token_urlsafe(32)}"

    return flow, state


def create_authorization_url(telegram_user_id: str) -> Tuple[str, str]:
    """
    Create the Google OAuth authorization URL with state.

    Args:
        telegram_user_id: The Telegram user ID to include in the state

    Returns:
        Tuple[str, str]: (authorization_url, state)
    """
    flow = create_oauth_flow()

    # Generate a state that includes the telegram_user_id
    state = f"{telegram_user_id}:{secrets.token_urlsafe(32)}"
    auth_url, _ = flow.authorization_url(
        access_type="offline", include_granted_scopes="true", state=state
    )
    return auth_url, state


async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """
    Exchange an authorization code for access and refresh tokens.

    Args:
        code: The authorization code from Google

    Returns:
        Dict[str, Any]: The token response containing access and refresh tokens
    """
    flow = create_oauth_flow()
    flow.fetch_token(code=code)
    return flow.credentials.token
