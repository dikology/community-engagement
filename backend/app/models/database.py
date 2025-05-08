from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class UserMapping(Base):
    """SQLAlchemy model for storing Telegram-Google user mappings."""

    __tablename__ = "user_mappings"

    telegram_user_id = Column(String, primary_key=True)
    google_email = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class OAuthState(Base):
    """SQLAlchemy model for storing OAuth state information."""

    __tablename__ = "oauth_states"

    state = Column(String, primary_key=True)
    telegram_user_id = Column(
        String, ForeignKey("user_mappings.telegram_user_id"), nullable=False
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
