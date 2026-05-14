"""T004 - Shared pytest fixtures for Layer 2 tests (no MIMIC dependency)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
import networkx as nx
from dataclasses import dataclass
from typing import Dict, List


# ---------------------------------------------------------------------------
# Biomarker constants
# ---------------------------------------------------------------------------
BIOMARKERS = [
    "hemoglobin", "wbc", "creatinine", "temperature", "heart_rate",
    "spo2", "respiratory_rate", "sbp", "glucose", "crp",
    "bilirubin_total", "platelet",
]

NORMAL_RANGES = {
    "hemoglobin": (12.0, 16.0),
    "wbc": (4.0, 11.0),
    "creatinine": (0.6, 1.2),
    "temperature": (36.5, 37.5),
    "heart_rate": (60, 100),
    "spo2": (95, 100),
    "respiratory_rate": (12, 20),
    "sbp": (100, 140),
    "glucose": (70, 140),
    "crp": (0.0, 5.0),
    "bilirubin_total": (0.2, 1.2),
    "platelet": (150, 400),
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def synthetic_patient_timeseries() -> List[Dict]:
    """50 synthetic patients with 48h biomarker timeseries."""
    rng = np.random.default_rng(42)
    patients = []
    diseases = ["tb"] * 15 + ["anemia"] * 15 + ["heart_failure"] * 10 + ["healthy"] * 10
    for i, disease in enumerate(diseases):
        n_timepoints = rng.integers(48, 120)
        times = np.sort(rng.uniform(0, n_timepoints, n_timepoints))
        data = {"time_hours": times}
        for bm in BIOMARKERS:
            lo, hi = NORMAL_RANGES[bm]
            vals = rng.uniform(lo * 0.7, hi * 1.3, n_timepoints)
            # Disease-specific perturbation
            if disease == "anemia" and bm == "hemoglobin":
                vals = rng.uniform(5.0, 9.0, n_timepoints)
            if disease == "tb" and bm == "wbc":
                vals = rng.uniform(12.0, 25.0, n_timepoints)
            data[bm] = vals
        df = pd.DataFrame(data)
        patients.append({
            "patient_id": f"P{i:04d}",
            "timeseries": df,
            "labels": [disease] if disease != "healthy" else [],
            "disease_names": [disease] if disease != "healthy" else [],
            "demographics": {
                "age": float(rng.integers(18, 80)),
                "sex_binary": float(rng.integers(0, 2)),
                "bmi": float(rng.uniform(16.0, 35.0)),
                "admission_weight": float(rng.uniform(40.0, 100.0)),
            },
        })
    return patients


@pytest.fixture
def synthetic_panel_dataset(synthetic_patient_timeseries) -> pd.DataFrame:
    """Flat panel dataset (all patients × timepoints, all biomarkers)."""
    rows = []
    for p in synthetic_patient_timeseries:
        df = p["timeseries"].copy()
        df["patient_id"] = p["patient_id"]
        df["disease_label"] = p["disease_names"][0] if p["disease_names"] else "healthy"
        rows.append(df)
    panel = pd.concat(rows, ignore_index=True)
    return panel


@pytest.fixture
def simple_causal_graph() -> nx.DiGraph:
    """Known 3-node DAG: nutrition → hemoglobin → fatigue."""
    G = nx.DiGraph()
    G.add_edge("nutrition", "hemoglobin", lag_hours=24, correlation=0.65, p_value=0.001,
               edge_type="direct", confidence="high")
    G.add_edge("hemoglobin", "fatigue", lag_hours=12, correlation=0.55, p_value=0.003,
               edge_type="direct", confidence="high")
    return G


@pytest.fixture
def tb_causal_graph() -> nx.DiGraph:
    """Synthetic TB causal graph with known structure."""
    G = nx.DiGraph()
    edges = [
        ("malnutrition", "tb_susceptibility", 0.62),
        ("poor_ventilation", "tb_susceptibility", 0.41),
        ("tb_susceptibility", "wbc", 0.55),
        ("tb_susceptibility", "crp", 0.70),
        ("wbc", "temperature", 0.38),
    ]
    for src, dst, corr in edges:
        G.add_edge(src, dst, lag_hours=24, correlation=corr,
                   p_value=0.01, edge_type="direct", confidence="high")
    return G


@pytest.fixture
def synthetic_patient_features() -> Dict:
    """Layer 1 feature vector for a high-TB-risk patient."""
    return {
        # rPPG
        "heart_rate": 98.0, "spo2": 94.0, "hrv_rmssd": 28.0,
        "hrv_sdnn": 35.0, "lf_hf_ratio": 3.2, "respiratory_rate": 22.0,
        "rppg_confidence": 0.85,
        # Audio
        "cough_tb_prob": 0.74, "cough_pneumonia_prob": 0.12,
        "cough_covid_prob": 0.05, "cough_asthma_prob": 0.04,
        "cough_copd_prob": 0.03, "breathing_rate_audio": 21.0,
        "ie_ratio": 1.8, "wheeze_severity": 1.0, "crackle_severity": 0.0,
        "jitter_local": 0.8, "shimmer_local": 2.1, "hnr": 18.5,
        # Visual
        "jaundice_index": 0.05, "conjunctival_pallor": 0.55,
        "cyanosis_score": 0.08, "dengue_flush_score": 0.10,
        "skin_pallor_pct": 30.0, "visual_confidence": 0.78,
        # IMU
        "gait_symmetry": 0.88, "cadence": 105.0,
        "stride_variability": 0.12, "imu_confidence": 0.90,
        # Demographics
        "age": 32.0, "sex_binary": 1.0, "bmi": 16.5,
        "wealth_index": 2.0, "urban_rural": 0.0,
        "crowding_index": 3.8, "nutrition_score": 2.5,
        "smoking_status": 0.0, "water_quality": 2.0,
    }


@pytest.fixture
def modality_available() -> Dict:
    return {"rppg": True, "audio": True, "visual": True, "imu": True}
