from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

class HealthStatus(str, Enum):
    OK = "ok"
    ERROR = "error"

class HealthCheckResponse(BaseModel):
    """Health check response model."""
    status: HealthStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    services: Dict[str, HealthStatus] = {}

class ChatMessageResponse(BaseModel):
    """Response model for a single chat message."""
    id: str
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    message: ChatMessageResponse
    conversation_id: Optional[str] = None
    usage: Dict[str, int] = {}
    finish_reason: Optional[str] = None

class HistoricalParallel(BaseModel):
    """A historical parallel to current events."""
    event: str
    year: int
    similarity: float = Field(..., ge=0.0, le=1.0)
    description: str
    source: Optional[str] = None

class AnalysisResult(BaseModel):
    """Analysis of the content."""
    summary: str
    key_points: List[str]
    sentiment: float = Field(..., ge=-1.0, le=1.0)
    tags: List[str] = []

class MemeImage(BaseModel):
    """Generated meme image."""
    url: Optional[HttpUrl] = None
    text: Optional[str] = None
    style: Optional[str] = "default"

class DetoxResponse(BaseModel):
    """Response model for detox endpoint."""
    id: str
    original_content: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    historical_parallels: Optional[List[HistoricalParallel]] = None
    analysis: Optional[AnalysisResult] = None
    meme: Optional[MemeImage] = None
    metadata: Dict[str, Any] = {}

class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SYNCING = "syncing"

class IntegrationResponse(BaseModel):
    """Response model for integrations."""
    id: str
    user_id: str
    type: str
    status: IntegrationStatus
    settings: Dict[str, Any] = {}
    enabled: bool = True
    last_synced: Optional[datetime] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
