"""Database configuration and session management."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.models import Base

# Database URL - using SQLite for MVP, can upgrade to PostgreSQL later
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./coverageiq.db")

# Create async engine with SQLite-specific settings for async operations
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific: allow concurrent access, use timeout for locks
    connect_args = {
        "check_same_thread": False,
        "timeout": 30
    }

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    connect_args=connect_args,
    # Pool settings to prevent concurrent connection issues
    pool_pre_ping=True,
    pool_size=1,  # SQLite works best with single connection
    max_overflow=0
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for getting database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
