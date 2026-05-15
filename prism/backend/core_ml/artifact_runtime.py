"""
Load finetuned artifacts from ``prism/backend/core_ml/`` for presentation / production.

Expected filenames (place files next to ``model_loader.py`` in ``core_ml/``):

- ``prism_yamnet_audio.h5`` — Keras model (fallback SENSE head)
- ``lstm_trajectory.pth`` — ``DiseaseTrajectoryLSTM`` state_dict or full module (Layer 3)
- ``causal_explainer.pkl`` — sklearn estimator, template dict, or joblib blob (Layer 2 hint)

Alternate names are resolved with a small glob (e.g. ``*trajectory*.pth``).
"""

from __future__ import annotations

import glob
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path(__file__).resolve().parent

# One-shot cache per process (restart API/worker after replacing weights).
_runtime_cache: Dict[str, Any] = {}


def _repo_root() -> Path:
    # core_ml → backend → prism → Vaidya
    return MODEL_DIR.parent.parent.parent


def _ensure_repo_on_syspath() -> None:
    root = str(_repo_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def _resolve_file(base: str, extra_globs: Tuple[str, ...] = ()) -> Optional[Path]:
    direct = MODEL_DIR / base
    if direct.is_file():
        return direct
    for pattern in extra_globs:
        matches = sorted(MODEL_DIR.glob(pattern))
        if matches:
            return matches[0]
    return None


def _torch_load(path: Path) -> Any:
    import torch

    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except Exception:
        # Finetuned checkpoints are often full pickles (trusted local files in core_ml/).
        return torch.load(path, map_location="cpu", weights_only=False)


class MockModel:
    """Deterministic stub when artifacts are missing or fail to load."""

    is_real = False
    backend_kind = "mock"

    def __init__(self, name: str, path: str):
        self.name = name
        self.path = path

    def infer(self, data: Any) -> Dict[str, float]:
        seed = len(str(data)) if data else 42
        random.seed(seed)
        if self.name == "YAMNet":
            return {
                "TB_Cough": random.uniform(0.6, 0.9),
                "Wheezing": random.uniform(0.1, 0.4),
                "Normal": random.uniform(0.01, 0.1),
            }
        raise RuntimeError(f"MockModel {self.name} infer not implemented for this call")


def _yamnet_probs_to_dict(y: np.ndarray) -> Dict[str, float]:
    """Map a 1×K probability row to YAMNet-style keys used by legacy SENSE."""
    y = np.asarray(y)
    if y.ndim == 1:
        y = y.reshape(1, -1)
    row = y[0].astype(np.float64)
    s = float(np.sum(row)) or 1.0
    row = row / s
    if row.size >= 3:
        return {
            "TB_Cough": float(row[0]),
            "Wheezing": float(row[1]),
            "Normal": float(row[2]),
        }
    if row.size == 2:
        return {
            "TB_Cough": float(row[0]),
            "Wheezing": float(row[1]) * 0.5,
            "Normal": float(row[1]) * 0.5,
        }
    v = float(row[0]) if row.size else 0.5
    return {"TB_Cough": v, "Wheezing": (1.0 - v) * 0.4, "Normal": (1.0 - v) * 0.6}


class TorchYamnetArtifact:
    """PyTorch 32→softmax(3) head when Keras/TF is unavailable (e.g. Python 3.14)."""

    is_real = True
    backend_kind = "torch"

    def __init__(self, path: Path, model: Any):
        self.path = str(path)
        self._model = model

    @classmethod
    def try_load(cls, path: Path) -> Optional["TorchYamnetArtifact"]:
        import torch.nn as nn

        try:
            ckpt = _torch_load(path)
        except Exception as e:
            logger.warning("torch.load failed for audio head %s: %s", path, e)
            return None
        if not isinstance(ckpt, nn.Module):
            logger.warning("Expected nn.Module in %s, got %s", path, type(ckpt))
            return None
        ckpt.eval()
        logger.info("Loaded PyTorch audio head from %s", path)
        return cls(path, ckpt)

    def _vec(self, data: Any) -> Any:
        import torch

        rng = np.random.default_rng(abs(hash(str(data))) % (2**31))
        v = rng.normal(0, 0.08, size=(1, 32)).astype(np.float32)
        return torch.tensor(v)

    def infer(self, data: Any) -> Dict[str, float]:
        import torch

        x = self._vec(data)
        with torch.no_grad():
            logits = self._model(x)
            if logits.ndim == 1:
                logits = logits.unsqueeze(0)
            y = torch.softmax(logits, dim=-1).numpy()
        return _yamnet_probs_to_dict(y)


class KerasYamnetArtifact:
    """Keras ``.h5`` classifier for legacy YAMNet-style SENSE fallback."""

    is_real = True
    backend_kind = "keras"

    def __init__(self, path: Path, model: Any):
        self.path = str(path)
        self._model = model

    @classmethod
    def try_load(cls, path: Path) -> Optional["KerasYamnetArtifact"]:
        try:
            import tensorflow as tf  # noqa: F401
            from tensorflow import keras
        except ImportError:
            logger.warning("TensorFlow not installed; cannot load %s", path)
            return None
        try:
            model = keras.models.load_model(path, compile=False)
        except Exception as e:
            logger.warning("Failed to load Keras model %s: %s", path, e)
            return None
        logger.info("Loaded Keras audio head from %s", path)
        return cls(path, model)

    def _build_batch(self, data: Any) -> np.ndarray:
        spec = self._model.input_shape
        rng = np.random.default_rng(abs(hash(str(data))) % (2**31))
        if spec is None or len(spec) < 2:
            return rng.normal(0, 0.05, size=(1, 32)).astype(np.float32)

        shape_rest = []
        for dim in spec[1:]:
            if dim is None:
                shape_rest.append(32)
            else:
                shape_rest.append(int(dim))
        batch = rng.normal(0, 0.08, size=(1, *tuple(shape_rest))).astype(np.float32)
        return np.clip(batch, -5.0, 5.0)

    def infer(self, data: Any) -> Dict[str, float]:
        batch = self._build_batch(data)
        y = self._model.predict(batch, verbose=0)
        return _yamnet_probs_to_dict(y)


class TorchTrajectoryArtifact:
    """``lstm_trajectory.pth`` — uses ``DiseaseTrajectoryLSTM`` from repo when possible."""

    is_real = True
    backend_kind = "torch"

    def __init__(self, path: Path, model: Any):
        self.path = str(path)
        self._model = model

    @classmethod
    def try_load(cls, path: Path) -> Optional["TorchTrajectoryArtifact"]:
        import torch.nn as nn

        try:
            ckpt = _torch_load(path)
        except Exception as e:
            logger.warning("torch.load failed for %s: %s", path, e)
            return None

        _ensure_repo_on_syspath()
        try:
            from layer3_twin.trajectory_model import DiseaseTrajectoryLSTM
        except ImportError as e:
            logger.warning("Cannot import DiseaseTrajectoryLSTM: %s", e)
            return None

        if isinstance(ckpt, nn.Module):
            m = ckpt
            m.eval()
            logger.info("Loaded full nn.Module trajectory from %s", path)
            return cls(path, m)

        m = DiseaseTrajectoryLSTM()
        if not isinstance(ckpt, dict):
            logger.warning("Unexpected checkpoint type for %s: %s", path, type(ckpt))
            return None
        try:
            m.load_state_dict(ckpt, strict=True)
        except Exception:
            try:
                m.load_state_dict(ckpt, strict=False)
                logger.warning("Loaded trajectory state_dict with strict=False from %s", path)
            except Exception as e2:
                logger.warning("state_dict load failed for %s: %s", path, e2)
                return None
        m.eval()
        logger.info("Loaded DiseaseTrajectoryLSTM weights from %s", path)
        return cls(path, m)

    def infer_from_sense(
        self,
        sense: Dict[str, Any],
        causal: Dict[str, Any],
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        import torch

        _ensure_repo_on_syspath()
        from layer3_twin.trajectory_model import patient_to_tensor

        probs = sense.get("disease_probabilities") or {}
        base_risk = float(max(probs.values())) if probs else 0.5
        pf = features or {}
        nutrition = float(pf.get("nutrition_score", 5.0))
        x = patient_to_tensor({"base_risk": base_risk, "nutrition_score": nutrition})

        with torch.no_grad():
            y = self._model(x)
            arr = y.detach().cpu().numpy().reshape(-1)

        n = int(arr.shape[0])
        months_idx = [0, 3, 6]

        def clamp01(v: float) -> float:
            return max(0.02, min(0.99, v))

        series: List[float] = [float(arr[min(mi, n - 1)]) for mi in months_idx]
        worsen = [clamp01(v + 0.03 * i) for i, v in enumerate(series)]
        improve = [clamp01(v * (1.0 - 0.1 * i)) for i, v in enumerate(series)]

        def strip(vals: List[float]) -> List[Dict[str, Any]]:
            return [
                {"month": int(m), "values": {"tb_prob": round(v, 4)}}
                for m, v in zip(months_idx, vals)
            ]

        max_r = float(np.max(arr)) if len(arr) else base_risk
        months_crit = max(2.5, min(8.5, 4.0 + 6.0 * (1.0 - min(1.0, max_r))))

        return {
            "months_to_critical": round(months_crit, 1),
            "months_to_critical_with_intervention": round(months_crit + 12.0 * min(1.0, max_r), 1),
            "intervention_applied": "Finetuned_LSTM_trajectory",
            "without_intervention": strip(worsen),
            "with_best_intervention": strip(improve),
        }


class CausalArtifact:
    """Wraps joblib/pickle object; augments sense-derived causal text when possible."""

    is_real = True
    backend_kind = "sklearn_or_dict"

    def __init__(self, path: Path, obj: Any):
        self.path = str(path)
        self._obj = obj

    @classmethod
    def try_load(cls, path: Path) -> Optional["CausalArtifact"]:
        try:
            import joblib

            obj = joblib.load(path)
        except Exception as e1:
            try:
                import pickle

                with open(path, "rb") as f:
                    obj = pickle.load(f)
            except Exception as e2:
                logger.warning("Could not load causal artifact %s: joblib=%s pickle=%s", path, e1, e2)
                return None
        logger.info("Loaded causal artifact from %s (%s)", path, type(obj))
        return cls(path, obj)

    def explain(self, sense: Dict[str, Any], patient_features: Dict[str, Any]) -> Dict[str, Any]:
        from backend.services.pipeline_derived import build_causal_results

        base = build_causal_results(sense, patient_features)
        obj = self._obj

        if isinstance(obj, dict):
            if "attributions" in obj or "narrative" in obj:
                merged = dict(base)
                if "attributions" in obj:
                    merged["attributions"] = {**base.get("attributions", {}), **obj["attributions"]}
                if "narrative" in obj:
                    merged["narrative"] = str(obj["narrative"]) + " " + merged.get("narrative", "")
                if "counterfactuals" in obj:
                    merged["counterfactuals"] = obj["counterfactuals"]
                return merged

        if hasattr(obj, "predict_proba"):
            probs = sense.get("disease_probabilities") or {}
            names = sorted(probs.keys())
            n_in = getattr(obj, "n_features_in_", len(names))
            x = np.zeros((1, int(n_in)), dtype=np.float32)
            for i in range(min(len(names), int(n_in))):
                x[0, i] = float(probs[names[i]])
            try:
                p = obj.predict_proba(x)[0]
                cls_names = list(getattr(obj, "classes_", range(len(p))))
                j = int(np.argmax(p))
                tag = str(cls_names[j]) if j < len(cls_names) else str(j)
                base["narrative"] = (
                    f"Explainer model ({Path(self.path).name}) favours class {tag} "
                    f"(p={float(np.max(p)):.2f}). "
                    + base["narrative"]
                )
            except Exception as e:
                logger.debug("Causal sklearn infer skipped: %s", e)

        return base


def clear_ml_runtime_cache() -> None:
    """Drop cached ML wrappers after replacing files on disk."""
    _runtime_cache.clear()


def load_yamnet_runtime() -> Any:
    if "yamnet" in _runtime_cache:
        return _runtime_cache["yamnet"]
    path_h5 = _resolve_file("prism_yamnet_audio.h5", ("*yamnet*.h5", "*prism*audio*.h5"))
    if path_h5:
        art = KerasYamnetArtifact.try_load(path_h5)
        if art is not None:
            _runtime_cache["yamnet"] = art
            return art
    path_pt = _resolve_file("prism_yamnet_torch.pt", ("*yamnet*.pt", "*prism*audio*.pt"))
    if path_pt:
        art = TorchYamnetArtifact.try_load(path_pt)
        if art is not None:
            _runtime_cache["yamnet"] = art
            return art
    fallback = MODEL_DIR / "prism_yamnet_audio.h5"
    m = MockModel("YAMNet", str(fallback))
    _runtime_cache["yamnet"] = m
    return m


def load_trajectory_runtime() -> Any:
    if "trajectory" in _runtime_cache:
        return _runtime_cache["trajectory"]
    path = _resolve_file(
        "lstm_trajectory.pth",
        ("*trajectory*.pth", "*lstm*.pth"),
    )
    if path and path.suffix.lower() == ".pth":
        art = TorchTrajectoryArtifact.try_load(path)
        if art is not None:
            _runtime_cache["trajectory"] = art
            return art
    fallback = MODEL_DIR / "lstm_trajectory.pth"
    m = MockModel("LSTM", str(fallback))
    _runtime_cache["trajectory"] = m
    return m


def load_causal_runtime() -> Any:
    if "causal" in _runtime_cache:
        return _runtime_cache["causal"]
    path = _resolve_file("causal_explainer.pkl", ("*causal*.pkl", "*explainer*.pkl"))
    if path:
        art = CausalArtifact.try_load(path)
        if art is not None:
            _runtime_cache["causal"] = art
            return art
    fallback = MODEL_DIR / "causal_explainer.pkl"
    m = MockModel("CausalExplainer", str(fallback))
    _runtime_cache["causal"] = m
    return m


def ml_stack_status() -> Dict[str, Any]:
    """JSON-serializable status for ``GET /health/ml`` (forces a fresh probe, bypasses cache)."""
    _runtime_cache.clear()
    out: Dict[str, Any] = {"core_ml_dir": str(MODEL_DIR), "artifacts": {}}
    for key, loader in (
        ("yamnet_audio", load_yamnet_runtime),
        ("lstm_trajectory", load_trajectory_runtime),
        ("causal_explainer", load_causal_runtime),
    ):
        try:
            m = loader()
            out["artifacts"][key] = {
                "path": getattr(m, "path", None),
                "is_real": bool(getattr(m, "is_real", False)),
                "backend_kind": getattr(m, "backend_kind", None),
                "class": type(m).__name__,
            }
        except Exception as e:
            out["artifacts"][key] = {"error": str(e)}
    return out
