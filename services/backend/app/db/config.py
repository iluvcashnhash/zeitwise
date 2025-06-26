"""Database configuration and session management."""
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# Create async engine
DATABASE_URL = settings.DATABASE_URL

# Check if we're in test mode
if "pytest" in str(os.getpid()):
    DATABASE_URL = settings.TEST_DATABASE_URL
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.SQL_ECHO,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        DATABASE_URL,
        echo=settings.SQL_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
    )

# Create async session factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# Base class for all models
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

async def create_tables():
    """Create all tables in the database."""
    from sqlalchemy.ext.asyncio import AsyncEngine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_tables():
    """Drop all tables in the database (for testing)."""
    from sqlalchemy.ext.asyncio import AsyncEngine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
