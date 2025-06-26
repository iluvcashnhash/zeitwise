from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """Role of the message sender in the chat."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    """A single message in the chat."""
    role: MessageRole
    content: str
    name: Optional[str] = None

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    messages: List[Message] = Field(
        ...,
        description="List of messages in the conversation",
        min_items=1
    )
    persona_id: str = Field(
        ...,
        description="ID of the persona to chat with",
        example="socrates"
    )
    temperature: float = Field(
        0.7,
        ge=0.0,
        le=2.0,
        description="Controls randomness in the response generation"
    )
    max_tokens: Optional[int] = Field(
        None,
        ge=1,
        le=4000,
        description="Maximum number of tokens to generate"
    )
    stream: bool = Field(
        False,
        description="Whether to stream the response"
    )

class DetoxContentType(str, Enum):
    """Type of content to detoxify."""
    TEXT = "text"
    URL = "url"
    IMAGE = "image"

class DetoxRequest(BaseModel):
    """Request model for detox endpoint."""
    content: str = Field(
        ...,
        description="The content to process (text, URL, or image data)",
        example="Breaking: Stock market crashes 50%!"
    )
    content_type: DetoxContentType = Field(
        DetoxContentType.TEXT,
        description="Type of the provided content"
    )
    include_historical_parallels: bool = Field(
        True,
        description="Whether to include historical parallels in the response"
    )
    include_analysis: bool = Field(
        True,
        description="Whether to include AI analysis in the response"
    )
    include_meme: bool = Field(
        True,
        description="Whether to generate and include a meme in the response"
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context for the request"
    )

class IntegrationType(str, Enum):
    """Type of integration."""
    TELEGRAM = "telegram"
    TWITTER = "twitter"
    RSS = "rss"
    CUSTOM = "custom"

class IntegrationConfig(BaseModel):
    """Configuration for an integration."""
    type: IntegrationType
    settings: Dict[str, Any]
    enabled: bool = True
    last_synced: Optional[datetime] = None

class IntegrationRequest(BaseModel):
    """Request model for managing integrations."""
    action: str = Field(..., description="Action to perform: 'create', 'update', 'delete', 'sync'")
    integration_id: Optional[str] = Field(None, description="ID of the integration to update/delete")
    config: Optional[IntegrationConfig] = Field(None, description="Configuration for create/update actions")
