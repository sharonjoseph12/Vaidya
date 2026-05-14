"""T036 - Integration test for Layer 2 output feeding into Layer 3."""
from __future__ import annotations

import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from layer2_reason.causal_engine import PRISMCausalEngine
from layer2_reason.causal_discovery.causal_graph_store import CausalGraphStore
from layer2_reason.scm.scm_builder import fit_disease_scms


@pytest.fixture
def test_env():
    """Sets up a temporary directory with a mock TB graph and SCM."""
    tmp = tempfile.TemporaryDirectory()
    base_dir = Path(tmp.name)
    graphs_dir = base_dir / "graphs"
    models_dir = base_dir / "scm_models"
    
    rng = np.random.default_rng(42)
    n = 100
    nutrition = rng.normal(5, 2, n)
    # malnutrition lowers immunity -> increases tb_susceptibility
    tb_susc = -0.8 * nutrition + rng.normal(0, 0.5, n)
    
    df = pd.DataFrame({"nutrition_score": nutrition, "tb_susceptibility": tb_susc})
    df["disease_label"] = "tb"
    df["patient_id"] = "P1"
    df["time_hours"] = 1.0
    
    G = nx.DiGraph()
    G.add_edge("nutrition_score", "tb_susceptibility")
    
    store = CausalGraphStore(graphs_dir)
    store.save_graph("tb", G)
    fit_disease_scms(df, {"tb": G}, models_dir, mode="debug")
    
    # Save panel for DoWhy background
    df.to_pickle(base_dir / "panel.pkl")
    
    yield base_dir, base_dir / "panel.pkl"
    tmp.cleanup()


def test_layer2_to_layer3_forcing_function(test_env):
    """Test that Layer 2 intervention outputs can be correctly extracted as ODE forcing functions."""
    base_dir, panel_path = test_env
    
    engine = PRISMCausalEngine(
        disease="tb",
        graphs_dir=base_dir / "graphs",
        models_dir=base_dir / "scm_models"
    )
    engine.scm_pipeline.load_reference_data("tb", panel_path)
    
    patient = {"nutrition_score": 2.0, "tb_susceptibility": 4.0}
    
    # Run full analysis
    report = engine.full_causal_analysis(patient, disease_probability=0.85)
    
    assert report.disease == "tb"
    assert len(report.top_interventions) > 0
    
    # The top intervention should be nutrition (since it's in the TB catalog)
    interventions_for_l3 = [iv.to_ode_forcing_fn() for iv in report.top_interventions]
    
    # Find nutrition
    nut_forcing = next((iv for iv in interventions_for_l3 if iv["treatment_var"] == "nutrition_score"), None)
    assert nut_forcing is not None
    
    # Validate contract format
    assert "effect_magnitude" in nut_forcing
    assert "onset_delay_days" in nut_forcing
    assert "duration_days" in nut_forcing
    
    # We expect positive reduction
    assert nut_forcing["effect_magnitude"] > 0
