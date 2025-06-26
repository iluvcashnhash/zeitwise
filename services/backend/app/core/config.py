from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Project settings
    PROJECT_NAME: str = "ZeitWise Backend"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here"  # Change in production!
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:19006"]
    
    # Database settings
    POSTGRES_SERVER: str = "postgres"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "zeitwise"
    DATABASE_URI: Optional[str] = None
    
    # Redis settings
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "redispass"
    
    # Qdrant settings
    QDRANT_URL: str = "http://qdrant:6333"
    
    # Supabase settings
    SUPABASE_URL: str = "http://localhost:54321"  # Local Supabase URL
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
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    def get_database_url(self) -> str:
        if self.DATABASE_URI:
            return self.DATABASE_URI
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
    
    def get_redis_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

# Create settings instance
settings = Settings()
