from fastapi import APIRouter, Depends, HTTPException, status, Request
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

from app.schemas.requests import IntegrationRequest, IntegrationConfig, IntegrationType
from app.schemas.responses import IntegrationResponse, IntegrationStatus, ErrorResponse
from app.core.security import get_current_user

router = APIRouter(
    prefix="/integrations",
    tags=["integrations"],
    dependencies=[Depends(get_current_user)],
    responses={
        404: {"model": ErrorResponse, "description": "Not found"},
        400: {"model": ErrorResponse, "description": "Bad request"},
    },
)

# In-memory storage for demo purposes
# In a real app, this would be a database
integrations_db: Dict[str, Dict[str, Any]] = {}

@router.post("", response_model=IntegrationResponse)
async def manage_integration(
    request: IntegrationRequest,
    user: dict = Depends(get_current_user)
) -> IntegrationResponse:
    """
    Create, update, or delete an integration.
    
    Actions:
    - create: Create a new integration
    - update: Update an existing integration
    - delete: Delete an integration
    - sync: Trigger a sync for an integration
    """
    user_id = user.get("sub")
    now = datetime.now(timezone.utc)
    
    if request.action == "create":
        if not request.config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Config is required for create action"
            )
        
        integration_id = str(uuid.uuid4())
        integration = {
            "id": integration_id,
            "user_id": user_id,
            "type": request.config.type,
            "status": IntegrationStatus.ACTIVE,
            "settings": request.config.settings,
            "enabled": request.config.enabled,
            "created_at": now,
            "updated_at": now,
            "last_synced": None,
        }
        integrations_db[integration_id] = integration
        
        return IntegrationResponse(**integration)
    
    elif request.action == "update":
        if not request.integration_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="integration_id is required for update action"
            )
        
        if request.integration_id not in integrations_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        integration = integrations_db[request.integration_id]
        if integration["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this integration"
            )
        
        if request.config:
            integration.update({
                "type": request.config.type,
                "settings": request.config.settings,
                "enabled": request.config.enabled,
                "updated_at": now,
            })
        
        return IntegrationResponse(**integration)
    
    elif request.action == "delete":
        if not request.integration_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="integration_id is required for delete action"
            )
        
        if request.integration_id not in integrations_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        integration = integrations_db[request.integration_id]
        if integration["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this integration"
            )
        
        del integrations_db[request.integration_id]
        return IntegrationResponse(**integration)
    
    elif request.action == "sync":
        if not request.integration_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="integration_id is required for sync action"
            )
        
        if request.integration_id not in integrations_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Integration not found"
            )
        
        integration = integrations_db[request.integration_id]
        if integration["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to sync this integration"
            )
        
        # TODO: Implement actual sync logic
        integration["last_synced"] = now
        integration["updated_at"] = now
        
        return IntegrationResponse(**integration)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid action: {request.action}"
        )

@router.get("", response_model=List[IntegrationResponse])
async def list_integrations(
    type: Optional[str] = None,
    enabled: Optional[bool] = None,
    user: dict = Depends(get_current_user)
) -> List[IntegrationResponse]:
    """
    List all integrations for the current user.
    
    Can be filtered by type and enabled status.
    """
    user_id = user.get("sub")
    
    # Filter integrations by user_id
    user_integrations = [
        IntegrationResponse(**i) for i in integrations_db.values() 
        if i["user_id"] == user_id
    ]
    
    # Apply filters
    if type is not None:
        user_integrations = [i for i in user_integrations if i.type == type]
    
    if enabled is not None:
        user_integrations = [i for i in user_integrations if i.enabled == enabled]
    
    return user_integrations

@router.get("/types", response_model=List[Dict[str, Any]])
async def list_integration_types() -> List[Dict[str, Any]]:
    """
    List all available integration types.
    
    Returns metadata about each integration type, including required settings.
    """
    return [
        {
            "type": "telegram",
            "name": "Telegram",
            "description": "Connect your Telegram account to forward messages",
            "icon": "telegram",
            "settings_schema": {
                "type": "object",
                "required": ["api_token"],
                "properties": {
                    "api_token": {
                        "type": "string",
                        "description": "Telegram bot API token"
                    },
                    "auto_forward": {
                        "type": "boolean",
                        "default": True,
                        "description": "Automatically forward new messages"
                    }
                }
            }
        },
        {
            "type": "rss",
            "name": "RSS Feed",
            "description": "Subscribe to an RSS feed",
            "icon": "rss",
            "settings_schema": {
                "type": "object",
                "required": ["feed_url"],
                "properties": {
                    "feed_url": {
                        "type": "string",
                        "format": "uri",
                        "description": "URL of the RSS feed"
                    },
                    "poll_interval": {
                        "type": "integer",
                        "default": 3600,
                        "description": "Polling interval in seconds"
                    }
                }
            }
        }
    ]
