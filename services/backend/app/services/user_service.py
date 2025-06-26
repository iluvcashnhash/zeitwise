"""
User service for handling user-related operations.
"""
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
import logging

from fastapi import HTTPException, status, Depends
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.db.session import get_db
from app.models.user import UserInDB, UserCreate, UserUpdate, UserPublic, UserWithToken
from app.services.supabase_auth import supabase_auth_service

logger = logging.getLogger(__name__)

class UserService:
    """Service for user-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_by_id(self, user_id: UUID) -> Optional[UserInDB]:
        """Get a user by ID."""
        # First try to get from Supabase Auth
        try:
            supabase_user = await supabase_auth_service.get_user_by_id(str(user_id))
            if not supabase_user:
                return None
                
            # Then get from local DB
            # TODO: Implement local DB lookup
            # user = self.db.query(User).filter(User.id == user_id).first()
            # if not user:
            #     return None
            # 
            # return UserInDB.from_orm(user)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Get a user by email."""
        try:
            # First try to get from Supabase Auth
            supabase_user = await supabase_auth_service.get_user_by_email(email)
            if not supabase_user:
                return None
                
            # Then get from local DB
            # TODO: Implement local DB lookup
            # user = self.db.query(User).filter(User.email == email).first()
            # if not user:
            #     return None
            #     
            # return UserInDB.from_orm(user)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
    
    async def create(self, user_in: UserCreate) -> UserInDB:
        """Create a new user."""
        try:
            # Check if user already exists
            existing_user = await self.get_by_email(user_in.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Create user in Supabase Auth
            auth_response = await supabase_auth_service.sign_up_with_email_password(
                email=user_in.email,
                password=user_in.password,
                user_metadata={
                    "full_name": user_in.full_name,
                    "avatar_url": user_in.avatar_url,
                    **user_in.metadata_
                }
            )
            
            if not auth_response or "user" not in auth_response:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create user in authentication service"
                )
            
            # Create user in local DB
            # TODO: Implement local DB creation
            # db_user = User(
            #     id=UUID(auth_response["user"]["id"]),
            #     email=user_in.email,
            #     hashed_password=get_password_hash(user_in.password),
            #     full_name=user_in.full_name,
            #     is_active=True,
            #     is_verified=False,
            #     metadata_=user_in.metadata_
            # )
            # self.db.add(db_user)
            # self.db.commit()
            # self.db.refresh(db_user)
            # 
            # return UserInDB.from_orm(db_user)
            
            # For now, return a mock user
            return UserInDB(
                id=UUID(auth_response["user"]["id"]),
                email=user_in.email,
                hashed_password=get_password_hash(user_in.password),
                full_name=user_in.full_name,
                is_active=True,
                is_verified=False,
                metadata_=user_in.metadata_
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            # Try to clean up the auth user if creation failed
            try:
                if 'user' in locals() and 'id' in auth_response.get('user', {}):
                    await supabase_auth_service.delete_user(auth_response["user"]["id"])
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up user after failed creation: {cleanup_error}")
                
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while creating the user"
            )
    
    async def update(
        self, 
        user_id: UUID, 
        user_in: UserUpdate,
        current_user: UserInDB
    ) -> UserInDB:
        """Update a user."""
        try:
            # Check if user exists
            user = await self.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            # Check permissions (users can only update their own profile unless admin)
            if str(user_id) != str(current_user.id) and not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this user"
                )
            
            # Update in Supabase Auth
            update_data = {}
            if user_in.email and user_in.email != user.email:
                update_data["email"] = user_in.email
            if user_in.full_name:
                update_data["user_metadata"] = {"full_name": user_in.full_name}
            
            if update_data:
                await supabase_auth_service.update_user(str(user_id), **update_data)
            
            # Update in local DB
            # TODO: Implement local DB update
            # update_data = user_in.dict(exclude_unset=True, exclude_none=True)
            # if "password" in update_data:
            #     update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            # 
            # for field, value in update_data.items():
            #     setattr(user, field, value)
            # 
            # user.updated_at = datetime.utcnow()
            # self.db.commit()
            # self.db.refresh(user)
            
            # Get updated user
            updated_user = await self.get_by_id(user_id)
            if not updated_user:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to retrieve updated user"
                )
                
            return updated_user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while updating the user"
            )
    
    async def authenticate(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate a user with email and password."""
        try:
            # First try to authenticate with Supabase
            auth_response = await supabase_auth_service.sign_in_with_email_password(
                email=email,
                password=password
            )
            
            if not auth_response or "user" not in auth_response:
                return None
                
            # Get the user from our database
            user = await self.get_by_email(email)
            if not user:
                return None
                
            # Update last login time
            # TODO: Implement last login update in local DB
            # user.last_login_at = datetime.utcnow()
            # self.db.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def delete(self, user_id: UUID, current_user: UserInDB) -> bool:
        """Delete a user."""
        try:
            # Check if user exists
            user = await self.get_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
                
            # Check permissions (users can only delete themselves unless admin)
            if str(user_id) != str(current_user.id) and not current_user.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to delete this user"
                )
            
            # Delete from Supabase Auth
            await supabase_auth_service.delete_user(str(user_id))
            
            # Delete from local DB
            # TODO: Implement local DB deletion
            # self.db.delete(user)
            # self.db.commit()
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while deleting the user"
            )
    
    async def request_password_reset(self, email: str) -> bool:
        """Request a password reset for a user."""
        try:
            return await supabase_auth_service.reset_password_for_email(email)
        except Exception as e:
            logger.error(f"Error requesting password reset: {e}")
            # Don't reveal if the email exists or not
            return True
    
    async def verify_email(self, token: str) -> bool:
        """Verify a user's email using a verification token."""
        try:
            return await supabase_auth_service.verify_email(token)
        except Exception as e:
            logger.error(f"Error verifying email: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

# Dependency to get the current user service
def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)
