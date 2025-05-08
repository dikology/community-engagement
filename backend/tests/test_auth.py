import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app.main import app
from app.models.user import OAuthState

client = TestClient(app)

# Test data
TELEGRAM_USER_ID = "123456789"
GOOGLE_EMAIL = "test@example.com"
MOCK_STATE = "123456789:mock_state"
MOCK_CODE = "mock_auth_code"
MOCK_ACCESS_TOKEN = "mock_access_token"
MOCK_USER_INFO = {
    "email": GOOGLE_EMAIL,
    "name": "Test User",
    "picture": "https://example.com/photo.jpg",
}


@pytest.fixture
def mock_oauth_flow():
    """Mock the OAuth flow to return predictable values."""
    with patch("app.api.v1.endpoints.auth.create_oauth_flow") as mock:
        mock_flow = MagicMock()
        mock_flow.authorization_url.return_value = ("https://mock-auth-url", None)
        mock_flow.fetch_token.return_value = {"access_token": MOCK_ACCESS_TOKEN}
        mock.return_value = (mock_flow, MOCK_STATE)
        yield mock


@pytest.fixture
def mock_httpx_client():
    """Mock the httpx client for Google API calls."""
    with patch("app.api.v1.endpoints.auth.httpx.AsyncClient") as mock:

        async def mock_get(*args, **kwargs):
            response = MagicMock()
            response.json.return_value = MOCK_USER_INFO
            return response

        client = MagicMock()
        client.get = mock_get
        mock.return_value.__aenter__.return_value = client
        yield mock


@pytest.fixture
def mock_oauth_states():
    """Mock the OAuth states storage."""
    oauth_states = {}
    with patch("app.api.v1.endpoints.auth.oauth_states", oauth_states):
        yield oauth_states


@pytest.fixture
def mock_secrets():
    """Mock the secrets module to return predictable values."""
    with patch("app.core.oauth.secrets") as mock:
        mock.token_urlsafe.return_value = "mock_state"
        yield mock


def test_initiate_oauth(mock_oauth_flow, mock_oauth_states, mock_secrets):
    """Test the OAuth initiation endpoint."""
    # Get the mock flow from the fixture
    mock_flow = mock_oauth_flow.return_value[0]

    response = client.get(f"/api/v1/auth/link?telegram_user_id={TELEGRAM_USER_ID}")

    # Print response content for debugging
    print("\nResponse content:")
    print(response.text)

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Redirecting to Google" in response.text

    # Verify the mock was called correctly
    mock_oauth_flow.assert_called_once_with(TELEGRAM_USER_ID)
    mock_flow.authorization_url.assert_called_once_with(
        access_type="offline", include_granted_scopes="true", state=MOCK_STATE
    )

    # Get the actual URL used in the response
    auth_url = mock_flow.authorization_url.return_value[0]
    assert auth_url in response.text

    # Verify state was stored
    assert MOCK_STATE in mock_oauth_states
    assert mock_oauth_states[MOCK_STATE].telegram_user_id == TELEGRAM_USER_ID


def test_oauth_callback_success(
    mock_oauth_flow, mock_httpx_client, mock_oauth_states, mock_secrets
):
    """Test successful OAuth callback."""
    # First initiate OAuth to create state
    client.get(f"/api/v1/auth/link?telegram_user_id={TELEGRAM_USER_ID}")

    # Verify state exists
    assert MOCK_STATE in mock_oauth_states

    # Then test callback
    response = client.get(f"/oauth/callback?state={MOCK_STATE}&code={MOCK_CODE}")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Successful" in response.text
    assert "Your Google account has been successfully linked" in response.text

    # Verify state was cleaned up
    assert MOCK_STATE not in mock_oauth_states


def test_oauth_callback_invalid_state(mock_oauth_states):
    """Test OAuth callback with invalid state."""
    response = client.get(f"/oauth/callback?state=invalid_state&code={MOCK_CODE}")

    assert response.status_code == 400
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Failed" in response.text
    assert "Invalid or expired authentication state" in response.text


def test_oauth_callback_expired_state(mock_oauth_flow, mock_oauth_states, mock_secrets):
    """Test OAuth callback with expired state."""
    # Create an expired state
    expired_state = OAuthState(
        state=MOCK_STATE,
        telegram_user_id=TELEGRAM_USER_ID,
        expires_at=datetime.utcnow() - timedelta(minutes=1),
    )
    mock_oauth_states[MOCK_STATE] = expired_state

    response = client.get(f"/oauth/callback?state={MOCK_STATE}&code={MOCK_CODE}")

    assert response.status_code == 400
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Expired" in response.text
    assert "Your authentication session has expired" in response.text


def test_oauth_callback_google_error(
    mock_oauth_flow, mock_httpx_client, mock_oauth_states, mock_secrets
):
    """Test OAuth callback when Google API returns an error."""
    # First initiate OAuth to create state
    client.get(f"/api/v1/auth/link?telegram_user_id={TELEGRAM_USER_ID}")

    # Verify state exists
    assert MOCK_STATE in mock_oauth_states

    # Mock Google API error
    async def mock_get_error(*args, **kwargs):
        raise Exception("Google API Error")

    mock_httpx_client.return_value.__aenter__.return_value.get = mock_get_error

    response = client.get(f"/oauth/callback?state={MOCK_STATE}&code={MOCK_CODE}")

    assert response.status_code == 500
    assert "text/html" in response.headers["content-type"]
    assert "Authentication Error" in response.text
    assert "Failed to complete authentication" in response.text

    # Verify state was cleaned up
    assert MOCK_STATE not in mock_oauth_states


def test_oauth_flow_cleanup(
    mock_oauth_flow, mock_httpx_client, mock_oauth_states, mock_secrets
):
    """Test that OAuth state is cleaned up after use."""
    # First initiate OAuth to create state
    client.get(f"/api/v1/auth/link?telegram_user_id={TELEGRAM_USER_ID}")

    # Verify state exists
    assert MOCK_STATE in mock_oauth_states

    # Complete OAuth flow
    client.get(f"/oauth/callback?state={MOCK_STATE}&code={MOCK_CODE}")

    # Verify state is cleaned up
    assert MOCK_STATE not in mock_oauth_states
