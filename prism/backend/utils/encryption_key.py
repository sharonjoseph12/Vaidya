"""
Normalize and decode ENCRYPTION_KEY (base64) for AES-GCM.

Handles common .env issues: UTF-8 BOM, wrapped lines, stray spaces, missing padding,
and URL-safe base64 variants.
"""

from __future__ import annotations

import base64
import binascii
import re
from pathlib import Path


def backend_dotenv_path() -> Path:
    """``prism/backend/.env`` (this file lives in ``backend/utils/``)."""
    return Path(__file__).resolve().parent.parent / ".env"


def raw_encryption_key_from_backend_env() -> str:
    """
    Prefer ``ENCRYPTION_KEY`` from ``backend/.env`` so crypto matches the file even when
    a stale Windows User/System ``ENCRYPTION_KEY`` is set in the process environment.
    """
    env_file = backend_dotenv_path()
    if env_file.is_file():
        from dotenv import dotenv_values

        m = dotenv_values(env_file, encoding="utf-8-sig")
        k = m.get("ENCRYPTION_KEY") or m.get("encryption_key")
        if k is not None and str(k).strip():
            return str(k).strip()
    from backend.config import get_settings

    return get_settings().encryption_key


def load_aes_key_bytes_from_b64(s: str) -> bytes:
    """
    Parse ENCRYPTION_KEY into raw AES key bytes (16, 24, or 32 bytes).

    Raises ValueError with actionable text (surfaced as HTTP 400) on failure.
    """
    if not s or not isinstance(s, str):
        raise ValueError("ENCRYPTION_KEY is empty.")

    t = s.strip().lstrip("\ufeff")
    t = re.sub(r"\s+", "", t)
    if not t:
        raise ValueError("ENCRYPTION_KEY is empty.")

    pad = (-len(t)) % 4
    padded = t + ("=" * pad)

    raw: bytes | None = None
    try:
        raw = base64.b64decode(padded, validate=True)
    except binascii.Error:
        try:
            raw = base64.urlsafe_b64decode(padded)
        except binascii.Error as exc:
            raise ValueError(
                "ENCRYPTION_KEY must be valid base64 (standard or URL-safe). "
                'Generate: python -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"'
            ) from exc

    if len(raw) not in (16, 24, 32):
        raise ValueError(
            f"ENCRYPTION_KEY must decode to 16, 24, or 32 bytes for AES-GCM (got {len(raw)}). "
            "Use: openssl rand -base64 32"
        )
    return raw


def canonical_encryption_key_b64(s: str) -> str:
    """Return standard base64 (no newlines) for the same key material."""
    return base64.b64encode(load_aes_key_bytes_from_b64(s)).decode("ascii")
