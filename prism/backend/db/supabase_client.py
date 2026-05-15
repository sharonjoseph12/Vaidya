"""
PRISM Platform — Supabase Client Singleton
Provides a configured Supabase client for all database operations.
"""

from functools import lru_cache
from typing import Any
import logging

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None # type: ignore
    Client = Any # type: ignore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_supabase_client() -> Any:
    """
    Create and cache a Supabase client instance.
    Uses the service role key for server-side operations (bypasses RLS).
    """
    from backend.config import get_settings
    settings = get_settings()

    try:
        client = create_client( # type: ignore
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
        logger.info("Supabase client initialized for %s", settings.supabase_url)
        return client
    except Exception as e:
        logger.warning("Supabase initialization failed, using mock client: %s", e)
        # Simple mock object to allow the app to run without real Supabase
        import time
        mock_db_state = {}
        
        class MockTable:
            def __init__(self, name):
                self.name = name
                self.current_id = None
                self.insert_data = None
                self.update_data = None

            def select(self, *args, **kwargs): return self
            def order(self, *args, **kwargs): return self
            def limit(self, *args, **kwargs): return self
            def range(self, *args, **kwargs): return self
            def single(self, *args, **kwargs): return self
            
            def eq(self, column, value, *args, **kwargs):
                if column == "id":
                    self.current_id = value
                return self
                
            def insert(self, data, *args, **kwargs):
                self.insert_data = data
                if "id" in data:
                    mock_db_state[data["id"]] = data
                return self
                
            def update(self, data, *args, **kwargs):
                self.update_data = data
                return self
                
            def execute(self, *args, **kwargs):
                class MockResponse:
                    def __init__(self, data):
                        self.data = data
                        self.count = len(data)
                
                # Handle update execution
                if self.update_data and self.current_id and self.current_id in mock_db_state:
                    mock_db_state[self.current_id].update(self.update_data)
                    return MockResponse([mock_db_state[self.current_id]])
                    
                # Handle select execution (list)
                if not self.current_id:
                    items = list(mock_db_state.values())
                    if not items:
                        items = [{
                            "id": "550e8400-e29b-41d4-a716-446655440000", 
                            "name": "Demo Patient", 
                            "status": "active",
                            "created_at": "2026-05-14T00:00:00Z",
                            "consent_given": True,
                            "round_number": 1,
                            "participating_nodes": 5,
                            "dp_epsilon_spent": 0.01
                        }]
                    return MockResponse(items)
                
                # Handle select execution (single)
                if self.current_id and self.current_id in mock_db_state:
                    return MockResponse([mock_db_state[self.current_id]])
                    
                # Default fallback
                return MockResponse([])

        class MockClient:
            def __init__(self):
                self.storage = type('obj', (object,), {'from_': lambda s: type('obj', (object,), {'upload': lambda p, b: True})})()
            def table(self, name):
                return MockTable(name)
        return MockClient()


@lru_cache(maxsize=1)
def get_supabase_anon_client() -> Any:
    """
    Create a Supabase client with the anonymous key (for RLS-aware operations).
    Used when operating on behalf of authenticated users.
    """
    from backend.config import get_settings
    settings = get_settings()

    try:
        client = create_client( # type: ignore
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_anon_key,
        )
        logger.info("Supabase anon client initialized for %s", settings.supabase_url)
        return client
    except Exception as e:
        logger.warning("Supabase anon initialization failed, using mock client: %s", e)
        # Use the same mock as above
        return get_supabase_client()


async def log_audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    ip_address: str | None = None,
    details: dict | None = None,
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
