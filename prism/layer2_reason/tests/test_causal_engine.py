"""T027 - Performance and integration tests for PRISMCausalEngine."""
from __future__ import annotations

import tempfile
import time
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from layer2_reason.causal_engine import PRISMCausalEngine
from layer2_reason.causal_discovery.causal_graph_store import CausalGraphStore
from layer2_reason.scm.scm_builder import fit_disease_scms


@pytest.fixture
def mock_engine_env():
    """Sets up a temporary directory with a mock graph and SCM."""
    tmp = tempfile.TemporaryDirectory()
    base_dir = Path(tmp.name)
    graphs_dir = base_dir / "graphs"
    models_dir = base_dir / "scm_models"
    
    # 1. Create a synthetic SCM structure X -> Y -> Z
    rng = np.random.default_rng(42)
    n = 200
    X = rng.normal(0, 1, n)
    Y = 2.0 * X + rng.normal(0, 0.1, n)
    Z = -1.5 * Y + rng.normal(0, 0.1, n)
    
    df = pd.DataFrame({"X": X, "Y": Y, "Z": Z})
    df["disease_label"] = "test_synthetic"
    df["patient_id"] = "P1"
    df["time_hours"] = 1.0
    
    G = nx.DiGraph()
    G.add_edge("X", "Y")
    G.add_edge("Y", "Z")
    
    # 2. Save graph
    store = CausalGraphStore(graphs_dir)
    store.save_graph("test_synthetic", G)
    
    # 3. Fit and save SCM
    fit_disease_scms(df, {"test_synthetic": G}, models_dir, mode="debug")
    
    yield base_dir, df
    tmp.cleanup()


class TestCausalEnginePerformance:

    def test_full_causal_analysis_latency(self, mock_engine_env):
        base_dir, ref_data = mock_engine_env
        
        # Initialize engine
        engine = PRISMCausalEngine(
            disease="test_synthetic",
            graphs_dir=base_dir / "graphs",
            models_dir=base_dir / "scm_models"
        )
        
        # Inject reference data for the test
        panel_path = base_dir / "panel.pkl"
        ref_data.to_pickle(panel_path)
        engine.scm_pipeline.load_reference_data("test_synthetic", panel_path)
        
        # Warmup
        patient = {"X": 1.0, "Y": 2.0, "Z": -3.0}
        engine.full_causal_analysis(patient, 0.8)
        
        # Run 100 iterations
        times = []
        for i in range(100):
            # slightly vary input
            pt = {"X": 1.0 + (i/100), "Y": 2.0, "Z": -3.0}
            
            start_t = time.perf_counter()
            report = engine.full_causal_analysis(pt, 0.8)
            t_ms = (time.perf_counter() - start_t) * 1000
            
            times.append(t_ms)
            
            assert report.disease == "test_synthetic"
            assert report.processing_time_ms > 0
            
        mean_t = np.mean(times)
        p95_t = np.percentile(times, 95)
        
        # Goal is < 200ms. Since Python DoWhy can be slow, 
        # this test asserts that caching keeps average < 200ms.
        assert mean_t < 200.0, f"Mean latency {mean_t:.2f}ms exceeds 200ms budget"
        
        print(f"\nPerformance: Mean={mean_t:.2f}ms, P95={p95_t:.2f}ms")

    def test_missing_data_graceful_degradation(self, mock_engine_env):
        base_dir, ref_data = mock_engine_env
        engine = PRISMCausalEngine(
            disease="test_synthetic",
            graphs_dir=base_dir / "graphs",
            models_dir=base_dir / "scm_models"
        )
        
        # Pass empty dict
        report = engine.full_causal_analysis({}, 0.5)
        
        # Should not crash, just produce empty attribution and warnings
        assert len(report.warnings) > 0
        assert report.causal_attributions.top_cause == "unknown"
