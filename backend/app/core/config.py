from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Community Engagement Bot"

    # Telegram Settings
    TELEGRAM_BOT_TOKEN: str

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: Optional[str] = None  # Will be computed

    # App Settings
    APP_BASE_URL: str
    WEBHOOK_SECRET: str

    # Database Settings
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None

    @property
    def redirect_uri(self) -> str:
        """Compute the full redirect URI."""
        return f"{self.APP_BASE_URL}/oauth/callback"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
