"""T013 - Temporal causal discovery using PCMCI (Mocked for Demo)."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

import networkx as nx
import pandas as pd

logger = logging.getLogger(__name__)

# Hardcoded realistic graph to avoid hours of PCMCI compute during demo
DEMO_CAUSAL_GRAPH = {
    "TB": {
        "malnutrition": 0.38,
        "poor_ventilation": 0.24, 
        "prior_infection": 0.21,
        "bmi_low": 0.17
    }
}

def run_pcmci(
    dataframe: pd.DataFrame, 
    var_names: List[str], 
    tau_max: int = 20, 
    pc_alpha: float = 0.05
) -> nx.DiGraph:
    """Mocked PCMCI: returns a hardcoded graph structure to avoid hours of compute."""
    logger.info("Bypassing PCMCI compute. Using hardcoded DEMO_CAUSAL_GRAPH.")
    G = nx.DiGraph()
    for disease, causes in DEMO_CAUSAL_GRAPH.items():
        # Ensure we connect to a standard outcome node for MVP
        target = "tb_susceptibility" if disease == "TB" else f"{disease.lower()}_susceptibility"
        for cause, weight in causes.items():
            G.add_edge(cause, target, weight=weight)
    return G

def build_causal_graph(pcmci_output: Any) -> nx.DiGraph:
    """Returns the pre-built mock graph."""
    if isinstance(pcmci_output, nx.DiGraph):
        return pcmci_output
    return nx.DiGraph()
