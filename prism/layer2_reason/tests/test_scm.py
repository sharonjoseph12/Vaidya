"""T026 - Tests for SCM pipeline (US1)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from layer2_reason.scm.causal_attribution import compute_causal_attribution
from layer2_reason.scm.intervention_engine import estimate_intervention_effect
from layer2_reason.scm.scm_builder import SCMBuilder, fit_disease_scms
from layer2_reason.scm.scm_pipeline import PRISMSCMPipeline


@pytest.fixture
def synthetic_scm_data() -> pd.DataFrame:
    """X → Y → Z"""
    rng = np.random.default_rng(42)
    n = 200
    X = rng.normal(0, 1, n)
    Y = 2.0 * X + rng.normal(0, 0.1, n)
    Z = -1.5 * Y + rng.normal(0, 0.1, n)
    
    df = pd.DataFrame({"X": X, "Y": Y, "Z": Z})
    df["disease_label"] = "test"
    df["patient_id"] = "P1"
    df["time_hours"] = 1.0
    return df


@pytest.fixture
def test_graph() -> nx.DiGraph:
    G = nx.DiGraph()
    G.add_edge("X", "Y")
    G.add_edge("Y", "Z")
    return G


class TestSCMBuilder:
    def test_fit_and_predict(self, synthetic_scm_data, test_graph):
        builder = SCMBuilder(mode="debug")
        builder.fit(synthetic_scm_data, test_graph, feature_cols=["X", "Y", "Z"])
        
        # Test X → Y
        # Since Y = 2.0 * X, predict_node("Y", {"X": 1.0}) should be ~2.0
        y_pred = builder.predict_node("Y", {"X": 1.0})
        assert pytest.approx(y_pred, rel=0.1) == 2.0
        
        # R2 should be high
        assert builder.r2_scores["Y"] > 0.9

    def test_save_load(self, synthetic_scm_data, test_graph):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            fit_disease_scms(synthetic_scm_data, {"test": test_graph}, out_dir, mode="debug")
            
            assert (out_dir / "test_scm.pkl").exists()
            
            loaded = SCMBuilder.load(out_dir / "test_scm.pkl")
            assert "Y" in loaded.node_models


class TestInterventionEngine:
    def test_estimate_intervention_effect(self, synthetic_scm_data, test_graph):
        # We want to intervene on X to change Z
        # Z = -1.5 * Y = -1.5 * (2.0 * X) = -3.0 * X
        # If X is 0.0, Z is 0.0
        # If do(X=1.0), Z should be -3.0
        
        from networkx.readwrite import json_graph
        # Mock dot graph for DoWhy
        dot = 'digraph { "X" -> "Y"; "Y" -> "Z"; }'
        
        patient = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        
        res = estimate_intervention_effect(
            patient_data=patient,
            treatment_var="X",
            treatment_value=1.0,
            outcome_var="Z",
            disease="test",
            graph_dot=dot,
            reference_data=synthetic_scm_data,
        )
        
        assert res.treatment_var == "X"
        assert res.outcome_var == "Z"
        assert res.is_identifiable is True
        
        # ATE of do(X=1) vs X=0 is -3.0. Baseline=0.0 → Intervened=-3.0
        # Absolute reduction = baseline - intervened = 0.0 - (-3.0) = +3.0
        assert pytest.approx(res.absolute_reduction, rel=0.1) == 3.0


class TestCausalAttribution:
    def test_compute_causal_attribution(self, synthetic_scm_data, test_graph):
        dot = 'digraph { "X" -> "Y"; "Y" -> "Z"; }'
        patient = {"X": 2.0, "Y": 4.0, "Z": -6.0}
        
        att = compute_causal_attribution(
            patient_data=patient,
            disease="test",
            outcome_var="Z",
            causal_graph=test_graph,
            graph_dot=dot,
            reference_data=synthetic_scm_data,
        )
        
        # Parent of Z is Y. So Y should be the top (and only) cause.
        assert att.top_cause == "Y"
        assert pytest.approx(att.top_cause_weight) == 1.0
        assert att.attributions["Y"] == 1.0


class TestNarrativeDeterminism:
    def test_narrative_is_deterministic(self):
        from layer2_reason.counterfactuals.explainer import PRISMExplainer
        from layer2_reason.scm.intervention_engine import _empty_intervention
        explainer = PRISMExplainer()
        
        iv = _empty_intervention("nutrition_score", 10.0, "tb_prob")
        iv.absolute_reduction = 0.20
        iv.relative_reduction_pct = 40.0
        
        s1 = explainer.build_plain_language_narrative(
            disease="tb",
            prob=0.50,
            attributions={"nutrition_score": 0.8},
            top_intervention=iv
        )
        s2 = explainer.build_plain_language_narrative(
            disease="tb",
            prob=0.50,
            attributions={"nutrition_score": 0.8},
            top_intervention=iv
        )
        
        assert s1 == s2
        assert "Tuberculosis probability: 50%." in s1
        assert "nutritional status" in s1


class TestUncertaintyReducer:
    def test_recommend_diagnostic_test(self):
        from layer2_reason.scm.uncertainty_reducer import recommend_diagnostic_test
        test_tb = recommend_diagnostic_test("tb", {"prob": 0.5})
        assert test_tb == "cbnaat_sputum" # highest info gain / sqrt(cost)
        
        test_unknown = recommend_diagnostic_test("unknown", {})
        assert test_unknown == "clinical_review"
