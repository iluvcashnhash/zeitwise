"""API endpoints for meme generation."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user_model import User
from app.schemas.meme import MemeCreate, MemeResponse, MemeStatus
from app.tasks.meme_generation import generate_meme_async

router = APIRouter()

@router.post(
    "/generate",
    response_model=MemeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate a meme",
    description="""
    Generate a meme based on a headline, analysis, and style.
    This is an asynchronous operation that returns immediately with a task ID.
    """,
)
async def create_meme(
    meme_data: MemeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemeResponse:
    """
    Generate a meme asynchronously.
    
    This endpoint starts a background task to generate a meme and returns immediately
    with a task ID that can be used to check the status of the generation.
    """
    try:
        # Start the Celery task
        task = generate_meme.delay(
            headline=meme_data.headline,
            analysis=meme_data.analysis,
            style=meme_data.style
        )
        
        return MemeResponse(
            status=MemeStatus.PENDING,
            task_id=task.id,
            message="Meme generation started",
            data={
                "headline": meme_data.headline,
                "style": meme_data.style
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start meme generation: {str(e)}"
        )

@router.get(
    "/status/{task_id}",
    response_model=MemeResponse,
    summary="Check meme generation status",
    description="Check the status of a meme generation task.",
)
async def check_meme_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MemeResponse:
    """
    Check the status of a meme generation task.
    
    Args:
        task_id: The ID of the Celery task
        
    Returns:
        Current status and result (if available) of the task
    """
    from celery.result import AsyncResult
    from app.core.celery import app as celery_app
    
    task = AsyncResult(task_id, app=celery_app)
    
    if task.state == 'PENDING':
        return MemeResponse(
            status=MemeStatus.PENDING,
            task_id=task_id,
            message="Meme generation in progress"
        )
    elif task.state == 'SUCCESS':
        return MemeResponse(
            status=MemeStatus.COMPLETED,
            task_id=task_id,
            message="Meme generated successfully",
            data=task.result
        )
    elif task.state == 'FAILURE':
        return MemeResponse(
            status=MemeStatus.FAILED,
            task_id=task_id,
            message=f"Meme generation failed: {str(task.result)}"
        )
    else:
        return MemeResponse(
            status=MemeStatus.PENDING,
            task_id=task_id,
            message=f"Meme generation status: {task.state}"
        )
