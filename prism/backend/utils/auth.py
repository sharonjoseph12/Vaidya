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
    """
    token = credentials.credentials

    try:
        from backend.config import get_settings
        settings = get_settings()

        # Development bypass for demo purposes
        token = token.strip()
        env = settings.environment.lower()
        is_dev = env == "development" or settings.debug
        is_mock = token in ["DEMO_TOKEN", "mock-jwt-token"]

        if is_dev and is_mock:
            return {
                "user_id": "00000000-0000-0000-0000-000000000000",
                "email": "demo@prism.health",
                "role": "authenticated",
            }

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
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        token = auth_header.split(" ")[1]
        from backend.config import get_settings
        settings = get_settings()
        env = settings.environment.lower()
        is_dev = env == "development" or settings.debug

        if is_dev and token in ["DEMO_TOKEN", "mock-jwt-token"]:
            return {
                "user_id": "00000000-0000-0000-0000-000000000000",
                "email": "demo@prism.health",
                "role": "authenticated",
            }

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
