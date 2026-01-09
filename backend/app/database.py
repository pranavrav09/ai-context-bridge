from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.LOG_LEVEL == "debug",
    pool_size=settings.DATABASE_POOL_SIZE if "postgresql" in settings.DATABASE_URL else 5,
    max_overflow=settings.DATABASE_MAX_OVERFLOW if "postgresql" in settings.DATABASE_URL else 10,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


# Dependency to get database session
async def get_db():
    """
    Async generator that yields database sessions.
    Use with FastAPI's Depends().
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
