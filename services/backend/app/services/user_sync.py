"""Service for syncing users between Supabase Auth and local database."""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from uuid import UUID

from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user_model import User
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.auth_provider import AuthProvider, get_auth_provider, is_social_provider, is_email_provider, is_phone_provider
from app.services.supabase_auth import supabase_auth_service

logger = logging.getLogger(__name__)

class UserSyncService:
    """Service for syncing users between Supabase Auth and local database."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def sync_user_from_supabase(
        self,
        user_id: str,
        update_if_exists: bool = True,
    ) -> User:
        """
        Sync a user from Supabase Auth to the local database.
        
        Args:
            user_id: The Supabase Auth user ID
            update_if_exists: Whether to update the user if they already exist
            
        Returns:
            The synced user
            
        Raises:
            HTTPException: If the user is not found in Supabase Auth
        """
        # Get user from Supabase Auth
        supabase_user = await supabase_auth_service.get_user_by_id(user_id)
        if not supabase_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in Supabase Auth",
            )
        
        # Check if user exists in local database
        user = await User.get_by_id(self.db, UUID(user_id))
        
        if user is None:
            # Create new user in local database
            return await self._create_user_from_supabase(supabase_user)
        elif update_if_exists:
            # Update existing user
            return await self._update_user_from_supabase(user, supabase_user)
        
        return user
    
    def _extract_provider_info(self, supabase_user: Dict[str, Any]) -> Dict[str, Any]:
        """Extract provider information from Supabase Auth user data."""
        user_metadata = supabase_user.get("user_metadata", {})
        app_metadata = supabase_user.get("app_metadata", {})
        
        # Get provider from user metadata or determine from identities
        provider = user_metadata.get("provider")
        if not provider and "identities" in supabase_user and supabase_user["identities"]:
            provider = supabase_user["identities"][0].get("provider")
        
        # Get all providers
        providers = set(user_metadata.get("providers", []))
        if provider and provider not in providers:
            providers.add(provider)
        
        # If no providers found but we have a provider, add it
        if not providers and provider:
            providers.add(provider)
        
        # If still no providers, try to determine from email/phone
        if not providers:
            if supabase_user.get("email"):
                providers.add("email")
            if supabase_user.get("phone"):
                providers.add("phone")
        
        return {
            "provider": provider or "email",  # Default to email if no provider found
            "providers": list(providers),
            "is_email_verified": bool(supabase_user.get("email_confirmed_at")),
            "is_phone_verified": bool(supabase_user.get("phone_confirmed_at")),
        }
    
    async def _create_user_from_supabase(self, supabase_user: Dict[str, Any]) -> User:
        """Create a new user in the local database from Supabase Auth user data."""
        from app.core.security import get_password_hash
        
        # Extract provider information
        provider_info = self._extract_provider_info(supabase_user)
        
        # Extract user data from Supabase Auth
        user_data = {
            "email": supabase_user.get("email"),
            "full_name": supabase_user.get("user_metadata", {}).get("full_name"),
            "avatar_url": supabase_user.get("user_metadata", {}).get("avatar_url"),
            "is_verified": provider_info["is_email_verified"] or provider_info["is_phone_verified"],
            "is_active": not supabase_user.get("banned_until"),
            "metadata_": {
                **supabase_user.get("user_metadata", {}),
                "app_metadata": supabase_user.get("app_metadata", {}),
                "providers": provider_info["providers"],
                "provider": provider_info["provider"],
            },
        }
        
        # Create user in local database
        user = User(
            id=UUID(supabase_user["id"]),
            **user_data,
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        logger.info(f"Created user in local database: {user.email} ({user.id})")
        return user
    
    async def _update_user_from_supabase(
        self, 
        user: User, 
        supabase_user: Dict[str, Any]
    ) -> User:
        """Update an existing user in the local database from Supabase Auth user data."""
        # Extract provider information
        provider_info = self._extract_provider_info(supabase_user)
        
        # Extract user data from Supabase Auth
        update_data = {}
        
        # Update email if changed
        if "email" in supabase_user and supabase_user["email"] != user.email:
            update_data["email"] = supabase_user["email"]
        
        # Update full name if changed
        full_name = supabase_user.get("user_metadata", {}).get("full_name")
        if full_name and full_name != user.full_name:
            update_data["full_name"] = full_name
        
        # Update avatar URL if changed
        avatar_url = supabase_user.get("user_metadata", {}).get("avatar_url")
        if avatar_url and avatar_url != user.avatar_url:
            update_data["avatar_url"] = avatar_url
        
        # Update verification status
        is_verified = provider_info["is_email_verified"] or provider_info["is_phone_verified"]
        if is_verified != user.is_verified:
            update_data["is_verified"] = is_verified
        
        # Update active status
        is_active = not supabase_user.get("banned_until")
        if is_active != user.is_active:
            update_data["is_active"] = is_active
        
        # Update metadata
        metadata = user.metadata_.copy()
        metadata_changed = False
        
        # Update user metadata
        if "user_metadata" in supabase_user:
            metadata.update(supabase_user["user_metadata"])
            metadata_changed = True
        
        # Update app metadata
        if "app_metadata" in supabase_user:
            metadata["app_metadata"] = supabase_user["app_metadata"]
            metadata_changed = True
        
        # Update provider information
        current_providers = set(metadata.get("providers", []))
        new_providers = set(provider_info["providers"])
        
        if current_providers != new_providers:
            metadata["providers"] = list(new_providers)
            metadata_changed = True
        
        if provider_info["provider"] and metadata.get("provider") != provider_info["provider"]:
            metadata["provider"] = provider_info["provider"]
            metadata_changed = True
        
        # Update verification status in metadata
        if metadata.get("email_verified") != provider_info["is_email_verified"]:
            metadata["email_verified"] = provider_info["is_email_verified"]
            metadata_changed = True
            
        if metadata.get("phone_verified") != provider_info["is_phone_verified"]:
            metadata["phone_verified"] = provider_info["is_phone_verified"]
            metadata_changed = True
        
        if metadata_changed:
            update_data["metadata_"] = metadata
        
        # Update user if there are changes
        if update_data:
            for key, value in update_data.items():
                setattr(user, key, value)
            
            user.updated_at = datetime.utcnow()
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
            
            logger.info(f"Updated user in local database: {user.email} ({user.id})")
        
        return user
    
    async def sync_current_user(self, request: Request) -> User:
        """
        Sync the current authenticated user from Supabase Auth to the local database.
        
        This should be used in FastAPI dependencies to ensure the local user is in sync
        with Supabase Auth.
        """
        from app.core.security import get_current_user_id
        
        # Get the current user ID from the JWT token
        user_id = await get_current_user_id(request)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        
        # Sync the user
        return await self.sync_user_from_supabase(user_id)

# Create a global instance for easy dependency injection
async def get_user_sync_service(db: AsyncSession) -> UserSyncService:
    return UserSyncService(db)
