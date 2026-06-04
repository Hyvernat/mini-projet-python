import os
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY = os.getenv("API_KEY", "dev-secret-key")
_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(_header_scheme)) -> str:
    """FastAPI dependency — raises HTTP 403 if the API key is missing or wrong."""
    if key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing API key",
        )
    return key
