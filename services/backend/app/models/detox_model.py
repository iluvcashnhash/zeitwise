"""Database models for detox pipeline."""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from sqlalchemy import Column, String, Boolean, Float, JSON, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class DetoxItem(Base):
    """Model for storing detox analysis results."""
    __tablename__ = "detox_items"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, index=True, default=uuid4)
    original_text = Column(Text, nullable=False)
    analysis = Column(Text, nullable=False)
    is_sensational = Column(Boolean, default=False, index=True)
    confidence = Column(Float, default=0.0)
    entities = Column(JSON, default=list)  # List of dicts with entity info
    similar_items = Column(JSON, default=list)  # List of similar items from Qdrant
    meme_task_id = Column(String, nullable=True, index=True)  # Celery task ID for meme generation
    metadata = Column(JSON, default=dict)  # Additional metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "original_text": self.original_text,
            "analysis": self.analysis,
            "is_sensational": self.is_sensational,
            "confidence": self.confidence,
            "entities": self.entities or [],
            "similar_items": self.similar_items or [],
            "meme_task_id": self.meme_task_id,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetoxItem':
        """Create model instance from dictionary."""
        return cls(
            id=data.get("id", uuid4()),
            original_text=data["original_text"],
            analysis=data.get("analysis", ""),
            is_sensational=data.get("is_sensational", False),
            confidence=data.get("confidence", 0.0),
            entities=data.get("entities", []),
            similar_items=data.get("similar_items", []),
            meme_task_id=data.get("meme_task_id"),
            metadata=data.get("metadata", {})
        )
