"""T019 - Layer 1 → Layer 2 feature vector validator."""
from __future__ import annotations

import logging
import math
from typing import Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class InsufficientFeaturesError(Exception):
    """Raised when a patient feature dict has too few valid values."""


FEATURE_BOUNDS: Dict[str, Tuple[float, float]] = {
    "heart_rate": (20, 300), "spo2": (50, 100), "hrv_rmssd": (1, 300),
    "hrv_sdnn": (1, 200), "lf_hf_ratio": (0.1, 20), "respiratory_rate": (4, 60),
    "rppg_confidence": (0, 1),
    "cough_tb_prob": (0, 1), "cough_pneumonia_prob": (0, 1), "cough_covid_prob": (0, 1),
    "cough_asthma_prob": (0, 1), "cough_copd_prob": (0, 1), "breathing_rate_audio": (4, 60),
    "ie_ratio": (0.2, 8), "wheeze_severity": (0, 3), "crackle_severity": (0, 3),
    "jitter_local": (0, 10), "shimmer_local": (0, 20), "hnr": (-20, 50),
    "jaundice_index": (0, 1), "conjunctival_pallor": (0, 1), "cyanosis_score": (0, 1),
    "dengue_flush_score": (0, 1), "skin_pallor_pct": (0, 100), "visual_confidence": (0, 1),
    "gait_symmetry": (0, 1), "cadence": (20, 200), "stride_variability": (0, 1),
    "imu_confidence": (0, 1),
    "age": (0, 120), "sex_binary": (0, 1), "bmi": (8, 70),
    "wealth_index": (1, 5), "urban_rural": (0, 1), "crowding_index": (0.1, 20),
    "nutrition_score": (0, 10), "smoking_status": (0, 1), "water_quality": (1, 5),
}

MODALITY_CONFIDENCE_KEYS = {
    "rppg": "rppg_confidence",
    "visual": "visual_confidence",
    "imu": "imu_confidence",
}

MODALITY_FEATURES = {
    "rppg": ["heart_rate", "spo2", "hrv_rmssd", "hrv_sdnn", "lf_hf_ratio", "respiratory_rate"],
    "audio": ["cough_tb_prob", "cough_pneumonia_prob", "breathing_rate_audio", "ie_ratio",
              "wheeze_severity", "crackle_severity", "jitter_local", "shimmer_local", "hnr"],
    "visual": ["jaundice_index", "conjunctival_pallor", "cyanosis_score",
               "dengue_flush_score", "skin_pallor_pct"],
    "imu": ["gait_symmetry", "cadence", "stride_variability"],
}

CONFIDENCE_THRESHOLD = 0.4
MIN_VALID_FEATURES = 3
MIN_MODALITIES = 2


def validate_features(
    features: Dict[str, float],
    modality_available: Optional[Dict[str, bool]] = None,
) -> Dict[str, float]:
    """Validate and sanitize a Layer 1 feature vector.

    Parameters
    ----------
    features : raw feature dict from Layer 1
    modality_available : optional dict of {modality: bool}

    Returns
    -------
    Sanitized feature dict (out-of-range → NaN, low-confidence modality → NaN)

    Raises
    ------
    InsufficientFeaturesError
        If fewer than MIN_VALID_FEATURES non-NaN features across MIN_MODALITIES modalities.
    """
    sanitized = dict(features)
    warnings = []

    # 1. Coerce out-of-range values → NaN
    for key, val in sanitized.items():
        if val is None or (isinstance(val, float) and math.isnan(val)):
            sanitized[key] = float("nan")
            continue
        if key in FEATURE_BOUNDS:
            lo, hi = FEATURE_BOUNDS[key]
            if not (lo <= val <= hi):
                warnings.append(f"{key}={val} outside bounds [{lo}, {hi}] → NaN")
                sanitized[key] = float("nan")

    # 2. Low-confidence modality masking
    for modality, conf_key in MODALITY_CONFIDENCE_KEYS.items():
        conf = sanitized.get(conf_key, float("nan"))
        if not math.isnan(conf) and conf < CONFIDENCE_THRESHOLD:
            for feat in MODALITY_FEATURES.get(modality, []):
                if feat in sanitized:
                    warnings.append(f"{feat} masked (confidence={conf:.2f} < {CONFIDENCE_THRESHOLD})")
                    sanitized[feat] = float("nan")

    # 3. Mark unavailable modalities
    if modality_available:
        for modality, available in modality_available.items():
            if not available:
                for feat in MODALITY_FEATURES.get(modality, []):
                    sanitized[feat] = float("nan")

    # 4. Check sufficiency
    valid_per_modality: Dict[str, int] = {}
    for modality, feats in MODALITY_FEATURES.items():
        count = sum(
            1 for f in feats
            if f in sanitized and not (isinstance(sanitized[f], float) and math.isnan(sanitized[f]))
        )
        valid_per_modality[modality] = count

    total_valid = sum(valid_per_modality.values())
    active_modalities = sum(1 for c in valid_per_modality.values() if c > 0)

    if total_valid < MIN_VALID_FEATURES or active_modalities < MIN_MODALITIES:
        raise InsufficientFeaturesError(
            f"Only {total_valid} valid features across {active_modalities} modalities "
            f"(minimum: {MIN_VALID_FEATURES} features, {MIN_MODALITIES} modalities). "
            f"Per-modality counts: {valid_per_modality}"
        )

    for w in warnings:
        logger.warning("Feature validation: %s", w)

    return sanitized
