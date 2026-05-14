"""
Integration tests for PRISM Layer 2: Causal Reasoning Engine.
"""

import pytest
import numpy as np
import pandas as pd

from layer2_reason.causal_engine import (
    build_causal_dag,
    generate_synthetic_patients,
    get_causal_attribution,
    causal_analysis,
    CausalReport,
    CAUSAL_EDGES,
    CLINICAL_BOUNDS,
)


# ── DAG structure ──────────────────────────────────────────────────────────

def test_dag_has_all_edges():
    G = build_causal_dag()
    for src, dst in CAUSAL_EDGES:
        assert G.has_edge(src, dst), f"Missing edge {src} -> {dst}"


def test_dag_tb_has_expected_parents():
    G = build_causal_dag()
    parents = set(G.predecessors("TB"))
    assert "immune_suppression" in parents
    assert "poor_ventilation" in parents
    assert "crowding_index" in parents


# ── Synthetic data ─────────────────────────────────────────────────────────

def test_synthetic_data_shape():
    df = generate_synthetic_patients(n=500)
    assert len(df) == 500
    assert "TB" in df.columns
    assert "malnutrition" in df.columns


def test_synthetic_data_bounds():
    df = generate_synthetic_patients()
    for col, (lo, hi) in CLINICAL_BOUNDS.items():
        if col in df.columns:
            assert df[col].min() >= lo - 0.01, f"{col} below lower bound"
            assert df[col].max() <= hi + 0.01, f"{col} above upper bound"


# ── Causal attribution ────────────────────────────────────────────────────

def test_attribution_sums_to_one():
    patient = {"immune_suppression": 0.7, "poor_ventilation": 0.3, "crowding_index": 0.5}
    attr = get_causal_attribution("TB", patient)
    assert abs(sum(attr.values()) - 1.0) < 1e-6


def test_attribution_unknown_disease():
    attr = get_causal_attribution("nonexistent_disease", {"x": 1})
    assert attr == {}


# ── Full causal analysis ──────────────────────────────────────────────────

def test_causal_analysis_returns_report():
    probs = {"TB": 0.65, "COPD": 0.05, "Healthy": 0.30}
    patient = {
        "malnutrition": 0.8,
        "crowding_index": 4.5,
        "bmi": 16.0,
        "smoking": 0,
        "nutrition_score": 3.0,
        "hemoglobin": 9.0,
        "age": 35,
        "ventilation_score": 2.0,
        "immune_suppression": 0.6,
        "poor_ventilation": 0.8,
    }
    report = causal_analysis(probs, patient)

    assert isinstance(report, CausalReport)
    assert report.disease == "TB"
    assert report.probability == 0.65
    assert report.top_intervention in report.attributions
    assert 0.0 <= report.probability_after_intervention <= report.probability
    assert "TB" in report.narrative
    assert "Primary driver" in report.narrative


def test_causal_analysis_narrative_format():
    probs = {"TB": 0.70, "Healthy": 0.30}
    patient = {"immune_suppression": 0.9, "crowding_index": 5.0, "poor_ventilation": 0.7}
    report = causal_analysis(probs, patient)
    # Narrative should mention percentage
    assert "%" in report.narrative
