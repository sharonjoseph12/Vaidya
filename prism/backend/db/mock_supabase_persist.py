"""
File-backed persistence for the Supabase *mock* client so all uvicorn workers share rows.

Without this, each worker keeps its own in-memory dict and ``POST /patients`` on worker A
followed by ``POST /diagnostics/analyze`` on worker B yields 404 Patient not found.

Set ``PRISM_MOCK_DB_JSON`` to override the JSON path (tests should point at a temp file).
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def mock_db_json_path() -> Path:
    override = os.environ.get("PRISM_MOCK_DB_JSON")
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / ".prism_mock_db.json"


def mock_db_lock_path() -> Path:
    p = mock_db_json_path()
    return p.with_name(p.name + ".lock")


def _normalize_tables(raw: Any) -> dict[str, dict[str, dict]]:
    out: dict[str, dict[str, dict]] = {}
    if not isinstance(raw, dict):
        return out
    for tname, rows in raw.items():
        if not isinstance(rows, dict):
            out[str(tname)] = {}
            continue
        bucket: dict[str, dict] = {}
        for rid, row in rows.items():
            if isinstance(row, dict):
                bucket[str(rid)] = dict(row)
        out[str(tname)] = bucket
    return out


def _load(path: Path) -> dict[str, dict[str, dict]]:
    if not path.is_file():
        return {}
    try:
        return _normalize_tables(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError, TypeError) as exc:
        logger.warning("PRISM mock DB unreadable (%s): %s", path, exc)
        return {}


def _save(path: Path, tables: dict[str, dict[str, dict]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tables, default=str, ensure_ascii=False), encoding="utf-8")


@contextmanager
def mock_db_transaction():
    """
    Load mock tables from disk, yield a mutable dict, then persist it (same lock for the whole op).
    """
    from filelock import FileLock

    path = mock_db_json_path()
    lock_path = mock_db_lock_path()
    lock = FileLock(str(lock_path), timeout=30)
    with lock:
        tables = _load(path)
        try:
            yield tables
        finally:
            _save(path, tables)
