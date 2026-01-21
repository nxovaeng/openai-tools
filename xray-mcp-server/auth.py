"""
Authentication dependencies for FastAPI.
"""

from fastapi import Security, HTTPException, status, Request
from fastapi.security import APIKeyHeader, HTTPBearer
from typing import Optional

from config import config

# API Key header name
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    api_key: Optional[str] = Security(api_key_header),
    bearer: Optional[str] = Security(bearer_scheme)
) -> str:
    """
    Verify API key from request header.
    
    Supports two authentication methods:
    1. X-API-Key header
    2. Bearer token (Authorization: Bearer <token>)
    
    Args:
        request: FastAPI request object
        api_key: API key from X-API-Key header
        bearer: Bearer token from Authorization header
        
    Returns:
        The valid API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    # Get expected API key
    expected_key = config.ensure_api_key()
    
    # Try X-API-Key header first
    if api_key:
        if api_key == expected_key:
            return api_key
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
    
    # Try Bearer token
    if bearer and bearer.credentials:
        if bearer.credentials == expected_key:
            return bearer.credentials
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Bearer Token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    # No valid authentication provided
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing authentication. Provide X-API-Key header or Bearer token.",
        headers={"WWW-Authenticate": "ApiKey, Bearer"},
    )
