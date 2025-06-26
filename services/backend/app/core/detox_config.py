"""Configuration for the detox pipeline."""
from typing import Dict, Any, List, Optional
from pydantic import BaseSettings, Field, validator

class DetoxSettings(BaseSettings):
    """Settings for the detox pipeline."""
    
    # Entity detection
    ENTITY_TYPES: List[str] = Field(
        default_factory=lambda: ["PERSON", "ORG", "GPE", "LOC", "PRODUCT", "EVENT", "WORK_OF_ART"],
        description="List of entity types to mask"
    )
    
    # Qdrant settings
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant server URL"
    )
    QDRANT_API_KEY: Optional[str] = Field(
        default=None,
        description="API key for Qdrant"
    )
    QDRANT_COLLECTION: str = Field(
        default="news_embeddings",
        description="Qdrant collection name for news embeddings"
    )
    
    # Embedding model
    EMBEDDING_MODEL: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        description="Sentence transformer model for text embeddings"
    )
    
    # Similarity search
    SIMILARITY_THRESHOLD: float = Field(
        default=0.7,
        description="Minimum similarity score (0-1) for considering items similar"
    )
    MAX_SIMILAR_ITEMS: int = Field(
        default=5,
        description="Maximum number of similar items to return"
    )
    
    # LLM settings
    LLM_TEMPERATURE: float = Field(
        default=0.3,
        description="Temperature for LLM generation (0-2)"
    )
    LLM_MAX_TOKENS: int = Field(
        default=500,
        description="Maximum number of tokens to generate"
    )
    
    # Meme generation
    ENABLE_MEME_GENERATION: bool = Field(
        default=True,
        description="Whether to enable meme generation for sensational content"
    )
    
    # Logging
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    class Config:
        env_prefix = "DETOX_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    @validator("ENTITY_TYPES", pre=True)
    def parse_entity_types(cls, v):
        """Parse entity types from comma-separated string if needed."""
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v

# Create settings instance
detox_settings = DetoxSettings()
