"""SQLAlchemy model for users."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    select,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.sql.expression import text

from app.core.config import settings
from app.models.base import Base
from app.schemas.user import UserCreate, UserUpdate


class User(Base):
    """User model for database representation."""
    
    __tablename__ = "users"
    
    # Authentication
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        comment="User's email address, must be unique"
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Hashed password, nullable for OAuth users"
    )
    
    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="User's full name"
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="URL to user's avatar image"
    )
    
    # Preferences
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        server_default="UTC",
        comment="User's timezone"
    )
    locale: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        server_default="en-US",
        comment="User's locale (e.g., en-US, ru-RU)"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
        comment="Whether the user account is active"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="Whether the user has verified their email"
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
        comment="Whether the user has superuser privileges"
    )
    
    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last login timestamp"
    )
    
    # Metadata
    metadata_: Mapped[Dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="{}",
        comment="Additional user metadata as JSON"
    )
    
    # Relationships
    # tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    # oauth_accounts = relationship("OAuthAccount", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"
    
    @classmethod
    async def get_by_email(cls, db: AsyncSession, email: str) -> Optional["User"]:
        """Get a user by email."""
        result = await db.execute(select(cls).where(cls.email == email))
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, user_id: UUID) -> Optional["User"]:
        """Get a user by ID."""
        result = await db.execute(select(cls).where(cls.id == user_id))
        return result.scalar_one_or_none()
    
    @classmethod
    async def create(
        cls, 
        db: AsyncSession, 
        user_in: UserCreate,
        is_superuser: bool = False,
        is_verified: bool = False,
    ) -> "User":
        """Create a new user."""
        from app.core.security import get_password_hash
        
        db_user = cls(
            email=user_in.email,
            hashed_password=get_password_hash(user_in.password) if user_in.password else None,
            full_name=user_in.full_name,
            avatar_url=user_in.avatar_url,
            timezone=user_in.timezone or "UTC",
            locale=user_in.locale or "en-US",
            is_active=user_in.is_active if user_in.is_active is not None else True,
            is_verified=is_verified or user_in.is_verified or False,
            is_superuser=is_superuser,
            metadata_=user_in.metadata_ or {},
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    
    async def update(
        self, 
        db: AsyncSession,
        user_in: UserUpdate,
    ) -> "User":
        """Update user data."""
        from app.core.security import get_password_hash
        
        update_data = user_in.dict(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data:
            self.hashed_password = get_password_hash(update_data["password"])
        
        # Update other fields
        for field, value in update_data.items():
            if field != "password" and hasattr(self, field):
                setattr(self, field, value)
        
        self.updated_at = datetime.utcnow()
        
        db.add(self)
        await db.commit()
        await db.refresh(self)
        return self
    
    async def delete(self, db: AsyncSession) -> bool:
        """Delete the user."""
        await db.delete(self)
        await db.commit()
        return True
    
    async def record_login(self, db: AsyncSession) -> None:
        """Record the user's login time."""
        self.last_login_at = datetime.utcnow()
        db.add(self)
        await db.commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "timezone": self.timezone,
            "locale": self.locale,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_superuser": self.is_superuser,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "metadata": self.metadata_,
        }
