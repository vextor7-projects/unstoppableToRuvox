from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# Create an asynchronous engine.
# The `DATABASE_URL` from settings is already formatted with "+asyncpg"
# by the pydantic validator in config.py.
async_engine = create_async_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,
    echo=False,  # Set to True in development to see SQL queries
)

# Create an asynchronous session factory (async_sessionmaker)
# This is the modern replacement for sessionmaker() in async SQLAlchemy
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # This is a good default for FastAPI dependencies
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a new SQLAlchemy async session.
    
    This dependency will be used in API endpoints to get a database session
    and will automatically handle opening and closing the session,
    as well as rolling back transactions on errors.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            # The session is automatically closed by the context manager
            pass
