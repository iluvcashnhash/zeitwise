"""Database dependencies for FastAPI."""
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.init_db import get_engine, get_session_maker
from app.core.config import settings

# Create engine and session maker at startup
engine = None
async_session_maker = None

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    global engine, async_session_maker
    
    # Initialize engine and session maker if not already done
    if engine is None:
        engine = await get_engine()
    if async_session_maker is None:
        async_session_maker = await get_session_maker(engine)
    
    # Create a new session for each request
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Reuse the same session for a single request
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides a database session."""
    async with get_db() as session:
        yield session

# Use this for type hints
DatabaseSession = Depends(get_db_session)
