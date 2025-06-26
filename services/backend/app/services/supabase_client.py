"""
Supabase client initialization and management.
"""
from typing import Optional
import os

from supabase import create_client, Client as SupabaseClient
from app.core.config import settings

# Global Supabase client instance
_supabase: Optional[SupabaseClient] = None

def get_supabase_client() -> SupabaseClient:
    """
    Get or create a Supabase client instance.
    
    Returns:
        SupabaseClient: Initialized Supabase client
        
    Raises:
        RuntimeError: If Supabase URL or key is not configured
    """
    global _supabase
    
    if _supabase is None:
        supabase_url = settings.SUPABASE_URL
        supabase_key = settings.SUPABASE_KEY
        
        if not supabase_url or not supabase_key:
            raise RuntimeError(
                "Supabase URL and key must be configured. "
                "Please set SUPABASE_URL and SUPABASE_KEY environment variables."
            )
            
        _supabase = create_client(supabase_url, supabase_key)
    
    return _supabase


def get_supabase_admin() -> SupabaseClient:
    """
    Get a Supabase client with admin privileges.
    
    Returns:
        SupabaseClient: Supabase client with admin privileges
        
    Raises:
        RuntimeError: If Supabase service role key is not configured
    """
    service_role_key = settings.SUPABASE_SERVICE_ROLE_KEY
    
    if not service_role_key:
        raise RuntimeError(
            "Supabase service role key is required for admin operations. "
            "Please set SUPABASE_SERVICE_ROLE_KEY environment variable."
        )
    
    return create_client(settings.SUPABASE_URL, service_role_key)
