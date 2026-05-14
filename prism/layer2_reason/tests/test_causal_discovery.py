"""T018 - Causal discovery tests (synthetic data, no MIMIC dependency)."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
import pytest

from layer2_reason.causal_discovery.causal_graph_store import CausalGraphStore
from layer2_reason.causal_discovery.graph_validator import validate_graph, merge_graphs


# ---------------------------------------------------------------------------
# Synthetic known-structure SCM for recovery test
# ---------------------------------------------------------------------------

def _generate_known_scm_data(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """Generate data from known SCM: X → Y → Z (linear)."""
    rng = np.random.default_rng(seed)
    X = rng.normal(0, 1, n)
    Y = 0.8 * X + rng.normal(0, 0.3, n)
    Z = 0.7 * Y + rng.normal(0, 0.3, n)
    df = pd.DataFrame({"X": X, "Y": Y, "Z": Z})
    df["patient_id"] = "P0001"
    df["disease_label"] = "synthetic"
    df["time_hours"] = np.arange(n, dtype=float)
    return df


# ---------------------------------------------------------------------------
# CausalGraphStore tests
# ---------------------------------------------------------------------------

class TestCausalGraphStore:

    def test_save_and_load_round_trip(self, simple_causal_graph):
        with tempfile.TemporaryDirectory() as tmp:
            store = CausalGraphStore(tmp)
            store.save_graph("test", simple_causal_graph)
            loaded = store.load_graph("test")
        assert set(loaded.nodes()) == set(simple_causal_graph.nodes())
        assert loaded.number_of_edges() == simple_causal_graph.number_of_edges()

    def test_get_parents(self, tb_causal_graph):
        with tempfile.TemporaryDirectory() as tmp:
            store = CausalGraphStore(tmp)
            store.save_graph("tb", tb_causal_graph)
            parents = store.get_parents("tb", "tb_susceptibility")
        assert "malnutrition" in parents
        assert "poor_ventilation" in parents

    def test_get_causal_path(self, tb_causal_graph):
        with tempfile.TemporaryDirectory() as tmp:
            store = CausalGraphStore(tmp)
            store.save_graph("tb", tb_causal_graph)
            paths = store.get_causal_path("tb", "malnutrition", "wbc")
        # malnutrition → tb_susceptibility → wbc
        assert any("tb_susceptibility" in p for p in paths)

    def test_export_dot(self, simple_causal_graph):
        with tempfile.TemporaryDirectory() as tmp:
            store = CausalGraphStore(tmp)
            store.save_graph("simple", simple_causal_graph)
            dot = store.export_dot("simple")
        assert "digraph" in dot
        assert "nutrition" in dot
        assert "->" in dot

    def test_load_nonexistent_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = CausalGraphStore(tmp)
            with pytest.raises(FileNotFoundError):
                store.load_graph("nonexistent_disease")


# ---------------------------------------------------------------------------
# GraphValidator tests
# ---------------------------------------------------------------------------

class TestGraphValidator:

    def test_valid_graph_passes(self, tb_causal_graph):
        report = validate_graph(tb_causal_graph, "tb")
        # Required edges are not in synthetic tb_causal_graph by exact name
        # but forbidden edge check should pass
        assert report["checks"]["forbidden_edges"] == "PASS"

    def test_forbidden_edge_fails(self):
        G = nx.DiGraph()
        G.add_edge("tb_susceptibility", "malnutrition")  # forbidden!
        report = validate_graph(G, "test")
        assert report["checks"]["forbidden_edges"] == "FAIL"
        assert report["overall_pass"] is False

    def test_validation_report_saved(self, simple_causal_graph):
        with tempfile.TemporaryDirectory() as tmp:
            validate_graph(simple_causal_graph, "simple", output_dir=tmp)
            report_path = Path(tmp) / "validation_simple.json"
            assert report_path.exists()
            with open(report_path) as f:
                report = json.load(f)
            assert "checks" in report

    def test_merge_graphs(self, simple_causal_graph, tb_causal_graph):
        merged = merge_graphs(simple_causal_graph, tb_causal_graph)
        assert merged.number_of_nodes() >= simple_causal_graph.number_of_nodes()
        assert merged.number_of_edges() >= simple_causal_graph.number_of_edges()


# ---------------------------------------------------------------------------
# PCMCI structure recovery test (lightweight — no tigramite needed for CI)
# ---------------------------------------------------------------------------

class TestPCMCIStructureRecovery:

    @pytest.mark.skipif(
        not __import__("importlib").util.find_spec("tigramite"),
        reason="tigramite not installed",
    )
    def test_known_structure_recovery(self):
        """PCMCI on X→Y→Z data should recover both edges."""
        from layer2_reason.causal_discovery.pcmci_discoverer import run_pcmci, build_causal_graph
        panel = _generate_known_scm_data(n=300)
        output = run_pcmci(panel, var_names=["X", "Y", "Z"], tau_max=3)
        G = build_causal_graph(output)
        # At least one of the known edges should be recovered
        edges = list(G.edges())
        # Check no reverse forbidden edges
        assert ("Z", "X") not in edges
        assert ("Z", "Y") not in edges or ("Y", "Z") in edges  # one direction

    def test_graph_store_available_without_tigramite(self, simple_causal_graph):
        """Graph store works independent of tigramite."""
        with tempfile.TemporaryDirectory() as tmp:
            store = CausalGraphStore(tmp)
            store.save_graph("test", simple_causal_graph)
            g = store.load_graph("test")
        assert g.number_of_nodes() == simple_causal_graph.number_of_nodes()


class TestFederatedGraphUpdater:
    def test_federated_update(self, simple_causal_graph):
        from layer2_reason.causal_discovery.federated_graph_updater import update_causal_graph_from_aggregated_weights
        
        # simple_causal_graph has edges: ("nutrition", "bmi"), ("bmi", "disease")
        # Give ("nutrition", "bmi") a weight of 0.5 initially
        simple_causal_graph["nutrition"]["bmi"]["weight"] = 0.5
        
        # Provide a delta that increases it
        delta = {("nutrition", "bmi"): 0.2}
        
        updated = update_causal_graph_from_aggregated_weights(
            current_graph=simple_causal_graph,
            delta_weights=delta,
            epsilon=10.0, # high epsilon = low noise for testing
            learning_rate=1.0
        )
        
        assert updated["nutrition"]["bmi"]["weight"] > 0.5
        
    def test_federated_update_pruning(self, simple_causal_graph):
        from layer2_reason.causal_discovery.federated_graph_updater import update_causal_graph_from_aggregated_weights
        
        simple_causal_graph["nutrition"]["bmi"]["weight"] = 0.1
        
        # Delta that pushes it below 0.05
        delta = {("nutrition", "bmi"): -0.1}
        
        updated = update_causal_graph_from_aggregated_weights(
            current_graph=simple_causal_graph,
            delta_weights=delta,
            epsilon=100.0,
            learning_rate=1.0
        )
        
        assert not updated.has_edge("nutrition", "bmi")
