"""Pydantic models for meme generation API."""
from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, HttpUrl

class MemeStatus(str, Enum):
    """Status of a meme generation task."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class MemeBase(BaseModel):
    """Base model for meme data."""
    headline: str = Field(..., description="The headline to create a meme for")
    analysis: str = Field(..., description="Analysis of the headline")
    style: str = Field(..., description="Style/tone for the meme")

class MemeCreate(MemeBase):
    """Request model for creating a new meme."""
    pass

class MemeResponse(BaseModel):
    """Response model for meme generation."""
    status: MemeStatus = Field(..., description="Status of the meme generation")
    task_id: Optional[str] = Field(None, description="ID of the background task")
    message: str = Field(..., description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Result data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "pending",
                "task_id": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Meme generation started",
                "data": {
                    "headline": "AI takes over the world",
                    "style": "funny"
                }
            }
        }

class MemeResult(BaseModel):
    """Model for completed meme data."""
    text: str = Field(..., description="Generated meme text")
    gif_url: Optional[HttpUrl] = Field(None, description="URL of the generated GIF")
    public_url: Optional[HttpUrl] = Field(None, description="Public URL of the meme")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "When you realize you forgot to add the off switch to the AI",
                "gif_url": "https://media.giphy.com/media/example.gif",
                "public_url": "https://example.supabase.co/storage/v1/object/public/memes/123.json"
            }
        }

class MemeListResponse(BaseModel):
    """Response model for listing memes."""
    count: int = Field(..., description="Total number of memes")
    results: List[Dict[str, Any]] = Field(..., description="List of memes")
    
    class Config:
        schema_extra = {
            "example": {
                "count": 2,
                "results": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "headline": "AI takes over the world",
                        "style": "funny",
                        "text": "When you realize you forgot to add the off switch to the AI",
                        "gif_url": "https://media.giphy.com/media/example1.gif",
                        "created_at": "2023-06-26T12:00:00Z"
                    },
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "headline": "New study shows benefits of AI",
                        "style": "informative",
                        "text": "AI: Making the impossible possible, one algorithm at a time",
                        "gif_url": "https://media.giphy.com/media/example2.gif",
                        "created_at": "2023-06-25T12:00:00Z"
                    }
                ]
            }
        }
