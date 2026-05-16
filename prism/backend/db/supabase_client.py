"""
PRISM Platform — Supabase Client Singleton
Provides a configured Supabase client for all database operations.
"""

from functools import lru_cache
from typing import Any
import logging
from uuid import UUID

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
        if "placeholder" in settings.supabase_url.lower():
            raise ValueError("Placeholder URL detected, forcing mock fallback")
        client = create_client( # type: ignore
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
        logger.info("Supabase client initialized for %s", settings.supabase_url)
        return client
    except Exception as e:
        from backend.db import mock_supabase_persist as _msp

        logger.warning("Supabase initialization failed, using mock client: %s", e)
        logger.warning(
            "Supabase mock is active; row data is synced via %s (set PRISM_MOCK_DB_JSON to override).",
            _msp.mock_db_json_path(),
        )
        # In-memory object storage (bucket -> path -> bytes) for scan-media downloads in dev
        mock_storage_state: dict[str, dict[str, bytes]] = {}

        class MockStorageBucket:
            def __init__(self, bucket_name: str):
                self._bucket = bucket_name

            def upload(self, path: str, file: bytes | bytearray, file_options: dict | None = None):
                data = bytes(file) if not isinstance(file, bytes) else file
                mock_storage_state.setdefault(self._bucket, {})[path] = data
                return {"path": path}

            def download(self, path: str) -> bytes:
                return mock_storage_state.get(self._bucket, {}).get(path, b"")

        class MockStorageRoot:
            def from_(self, bucket: str):
                return MockStorageBucket(bucket)

        class MockTable:
            def __init__(self, name: str):
                self.name = name
                self._filters: list[tuple[str, str]] = []
                self.insert_data: dict | None = None
                self.update_data: dict | None = None
                self._range: tuple[int, int] | None = None
                self._order: tuple[str, bool] | None = None
                self._limit: int | None = None
                self._count_mode: str | None = None

            def select(self, *args, **kwargs):
                self._count_mode = kwargs.get("count")
                return self

            def order(self, column: str, desc: bool = False, *args, **kwargs):
                self._order = (column, desc)
                return self

            def limit(self, n: int, *args, **kwargs):
                self._limit = n
                return self

            def range(self, start: int, end: int, *args, **kwargs):
                self._range = (start, end)
                return self

            def single(self, *args, **kwargs):
                return self

            def eq(self, column: str, value, *args, **kwargs):
                self._filters.append((column, str(value)))
                return self

            def insert(self, data, *args, **kwargs):
                self.insert_data = dict(data)
                return self

            def update(self, data, *args, **kwargs):
                self.update_data = dict(data)
                return self

            def _row_matches_filter(self, row: dict, col: str, val: str) -> bool:
                rv, fv = row.get(col), val
                if rv is None:
                    return False
                if col == "id" or col == "patient_id" or col.endswith("_id"):
                    try:
                        return UUID(str(rv)) == UUID(str(fv))
                    except ValueError:
                        pass
                return str(rv) == str(fv)

            def _filtered_rows(self, mock_tables: dict[str, dict[str, dict]]) -> list[dict]:
                rows = list(mock_tables.get(self.name, {}).values())
                for col, val in self._filters:
                    rows = [r for r in rows if self._row_matches_filter(r, col, val)]
                return rows

            def execute(self, *args, **kwargs):
                from backend.db.mock_supabase_persist import mock_db_transaction
                from datetime import datetime, timezone
                import uuid as uuid_mod

                with mock_db_transaction() as mock_tables:

                    class MockResponse:
                        def __init__(self, data: list, count: int | None = None):
                            self.data = data
                            self.count = count if count is not None else len(data)

                    if self.insert_data is not None:
                        row = dict(self.insert_data)
                        if "id" not in row:
                            row["id"] = str(uuid_mod.uuid4())
                        row.setdefault(
                            "created_at",
                            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                        )
                        tbl = mock_tables.setdefault(self.name, {})
                        tbl[str(row["id"])] = row
                        return MockResponse([row])

                    if self.update_data is not None:
                        rows = self._filtered_rows(mock_tables)
                        if len(rows) == 1:
                            rows[0].update(self.update_data)
                            return MockResponse([rows[0]])
                        return MockResponse([])

                    rows = self._filtered_rows(mock_tables)
                    if self._order:
                        col, desc = self._order

                        def sort_key(r: dict):
                            v = r.get(col)
                            if isinstance(v, (int, float)):
                                return v
                            return str(v) if v is not None else ""

                        rows = sorted(rows, key=sort_key, reverse=desc)

                    total = len(rows)
                    if self._range is not None:
                        lo, hi = self._range
                        rows = rows[lo : hi + 1]
                    if self._limit is not None:
                        rows = rows[: self._limit]

                    count_out = total if self._count_mode == "exact" else len(rows)
                    return MockResponse(rows, count=count_out)

        class MockClient:
            def __init__(self):
                self.storage = MockStorageRoot()

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
