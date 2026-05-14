"""T051 - Integration test between Layer 1 feature vector and Layer 2 CausalEngine."""
from __future__ import annotations

import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from layer2_reason.causal_engine import PRISMCausalEngine
from layer2_reason.causal_discovery.causal_graph_store import CausalGraphStore
from layer2_reason.scm.scm_builder import fit_disease_scms


def test_layer1_layer2_integration():
    """Simulate Layer 1 output and feed it to PRISMCausalEngine."""
    with tempfile.TemporaryDirectory() as tmp:
        base_dir = Path(tmp)
        graphs_dir = base_dir / "graphs"
        models_dir = base_dir / "scm_models"
        
        # 1. Setup mock models
        rng = np.random.default_rng(42)
        n = 100
        wbc = rng.normal(10.0, 2.0, n)
        tb_susc = 0.5 * wbc + rng.normal(0, 1.0, n)
        
        df = pd.DataFrame({"wbc": wbc, "tb_susceptibility": tb_susc})
        df["disease_label"] = "tb"
        df["patient_id"] = "P1"
        df["time_hours"] = 1.0
        
        G = nx.DiGraph()
        G.add_edge("wbc", "tb_susceptibility")
        
        store = CausalGraphStore(graphs_dir)
        store.save_graph("tb", G)
        fit_disease_scms(df, {"tb": G}, models_dir, mode="debug")
        df.to_pickle(base_dir / "panel.pkl")
        
        # 2. Layer 1 feature vector simulation
        # Contains many extra features that should be filtered or ignored
        l1_features = {
            "wbc": 12.0,
            "hemoglobin": 10.5,
            "temperature": 38.5,
            "nutrition_score": 5.0,
            "unrelated_feature": 100.0
        }
        
        # Modality available mask (from multimodal data completeness)
        modality_avail = {
            "vitals": True,
            "labs": True,
            "socioeconomic": True
        }
        
        engine = PRISMCausalEngine(
            disease="tb",
            graphs_dir=graphs_dir,
            models_dir=models_dir
        )
        engine.scm_pipeline.load_reference_data("tb", base_dir / "panel.pkl")
        
        # 3. Execution
        report = engine.full_causal_analysis(
            patient_features=l1_features,
            disease_probability=0.75,
            modality_available=modality_avail
        )
        
        # 4. Assertions
        assert report.disease == "tb"
        assert report.probability == 0.75
        assert report.processing_time_ms < 250.0  # Should be very fast
        
        # Unrelated feature should not be the top cause
        assert "unrelated_feature" not in report.causal_attributions.attributions
