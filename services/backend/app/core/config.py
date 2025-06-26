from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Dict, List, Literal, Optional, Union
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "ZeitWise Backend"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    TESTING: bool = False
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here"  # Change in production!
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:19006",
        "http://localhost:8000",
    ]
    
    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "zeitwise"
    DATABASE_URI: Optional[PostgresDsn] = None
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    
    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"
    
    # Supabase settings
    SUPABASE_URL: str = "https://your-project.supabase.co"
    SUPABASE_KEY: str = "your-anon-key"  # Supabase anon/public key
    SUPABASE_JWT_SECRET: str = "your-jwt-secret"  # Used to verify JWT tokens
    SUPABASE_SERVICE_ROLE_KEY: str = "your-service-role-key"  # For admin operations
    SUPABASE_AUTH_COOKIE_NAME: str = "sb-access-token"
    SUPABASE_REFRESH_COOKIE_NAME: str = "sb-refresh-token"
    SUPABASE_TOKEN_EXPIRY: int = 3600  # 1 hour
    SUPABASE_REFRESH_TOKEN_EXPIRY: int = 60 * 60 * 24 * 7  # 7 days
    
    # LLM settings
    OPENAI_API_KEY: str = ""
    GROK_API_KEY: str = ""
    
    # TTS settings
    SILERO_TTS_MODEL: str = "v3_en"
    
    # Security
    ALLOWED_HOSTS: List[str] = ["*"]
    SECURE_COOKIES: bool = True
    
    # First superuser
    FIRST_SUPERUSER_EMAIL: str = "admin@example.com"
    FIRST_SUPERUSER_PASSWORD: str = "changeme"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @property
    def DATABASE_URL(self) -> str:
        """Generate database URL from environment variables."""
        if self.DATABASE_URI is not None:
            return str(self.DATABASE_URI)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Generate synchronous database URL for Alembic."""
        if self.DATABASE_URI is not None:
            return str(self.DATABASE_URI).replace("postgresql+asyncpg", "postgresql")
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    @property
    def REDIS_URL(self) -> str:
        """Generate Redis URL from environment variables."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def check_environment(cls, v: str) -> str:
        """Validate environment value."""
        if v not in ["development", "testing", "production"]:
            raise ValueError("ENVIRONMENT must be one of: development, testing, production")
        return v
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running tests."""
        return self.TESTING

# Create settings instance
settings = Settings()
