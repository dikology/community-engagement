from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
import redis.asyncio as redis

settings = get_settings()

# PostgreSQL connection
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)

# Create async session factory
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Redis connection
redis_client = redis.from_url(settings.REDIS_URL) if settings.REDIS_URL else None


async def get_db():
    """Dependency for getting async database sessions."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis():
    """Dependency for getting Redis client."""
    if not redis_client:
        raise RuntimeError("Redis client not configured")
    return redis_client
