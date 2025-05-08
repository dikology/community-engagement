import pytest
import os
from app.core.config import Settings


@pytest.fixture(autouse=True)
def test_env():
    """Set up test environment variables."""
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_bot_token"
    os.environ["GOOGLE_CLIENT_ID"] = "test_client_id"
    os.environ["GOOGLE_CLIENT_SECRET"] = "test_client_secret"
    os.environ["APP_BASE_URL"] = "http://localhost:8000"
    os.environ["WEBHOOK_SECRET"] = "test_webhook_secret"
    yield
    # Clean up environment variables after tests
    for key in [
        "TELEGRAM_BOT_TOKEN",
        "GOOGLE_CLIENT_ID",
        "GOOGLE_CLIENT_SECRET",
        "APP_BASE_URL",
        "WEBHOOK_SECRET",
    ]:
        if key in os.environ:
            del os.environ[key]


@pytest.fixture
def settings():
    """Get test settings."""
    return Settings()
