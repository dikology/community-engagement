from fastapi import APIRouter
from fastapi.responses import HTMLResponse
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


@router.get("/link", response_class=HTMLResponse)
async def initiate_oauth(telegram_user_id: str):
    """
    Initiates the OAuth flow for linking a Telegram user with their Google account.
    Returns an HTML page that automatically redirects to the OAuth URL.

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

    # Return HTML that automatically redirects to the OAuth URL
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Redirecting to Google OAuth...</title>
        <meta http-equiv="refresh" content="0;url={auth_url}">
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f5f5f5;
            }}
            .container {{
                text-align: center;
                padding: 2rem;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .spinner {{
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Redirecting to Google...</h2>
            <div class="spinner"></div>
            <p>If you are not redirected automatically, <a href="{auth_url}">click here</a>.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(state: str, code: str):
    """
    Handles the OAuth callback from Google.
    Returns an HTML success page after successful authentication.
    """
    logger.info(f"Received OAuth callback with state: {state}")

    # Verify state
    oauth_state = oauth_states.get(state)
    if not oauth_state:
        logger.error(f"Invalid or expired state: {state}")
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Failed</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f5f5f5;
                    }
                    .container {
                        text-align: center;
                        padding: 2rem;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .error {
                        color: #dc3545;
                        margin: 20px 0;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Authentication Failed</h2>
                    <p class="error">Invalid or expired authentication state.</p>
                    <p>Please try again from your Telegram bot.</p>
                </div>
            </body>
            </html>
            """,
            status_code=400,
        )

    if oauth_state.expires_at < datetime.utcnow():
        logger.error(f"Expired state for user: {oauth_state.telegram_user_id}")
        return HTMLResponse(
            content="""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Expired</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f5f5f5;
                    }
                    .container {
                        text-align: center;
                        padding: 2rem;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }
                    .error {
                        color: #dc3545;
                        margin: 20px 0;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Authentication Expired</h2>
                    <p class="error">Your authentication session has expired.</p>
                    <p>Please try again from your Telegram bot.</p>
                </div>
            </body>
            </html>
            """,
            status_code=400,
        )

    logger.info(f"Found OAuth state for user: {oauth_state.telegram_user_id}")

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
            logger.info(f"Retrieved user info for email: {user_info['email']}")

        # Create user mapping
        user_mapping = UserMapping(
            telegram_user_id=oauth_state.telegram_user_id,
            google_email=user_info["email"],
            last_used_at=datetime.utcnow(),
        )
        user_mappings[oauth_state.telegram_user_id] = user_mapping
        logger.info(
            f"Created user mapping for Telegram user {oauth_state.telegram_user_id}"
        )

        # Return success page
        success_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                }
                .container {
                    text-align: center;
                    padding: 2rem;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .success {
                    color: #28a745;
                    margin: 20px 0;
                }
                .checkmark {
                    color: #28a745;
                    font-size: 48px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Authentication Successful!</h2>
                <div class="checkmark">✓</div>
                <p class="success">Your Google account has been successfully linked.</p>
                <p>You can now return to your Telegram bot and continue using the service.</p>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=success_html)

    except Exception as e:
        logger.error(f"Error in OAuth callback: {str(e)}")
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication Error</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        margin: 0;
                        background-color: #f5f5f5;
                    }}
                    .container {{
                        text-align: center;
                        padding: 2rem;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .error {{
                        color: #dc3545;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>Authentication Error</h2>
                    <p class="error">Failed to complete authentication: {str(e)}</p>
                    <p>Please try again from your Telegram bot.</p>
                </div>
            </body>
            </html>
            """,
            status_code=500,
        )
    finally:
        # Clean up used state
        if state in oauth_states:
            del oauth_states[state]
            logger.info(
                f"Cleaned up OAuth state for user: {oauth_state.telegram_user_id}"
            )
