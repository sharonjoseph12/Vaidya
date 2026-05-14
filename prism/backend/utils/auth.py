"""
PRISM Platform — JWT Authentication Middleware
Validates Supabase Auth JWT tokens for protected endpoints.
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Validate JWT token from Supabase Auth and extract user info.

    Returns:
        Dict with user_id, email, and role from the JWT payload.

    Raises:
        HTTPException 401 if token is invalid or expired.
    """
    token = credentials.credentials

    try:
        from backend.config import get_settings
        settings = get_settings()

        # Supabase JWT uses the anon key as the secret for HS256
        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
            )

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
        }

    except JWTError as e:
        logger.warning("JWT validation failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(
    request: Request,
) -> dict | None:
    """
    Optionally extract user from JWT. Returns None if no token present.
    Used for endpoints that work both authenticated and unauthenticated.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        token = auth_header.split(" ")[1]
        from backend.config import get_settings
        settings = get_settings()

        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_aud": False},
        )
        return {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
        }
    except (JWTError, IndexError):
        return None
