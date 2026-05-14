"""T041 - Federated Learning Graph Updater."""
from __future__ import annotations

import logging
from typing import Any, Dict

import networkx as nx
import numpy as np

from layer2_reason.causal_discovery.graph_validator import validate_graph

logger = logging.getLogger(__name__)


def apply_dp_noise(weight: float, epsilon: float = 1.0) -> float:
    """Apply Laplace noise for differential privacy."""
    # Scale of noise = sensitivity / epsilon
    # Assuming max edge weight change sensitivity is ~0.1
    sensitivity = 0.1
    scale = sensitivity / epsilon
    noise = np.random.laplace(0, scale)
    return weight + noise


def update_causal_graph_from_aggregated_weights(
    current_graph: nx.DiGraph,
    delta_weights: Dict[tuple[str, str], float],
    epsilon: float = 1.0,
    learning_rate: float = 0.1,
) -> nx.DiGraph:
    """
    Update causal graph edges based on FL weight deltas, with DP noise.
    
    If an edge weight drops below a threshold, the edge is removed.
    If the resulting graph violates domain knowledge, the update is rejected.
    """
    new_graph = current_graph.copy()
    
    # 1. Apply DP noise and update weights
    for (u, v), delta in delta_weights.items():
        if not new_graph.has_edge(u, v):
            # For MVP, we only update existing edges, not add new ones from FL
            continue
            
        noisy_delta = apply_dp_noise(delta, epsilon)
        
        # Get current weight (default 0.5 if not set)
        current_w = new_graph[u][v].get("weight", 0.5)
        new_w = current_w + (learning_rate * noisy_delta)
        
        # 2. Prune edges that become too weak
        if abs(new_w) < 0.05:
            new_graph.remove_edge(u, v)
        else:
            new_graph[u][v]["weight"] = new_w

    # 3. Validate against medical knowledge
    report = validate_graph(new_graph)
    if report["forbidden_edges_found"]:
        logger.warning("FL update rejected: introduced forbidden edges.")
        raise ValueError("Federated update violates forbidden edge constraints.")
        
    logger.info("FL update applied successfully. Epsilon budget consumed: %.2f", epsilon)
    return new_graph
