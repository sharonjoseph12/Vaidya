"""
PRISM Platform — Supabase Client Singleton
Provides a configured Supabase client for all database operations.
"""

from supabase import create_client, Client
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """
    Create and cache a Supabase client instance.
    Uses the service role key for server-side operations (bypasses RLS).
    """
    from backend.config import get_settings
    settings = get_settings()

    client = create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
    logger.info("Supabase client initialized for %s", settings.supabase_url)
    return client


@lru_cache(maxsize=1)
def get_supabase_anon_client() -> Client:
    """
    Create a Supabase client with the anonymous key (for RLS-aware operations).
    Used when operating on behalf of authenticated users.
    """
    from backend.config import get_settings
    settings = get_settings()

    client = create_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_anon_key,
    )
    logger.info("Supabase anon client initialized for %s", settings.supabase_url)
    return client


async def log_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    ip_address: str = None,
    details: dict = None,
) -> None:
    """Append an entry to the audit log (via service role — bypasses RLS)."""
    client = get_supabase_client()
    try:
        client.table("audit_log").insert({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "ip_address": ip_address,
            "details": details,
        }).execute()
    except Exception as e:
        logger.error("Failed to write audit log: %s", e)
