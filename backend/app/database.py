"""Database configuration and session management."""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.models import Base

# Database URL - using SQLite for MVP, can upgrade to PostgreSQL later
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./coverageiq.db")

# Create async engine with SQLite-specific settings for async operations
# For SQLite with aiosqlite, we disable connection pooling entirely to avoid
# concurrent access issues - each operation gets its own connection
connect_args = {}
engine_kwargs = {}

if DATABASE_URL.startswith("sqlite"):
    # SQLite-specific: use timeout for locks
    connect_args = {
        "timeout": 30
    }
    # Disable connection pooling for SQLite - prevents concurrent access errors
    engine_kwargs["poolclass"] = NullPool

engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    connect_args=connect_args,
    **engine_kwargs
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
