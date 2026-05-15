"""
Download scan audio/video from Supabase Storage into temp files for local inference.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def download_scan_files(
    session_id: str,
    audio_storage_path: Optional[str],
    video_storage_path: Optional[str],
) -> Tuple[Optional[str], Optional[str], str]:
    """
    Download artifacts to a temp directory.

    Returns:
        (local_audio_path, local_video_path, temp_dir) — caller must ``shutil.rmtree(temp_dir)``.
    """
    from backend.db.supabase_client import get_supabase_client

    tmp = tempfile.mkdtemp(prefix=f"prism_scan_{session_id}_")
    client = get_supabase_client()
    bucket = client.storage.from_("scan-media")

    local_audio: Optional[str] = None
    local_video: Optional[str] = None

    for label, storage_path, default_ext in (
        ("video", video_storage_path, ".webm"),
        ("audio", audio_storage_path, ".webm"),
    ):
        if not storage_path:
            continue
        try:
            raw = bucket.download(storage_path)
            data = raw if isinstance(raw, (bytes, bytearray)) else bytes(raw)
            if not data:
                logger.warning("Empty %s bytes for %s", label, storage_path)
                continue
            ext = Path(storage_path).suffix or default_ext
            out_path = str(Path(tmp) / f"{label}{ext}")
            Path(out_path).write_bytes(data)
            if label == "video":
                local_video = out_path
            else:
                local_audio = out_path
        except Exception as e:
            logger.warning("%s download failed (%s): %s", label, storage_path, e)

    return local_audio, local_video, tmp
