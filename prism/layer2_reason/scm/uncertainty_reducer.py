"""T038 - Uncertainty Reducer: recommend cost-effective diagnostic tests."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Mock mapping of diagnostic tests to their costs (INR) and information gain potential
DIAGNOSTIC_TESTS = {
    "cbnaat_sputum": {"cost": 2500, "info_gain": 0.8},
    "chest_xray": {"cost": 500, "info_gain": 0.4},
    "esr": {"cost": 150, "info_gain": 0.2},
    "peripheral_smear": {"cost": 100, "info_gain": 0.3},
    "dengue_ns1": {"cost": 600, "info_gain": 0.9},
    "ecg": {"cost": 300, "info_gain": 0.5},
    "lipid_profile": {"cost": 800, "info_gain": 0.6},
    "hba1c": {"cost": 500, "info_gain": 0.7},
}

DISEASE_TESTS = {
    "tb": ["cbnaat_sputum", "chest_xray", "esr"],
    "anemia": ["peripheral_smear"],
    "dengue": ["dengue_ns1"],
    "heart_failure": ["ecg", "lipid_profile"],
}


def recommend_diagnostic_test(
    disease: str,
    uncertainty_set: Dict[str, float],
    available_tests: Optional[List[str]] = None,
) -> str:
    """Recommend the most cost-effective diagnostic test to reduce uncertainty.

    Parameters
    ----------
    disease : The disease context.
    uncertainty_set : Current probability distribution / belief.
    available_tests : Tests available at the nearest facility.

    Returns
    -------
    Test ID string
    """
    tests = available_tests or DISEASE_TESTS.get(disease, [])
    if not tests:
        return "clinical_review"

    best_test = None
    best_score = -1.0

    for test in tests:
        meta = DIAGNOSTIC_TESTS.get(test)
        if not meta:
            continue
        
        # Simplified expected information gain per unit cost
        # score = InfoGain / log(Cost + 10)
        # Avoid zero division and massive cost penalty
        score = meta["info_gain"] / (meta["cost"] ** 0.5)
        
        if score > best_score:
            best_score = score
            best_test = test

    return best_test or "clinical_review"
