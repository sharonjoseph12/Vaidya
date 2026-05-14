"""T014 - FCI causal discovery for cross-sectional NFHS data (latent confounders)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import networkx as nx
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NFHS_FEATURES = [
    "nutrition_score", "hemoglobin_gdl", "anemia_binary", "tb_symptom_score",
    "wealth_index", "urban_rural", "water_source", "sanitation_type",
    "crowding_index",
]

# Required background knowledge edges (domain-enforced)
BK_REQUIRED = [
    ("malnutrition", "tb_susceptibility"),
    ("age", "hemoglobin_gdl"),
]


def run_fci(
    nfhs_df: pd.DataFrame,
    features: Optional[list] = None,
    alpha: float = 0.05,
    graphs_dir: str | Path | None = None,
) -> nx.DiGraph:
    """Run FCI algorithm on NFHS cross-sectional data.

    FCI handles latent confounders (PAG output).

    Parameters
    ----------
    nfhs_df : preprocessed NFHS DataFrame
    features : feature columns to use (default: NFHS_FEATURES)
    alpha : significance level for Fisher-Z CI test
    graphs_dir : if provided, save graph JSON here

    Returns
    -------
    nx.DiGraph with edge_type attributes (direct / bidirected / possible_direct)
    """
    try:
        from causallearn.search.ConstraintBased.FCI import fci
        from causallearn.utils.cit import fisherz
    except ImportError as e:
        raise ImportError("causal-learn not installed. Run: pip install causal-learn") from e

    if features is None:
        features = [f for f in NFHS_FEATURES if f in nfhs_df.columns]

    df_clean = nfhs_df[features].dropna()
    if len(df_clean) < 50:
        raise ValueError(f"Too few complete rows for FCI: {len(df_clean)}")

    dataset = df_clean.values.astype(float)
    logger.info("Running FCI | n=%d vars=%d alpha=%.3f", len(dataset), len(features), alpha)

    G_fci, edges = fci(
        dataset=dataset,
        independence_test_method=fisherz,
        alpha=alpha,
        depth=-1,
        max_path_length=4,
        verbose=False,
    )

    # --- Parse PAG to networkx ---
    nx_graph = nx.DiGraph()
    for feat in features:
        nx_graph.add_node(feat)

    # G_fci.graph is an adjacency matrix: 1=tail, 2=arrow, -1=circle
    n = len(features)
    adj = G_fci.graph
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # Arrow into j from i: adj[i,j]=-1 and adj[j,i]=1 (i→j)
            if adj[i, j] == -1 and adj[j, i] == 1:
                nx_graph.add_edge(features[i], features[j],
                                  edge_type="direct", confidence="medium")
            # Bidirected (latent common cause): adj[i,j]=adj[j,i]=-1
            elif adj[i, j] == -1 and adj[j, i] == -1 and not nx_graph.has_edge(features[i], features[j]):
                nx_graph.add_edge(features[i], features[j],
                                  edge_type="bidirected", confidence="uncertain")
            # Possible direct: circle-arrowhead
            elif adj[i, j] == 2 and adj[j, i] == -1 and not nx_graph.has_edge(features[i], features[j]):
                nx_graph.add_edge(features[i], features[j],
                                  edge_type="possible_direct", confidence="uncertain")

    logger.info("FCI graph: %d nodes, %d edges", nx_graph.number_of_nodes(), nx_graph.number_of_edges())

    if graphs_dir is not None:
        from layer2_reason.causal_discovery.causal_graph_store import CausalGraphStore
        store = CausalGraphStore(graphs_dir)
        # Save as fci_nfhs_graph.json
        from networkx.readwrite import json_graph
        import json
        path = Path(graphs_dir) / "fci_nfhs_graph.json"
        with open(path, "w") as f:
            json.dump(json_graph.node_link_data(nx_graph), f, indent=2)
        logger.info("FCI graph saved to %s", path)

    return nx_graph
