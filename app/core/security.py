"""
Security module for API key authentication
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load API keys from environment
SUPERUSER_API_KEY = os.getenv("fastapi_key_superuser")
USER_API_KEY = os.getenv("fast_api_key_user")

# Validate that API keys are set
if not SUPERUSER_API_KEY or not USER_API_KEY:
    raise ValueError("API keys must be set in environment variables")

# API Key header scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Validate API key from header
    Returns the key if valid, raises HTTPException if not
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        str: Valid API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Include X-API-Key header in your request."
        )
    
    if api_key not in [SUPERUSER_API_KEY, USER_API_KEY]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    
    return api_key


async def require_superuser(api_key: str = Security(get_api_key)) -> str:
    """
    Require superuser API key for write operations
    
    Args:
        api_key: API key validated by get_api_key
        
    Returns:
        str: Valid superuser API key
        
    Raises:
        HTTPException: If API key is not superuser level
    """
    if api_key != SUPERUSER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required. This endpoint requires elevated privileges."
        )
    return api_key


async def require_user_or_superuser(api_key: str = Security(get_api_key)) -> str:
    """
    Require either user or superuser API key (for read operations)
    
    Args:
        api_key: API key validated by get_api_key
        
    Returns:
        str: Valid API key (user or superuser)
        
    Raises:
        HTTPException: If API key is invalid
    """
    # get_api_key already validates that it's one of the two keys
    return api_key
