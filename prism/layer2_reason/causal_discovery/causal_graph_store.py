"""T011 - Causal graph store: JSON persistence and query interface."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)

GRAPHS_DIR = Path(__file__).parent.parent / "graphs"


class CausalGraphStore:
    """Persist and query causal graphs as JSON-serialized networkx DiGraphs."""

    def __init__(self, graphs_dir: str | Path = GRAPHS_DIR) -> None:
        self.graphs_dir = Path(graphs_dir)
        self.graphs_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, nx.DiGraph] = {}

    def save_graph(self, disease: str, graph: nx.DiGraph) -> Path:
        """Serialize and save a causal graph for a disease cohort."""
        path = self.graphs_dir / f"pcmci_{disease}_graph.json"
        data = json_graph.node_link_data(graph)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self._cache[disease] = graph
        logger.info("Saved %s causal graph to %s (%d nodes, %d edges)",
                    disease, path, graph.number_of_nodes(), graph.number_of_edges())
        return path

    def load_graph(self, disease: str) -> nx.DiGraph:
        """Load a causal graph for a disease cohort from JSON."""
        if disease in self._cache:
            return self._cache[disease]
        path = self.graphs_dir / f"pcmci_{disease}_graph.json"
        if not path.exists():
            # Try alternate naming (FCI)
            path = self.graphs_dir / f"fci_{disease}_graph.json"
        if not path.exists():
            raise FileNotFoundError(
                f"No causal graph found for disease '{disease}' in {self.graphs_dir}"
            )
        with open(path) as f:
            data = json.load(f)
        graph = json_graph.node_link_graph(data, directed=True)
        self._cache[disease] = graph
        logger.info("Loaded %s causal graph (%d nodes, %d edges)",
                    disease, graph.number_of_nodes(), graph.number_of_edges())
        return graph

    def get_parents(self, disease: str, node: str) -> List[str]:
        """Return causal parents of a node in the disease graph."""
        G = self.load_graph(disease)
        if node not in G:
            return []
        return list(G.predecessors(node))

    def get_causal_path(self, disease: str, source: str, target: str) -> List[List[str]]:
        """Return all directed paths from source to target."""
        G = self.load_graph(disease)
        try:
            paths = list(nx.all_simple_paths(G, source, target, cutoff=6))
            return paths
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def export_dot(self, disease: str) -> str:
        """Export a causal graph as a Graphviz DOT string."""
        G = self.load_graph(disease)
        lines = [f'digraph {disease} {{']
        lines.append('  rankdir=LR;')
        for node in G.nodes():
            lines.append(f'  "{node}";')
        for u, v, data in G.edges(data=True):
            corr = data.get("correlation", 0.0)
            lag = data.get("lag_hours", 0)
            label = f"r={corr:.2f} lag={lag}h"
            lines.append(f'  "{u}" -> "{v}" [label="{label}"];')
        lines.append("}")
        return "\n".join(lines)

    def list_available(self) -> List[str]:
        """List disease names for which graphs are stored."""
        diseases = set()
        for p in self.graphs_dir.glob("*_graph.json"):
            name = p.stem  # e.g. pcmci_tb_graph
            parts = name.split("_")
            if len(parts) >= 2:
                diseases.add(parts[1])
        return sorted(diseases)
