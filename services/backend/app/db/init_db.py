"""Initialize the database with initial data."""
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.base import Base
from app.models.user_model import User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

async def init_models(engine: AsyncEngine) -> None:
    """Create database tables."""
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")

async def get_engine() -> AsyncEngine:
    """Get database engine."""
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_recycle=300,  # Recycle connections after 5 minutes
    )

async def get_session_maker(engine: AsyncEngine):
    """Get async session maker."""
    return sessionmaker(
        engine, 
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

async def init_db() -> None:
    """Initialize database with initial data."""
    engine = await get_engine()
    
    # Create tables
    await init_models(engine)
    
    # Create session
    async_session_maker = await get_session_maker(engine)
    
    # Create initial data
    await create_initial_data(async_session_maker)
    
    # Close the engine
    await engine.dispose()

async def create_initial_data(async_session_maker) -> None:
    """Create initial data in the database."""
    from app.core.security import get_password_hash
    
    # Check if we already have a superuser
    async with async_session_maker() as session:
        # Check if users table exists
        result = await session.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'users'
                )
                """
            )
        )
        users_table_exists = result.scalar()
        
        if not users_table_exists:
            logger.info("Users table does not exist, skipping initial data creation")
            return
            
        # Check if we already have a superuser
        result = await session.execute(
            select(User).where(User.email == settings.FIRST_SUPERUSER_EMAIL)
        )
        user = result.scalar_one_or_none()
        
        if user is None and settings.FIRST_SUPERUSER_EMAIL and settings.FIRST_SUPERUSER_PASSWORD:
            logger.info("Creating initial superuser")
            
            # Create superuser
            superuser = User(
                email=settings.FIRST_SUPERUSER_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                full_name="Admin",
                is_superuser=True,
                is_verified=True,
                is_active=True,
            )
            
            session.add(superuser)
            await session.commit()
            logger.info(f"Created initial superuser: {settings.FIRST_SUPERUSER_EMAIL}")
        else:
            logger.info("Superuser already exists, skipping creation")
