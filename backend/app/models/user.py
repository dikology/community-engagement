from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserMapping(BaseModel):
    """Model for storing Telegram-Google user mappings."""

    telegram_user_id: str
    google_email: str
    created_at: datetime = datetime.utcnow()
    last_used_at: Optional[datetime] = None
    is_active: bool = True


class OAuthState(BaseModel):
    """Model for storing OAuth state information."""

    state: str
    telegram_user_id: str
    created_at: datetime = datetime.utcnow()
    expires_at: datetime  # State should expire after a short time
    is_used: bool = False
