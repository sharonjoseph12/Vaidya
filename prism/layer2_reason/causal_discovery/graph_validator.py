"""T012 - Graph validator: medical knowledge validation of causal graphs."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import networkx as nx

logger = logging.getLogger(__name__)

REQUIRED_EDGES: List[Tuple[str, str]] = [
    ("malnutrition", "tb_susceptibility"),
    ("hemoglobin", "fatigue"),
    ("wbc", "infection_marker"),
    ("temperature", "infection_marker"),
]

FORBIDDEN_EDGES: List[Tuple[str, str]] = [
    ("tb_susceptibility", "malnutrition"),
    ("fatigue", "hemoglobin"),
]


def validate_graph(
    graph: nx.DiGraph,
    disease: str,
    output_dir: str | Path | None = None,
) -> Dict:
    """Validate a discovered causal graph against medical knowledge.

    Parameters
    ----------
    graph : discovered causal graph (networkx DiGraph or general graph)
    disease : disease cohort name (for logging / output)
    output_dir : if provided, save validation_report.json there

    Returns
    -------
    Dict with keys 'checks', 'warnings', 'overall_pass'
    """
    report: Dict = {
        "disease": disease,
        "checks": {},
        "warnings": [],
        "overall_pass": True,
    }

    # 1. DAG check (warn only — PAG may have bidirected edges)
    if nx.is_directed_acyclic_graph(graph):
        report["checks"]["acyclicity"] = "PASS"
    else:
        msg = f"{disease}: discovered graph has cycles (may be PAG with bidirected edges)"
        report["checks"]["acyclicity"] = "WARN"
        report["warnings"].append(msg)
        logger.warning(msg)

    # 2. Required edges
    missing_required = []
    for src, dst in REQUIRED_EDGES:
        if src in graph.nodes and dst in graph.nodes:
            if not graph.has_edge(src, dst):
                missing_required.append((src, dst))
    if missing_required:
        report["checks"]["required_edges"] = "WARN"
        report["warnings"].append(f"Missing required edges: {missing_required}")
        logger.warning("Missing required edges for %s: %s", disease, missing_required)
    else:
        report["checks"]["required_edges"] = "PASS"

    # 3. Forbidden edges
    present_forbidden = []
    for src, dst in FORBIDDEN_EDGES:
        if graph.has_edge(src, dst):
            present_forbidden.append((src, dst))
    if present_forbidden:
        report["checks"]["forbidden_edges"] = "FAIL"
        report["overall_pass"] = False
        msg = f"Forbidden edges present in {disease} graph: {present_forbidden}"
        report["warnings"].append(msg)
        logger.error(msg)
    else:
        report["checks"]["forbidden_edges"] = "PASS"

    # 4. Connectivity: disease nodes reachable from ≥2 biomarkers
    disease_nodes = [n for n in graph.nodes if "susceptibility" in n or "disease" in n or disease in n]
    connectivity_ok = True
    for dn in disease_nodes:
        reachable_from = [
            n for n in graph.nodes
            if n != dn and nx.has_path(graph, n, dn)
        ]
        if len(reachable_from) < 2:
            connectivity_ok = False
            report["warnings"].append(
                f"Disease node '{dn}' reachable from only {len(reachable_from)} nodes"
            )
    report["checks"]["connectivity"] = "PASS" if connectivity_ok else "WARN"

    # Summary
    report["n_nodes"] = graph.number_of_nodes()
    report["n_edges"] = graph.number_of_edges()

    if output_dir is not None:
        out_path = Path(output_dir) / f"validation_{disease}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info("Saved validation report to %s", out_path)

    status = "PASSED" if report["overall_pass"] else "FAILED"
    logger.info("Graph validation %s for %s | warnings=%d", status, disease, len(report["warnings"]))
    return report


def merge_graphs(pcmci_graph: nx.DiGraph, fci_graph: nx.DiGraph) -> nx.DiGraph:
    """Merge PCMCI and FCI graphs; mark edge confidence levels."""
    merged = nx.DiGraph()
    merged.add_nodes_from(pcmci_graph.nodes(data=True))
    merged.add_nodes_from(fci_graph.nodes(data=True))

    # PCMCI edges
    for u, v, data in pcmci_graph.edges(data=True):
        merged.add_edge(u, v, **data, source="pcmci", confidence="high")

    # FCI edges
    for u, v, data in fci_graph.edges(data=True):
        if merged.has_edge(u, v):
            merged[u][v]["confidence"] = "high"
            merged[u][v]["fci_confirmed"] = True
        else:
            edge_type = data.get("edge_type", "possible_direct")
            conf = "medium" if edge_type == "direct" else "uncertain"
            merged.add_edge(u, v, **data, source="fci", confidence=conf)

    logger.info("Merged graph: %d nodes, %d edges", merged.number_of_nodes(), merged.number_of_edges())
    return merged
