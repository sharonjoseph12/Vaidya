"""
Layer 1 SENSE readiness — detect whether real multimodal pipeline can start.

Used by ``GET /health/sense`` so operators know if scans will use
``PRISMSensePipeline`` or fall back to legacy mock sensing.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    # prism/backend/services/sense_health.py → parents[3] = Vaidya
    return Path(__file__).resolve().parents[3]


def sense_pipeline_readiness() -> dict[str, Any]:
    """Return JSON-serializable readiness flags (no auth; safe for probes)."""
    out: dict[str, Any] = {
        "python_version": platform.python_version(),
        "mediapipe_installed": False,
        "mediapipe_version": None,
        "mediapipe_solutions_api": False,
        "repo_on_syspath": False,
        "pipeline_constructible": False,
        "error": None,
    }

    try:
        import mediapipe as mp

        out["mediapipe_installed"] = True
        out["mediapipe_version"] = getattr(mp, "__version__", None)
        sol = getattr(mp, "solutions", None)
        out["mediapipe_solutions_api"] = sol is not None
    except ImportError as e:
        out["error"] = f"mediapipe import failed: {e}"
        return out

    if not out["mediapipe_solutions_api"]:
        out["error"] = (
            "MediaPipe classic `solutions` API missing (common on unsupported Python "
            "or minimal wheels). Use Python 3.11–3.12 and install mediapipe per repo "
            "requirements.txt."
        )
        return out

    root = str(_repo_root())
    if root not in sys.path:
        sys.path.insert(0, root)
    out["repo_on_syspath"] = root in sys.path

    try:
        from layer1_sense.sense_pipeline import PRISMSensePipeline

        _ = PRISMSensePipeline(fps=30, sample_rate=16000)
        out["pipeline_constructible"] = True
    except Exception as e:
        out["error"] = str(e)

    return out
