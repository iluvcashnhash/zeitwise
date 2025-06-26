"""
User models for the application.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from pydantic.types import constr
from uuid import UUID, uuid4

# Password constraints
PasswordStr = constr(min_length=8, max_length=100, regex=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).*$")

class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = "UTC"
    locale: Optional[str] = "en-US"
    is_active: bool = True
    is_verified: bool = False
    metadata_: Dict[str, Any] = Field(default_factory=dict, alias="metadata")

    class Config:
        from_attributes = True
        populate_by_name = True
        json_encoders = {
            UUID: str
        }

class UserCreate(UserBase):
    """Model for creating a new user."""
    password: PasswordStr
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

class UserUpdate(BaseModel):
    """Model for updating an existing user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    metadata_: Optional[Dict[str, Any]] = Field(default=None, alias="metadata")
    password: Optional[PasswordStr] = None

class UserInDB(UserBase):
    """User model for database representation."""
    id: UUID = Field(default_factory=uuid4)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        populate_by_name = True

class UserPublic(UserBase):
    """Public user model for API responses."""
    id: UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserWithToken(UserPublic):
    """User model with authentication tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class Token(BaseModel):
    """Authentication token model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic

class TokenData(BaseModel):
    """Token payload data."""
    sub: Optional[str] = None
    email: Optional[str] = None
    scopes: List[str] = []
    exp: Optional[int] = None
