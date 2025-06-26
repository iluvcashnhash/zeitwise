"""API endpoints for the detox pipeline."""
import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_db, get_current_user
from app.models.user_model import User
from app.services.detox.pipeline import DetoxPipeline, DetoxAnalysis
from app.db.config import get_db as get_db_session
from app.models.detox_model import DetoxItem

# Configure logging
logger = logging.getLogger(__name__)


class DetoxRequest(BaseModel):
    """Request model for detox pipeline."""
    text: str = Field(..., description="Text to analyze")
    generate_meme: bool = Field(
        True, 
        description="Whether to generate a meme if content is sensational"
    )


class DetoxResponse(BaseModel):
    """Response model for detox pipeline."""
    id: str = Field(..., description="Detox item ID")
    status: str = Field(..., description="Processing status")
    original_text: str = Field(..., description="Original input text")
    masked_text: Optional[str] = Field(None, description="Text with entities masked")
    is_sensational: Optional[bool] = Field(None, description="Whether content is sensational")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    meme_task_id: Optional[str] = Field(None, description="Meme generation task ID if applicable")
    error: Optional[str] = Field(None, description="Error message if processing failed")


# Create router
router = APIRouter()

# Initialize pipeline
pipeline = DetoxPipeline()


async def process_detox_pipeline(
    db: AsyncSession,
    text: str,
    generate_meme: bool = True,
    user_id: Optional[UUID] = None
) -> Dict[str, Any]:
    """
    Process text through the detox pipeline.
    
    Args:
        db: Database session
        text: Text to process
        generate_meme: Whether to generate a meme if content is sensational
        user_id: Optional user ID for attribution
        
    Returns:
        Dict with processing results
    """
    try:
        # Process the text through the pipeline
        result = await pipeline.process(
            text=text,
            db=db,
            generate_meme=generate_meme
        )
        
        # Add user ID to the result if provided
        if user_id:
            result["user_id"] = user_id
            
        return {
            "status": "completed",
            **result
        }
        
    except Exception as e:
        logger.error(f"Error in detox pipeline: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "original_text": text
        }


@router.post(
    "/process",
    response_model=DetoxResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Process text through detox pipeline",
    description="""
    Process text through the detox pipeline to analyze and potentially detoxify it.
    This is an asynchronous operation that returns immediately with a task ID.
    """,
)
async def process_text(
    request: DetoxRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DetoxResponse:
    """
    Process text through the detox pipeline.
    
    This endpoint starts a background task to process the text and returns immediately
    with a task ID that can be used to check the status of the processing.
    """
    try:
        # Create a new detox item in the database
        detox_item = DetoxItem(
            original_text=request.text,
            status="pending",
            user_id=current_user.id if current_user else None
        )
        
        db.add(detox_item)
        await db.commit()
        await db.refresh(detox_item)
        
        # Start background task to process the text
        background_tasks.add_task(
            process_detox_background,
            detox_id=detox_item.id,
            text=request.text,
            generate_meme=request.generate_meme,
            user_id=current_user.id if current_user else None
        )
        
        return DetoxResponse(
            id=str(detox_item.id),
            status="pending",
            original_text=request.text
        )
        
    except Exception as e:
        logger.error(f"Error starting detox pipeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start detox pipeline: {str(e)}"
        )


async def process_detox_background(
    detox_id: UUID,
    text: str,
    generate_meme: bool = True,
    user_id: Optional[UUID] = None
) -> None:
    """
    Background task to process text through the detox pipeline.
    
    Args:
        detox_id: ID of the detox item
        text: Text to process
        generate_meme: Whether to generate a meme if content is sensational
        user_id: Optional user ID for attribution
    """
    async with get_db_session() as db:
        try:
            # Get the detox item
            detox_item = await db.get(DetoxItem, detox_id)
            if not detox_item:
                logger.error(f"Detox item not found: {detox_id}")
                return
                
            # Process the text through the pipeline
            result = await process_detox_pipeline(
                db=db,
                text=text,
                generate_meme=generate_meme,
                user_id=user_id
            )
            
            # Update the detox item with the results
            if result["status"] == "completed":
                detox_item.status = "completed"
                detox_item.masked_text = result.get("masked_text")
                detox_item.analysis = result.get("analysis", {}).get("analysis")
                detox_item.is_sensational = result.get("analysis", {}).get("is_sensational", False)
                detox_item.confidence = result.get("analysis", {}).get("confidence", 0.0)
                detox_item.entities = result.get("entities", [])
                detox_item.similar_items = result.get("similar_items", [])
                detox_item.meme_task_id = result.get("meme_data", {}).get("task_id") if result.get("meme_data") else None
                detox_item.metadata = {
                    "key_points": result.get("analysis", {}).get("key_points", []),
                    "meme_status": "pending" if result.get("meme_data") else None
                }
            else:
                detox_item.status = "error"
                detox_item.metadata = {
                    "error": result.get("error", "Unknown error")
                }
            
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error in background detox processing: {e}", exc_info=True)
            try:
                # Try to update the detox item with the error
                detox_item.status = "error"
                detox_item.metadata = {
                    "error": str(e)
                }
                await db.commit()
            except Exception as inner_e:
                logger.error(f"Error updating detox item with error: {inner_e}", exc_info=True)


@router.get(
    "/status/{detox_id}",
    response_model=DetoxResponse,
    summary="Get detox processing status",
    description="""
    Get the status of a detox processing task.
    """,
)
async def get_detox_status(
    detox_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> DetoxResponse:
    """
    Get the status of a detox processing task.
    
    Args:
        detox_id: ID of the detox item
        
    Returns:
        DetoxResponse with current status
    """
    try:
        # Get the detox item
        detox_item = await db.get(DetoxItem, detox_id)
        if not detox_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Detox item not found: {detox_id}"
            )
        
        # Check permissions (users can only see their own items or admin)
        if current_user and current_user.id != detox_item.user_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource"
            )
        
        return DetoxResponse(
            id=str(detox_item.id),
            status=detox_item.status,
            original_text=detox_item.original_text,
            masked_text=detox_item.masked_text,
            is_sensational=detox_item.is_sensational,
            confidence=detox_item.confidence,
            meme_task_id=detox_item.meme_task_id,
            error=detox_item.metadata.get("error") if detox_item.status == "error" else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detox status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detox status: {str(e)}"
        )
