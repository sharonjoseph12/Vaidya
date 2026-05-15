"""
Execute the real Layer 1 PRISMSensePipeline (rPPG + audio + visual + fusion).

Maps ``SenseResult`` into the JSON shape stored on ``diagnostic_sessions`` and
consumed by the frontend (aligned with legacy mock keys where possible).
"""

from __future__ import annotations

import logging
import numbers
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _workspace_root() -> Path:
    # prism/backend/services/real_sense.py → parents[3] = repo root (Vaidya)
    return Path(__file__).resolve().parents[3]


def _ensure_repo_on_syspath() -> None:
    root = str(_workspace_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def _json_safe(obj: Any) -> Any:
    """Convert numpy scalars / nested structures to JSON-serializable values."""
    if obj is None:
        return None
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, (str, int, float)):
        return obj
    if isinstance(obj, numbers.Integral):
        return int(obj)
    if isinstance(obj, numbers.Real):
        return float(obj)
    if hasattr(obj, "item") and callable(obj.item):
        try:
            return _json_safe(obj.item())
        except Exception:
            return str(obj)
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    return str(obj)


def sense_result_to_api_dict(sense: Any, had_video: bool, had_audio: bool) -> dict[str, Any]:
    """Flatten ``SenseResult`` for API / DB JSON columns."""
    raw = sense.to_dict()
    raw = _json_safe(raw)

    mean_std = getattr(sense, "uncertainty", {}) or {}
    uncertainty_intervals: dict[str, list[float]] = {}
    for name, pair in mean_std.items():
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            m, s = float(pair[0]), float(pair[1])
            uncertainty_intervals[str(name)] = [max(0.0, m - s), min(1.0, m + s)]

    visual = raw.get("visual") or {}
    cb = visual.get("color_biomarkers") or {}
    cs = visual.get("classifier_scores") or {}

    visual_flat = {
        "jaundice_score": float(cb.get("jaundice_score", 0) or 0),
        "pallor_score": float(cb.get("pallor_score", 0) or 0),
        "cyanosis_score": float(cb.get("cyanosis_score", 0) or 0),
        "dengue_flush_score": float(cb.get("dengue_flush_score", 0) or 0),
        "anemia_score": float(cs.get("anemia", 0) or 0),
    }

    audio = raw.get("audio") or {}
    if isinstance(audio, dict) and "cough_count" not in audio:
        audio["cough_count"] = 1 if audio.get("cough_detected") else 0

    disease_probs = sense.disease_probabilities if hasattr(sense, "disease_probabilities") else {}

    modalities: list[str] = []
    if had_video:
        modalities.extend(["rppg", "visual"])
    if had_audio:
        modalities.append("audio")

    return {
        "disease_probabilities": raw.get("disease_probabilities") or disease_probs,
        "rppg": raw.get("rppg") or {},
        "audio": audio,
        "visual": visual_flat,
        "uncertainty": uncertainty_intervals or _fallback_uncertainty(raw.get("disease_probabilities") or {}),
        "modalities_available": modalities,
        "processing_time_ms": int(raw.get("processing_time_ms", 0) or 0),
    }


def _fallback_uncertainty(probs: dict[str, Any]) -> dict[str, list[float]]:
    out: dict[str, list[float]] = {}
    for k, v in probs.items():
        try:
            p = float(v)
            margin = min(0.1, p * 0.15 + 0.02)
            out[str(k)] = [max(0.0, p - margin), min(1.0, p + margin)]
        except (TypeError, ValueError):
            continue
    return out


def run_real_sense(local_video: str | None, local_audio: str | None) -> dict[str, Any]:
    _ensure_repo_on_syspath()
    from layer1_sense.sense_pipeline import PRISMSensePipeline

    if not local_video and not local_audio:
        raise ValueError("Real SENSE requires at least one of video or audio on disk")

    pipeline = PRISMSensePipeline(fps=30, sample_rate=16000)
    sense = pipeline.run(video_path=local_video, audio_path=local_audio)
    return sense_result_to_api_dict(sense, bool(local_video), bool(local_audio))


def try_run_real_sense(local_video: str | None, local_audio: str | None) -> dict[str, Any] | None:
    try:
        return run_real_sense(local_video, local_audio)
    except Exception as e:
        logger.exception("Real SENSE pipeline failed: %s", e)
        return None
