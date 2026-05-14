"""T015 - Discovery pipeline: orchestrates PCMCI + FCI → merge → validate → store."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import networkx as nx
import pandas as pd

from layer2_reason.causal_discovery.causal_graph_store import CausalGraphStore
from layer2_reason.causal_discovery.graph_validator import merge_graphs, validate_graph

logger = logging.getLogger(__name__)

BIOMARKERS = [
    "hemoglobin", "wbc", "creatinine", "temperature", "heart_rate",
    "spo2", "respiratory_rate", "sbp", "glucose", "crp",
    "bilirubin_total", "platelet",
]

DEFAULT_DISEASE_COHORTS = ["tb", "anemia", "heart_failure", "general"]


def run_discovery_pipeline(
    panel_path: str | Path,
    nfhs_path: Optional[str | Path],
    graphs_dir: str | Path,
    diseases: List[str] = DEFAULT_DISEASE_COHORTS,
    tau_max: int = 20,
    validate: bool = True,
) -> Dict[str, nx.DiGraph]:
    """Full causal discovery pipeline.

    1. Load panel dataset
    2. Run PCMCI per disease cohort
    3. Run FCI on NFHS data (if provided)
    4. Merge PCMCI + FCI graphs
    5. Validate each graph
    6. Store validated graphs

    Returns
    -------
    Dict[disease → merged causal graph]
    """
    graphs_dir = Path(graphs_dir)
    store = CausalGraphStore(graphs_dir)

    # --- Load panel ---
    with open(panel_path, "rb") as f:
        panel: pd.DataFrame = pickle.load(f)
    logger.info("Loaded panel: %d rows, %d patients",
                len(panel), panel["patient_id"].nunique() if "patient_id" in panel.columns else -1)

    # --- PCMCI per cohort ---
    from layer2_reason.causal_discovery.pcmci_discoverer import run_pcmci_per_cohort
    pcmci_graphs = run_pcmci_per_cohort(
        panel=panel,
        var_names=BIOMARKERS,
        disease_cohorts=[d for d in diseases if d != "general"],
        graphs_dir=graphs_dir,
        tau_max=tau_max,
    )

    # --- FCI on NFHS (optional) ---
    fci_graph: Optional[nx.DiGraph] = None
    if nfhs_path is not None and Path(nfhs_path).exists():
        try:
            from layer2_reason.causal_discovery.fci_discoverer import run_fci
            with open(nfhs_path, "rb") as f:
                nfhs_df = pickle.load(f)
            fci_graph = run_fci(nfhs_df, graphs_dir=graphs_dir)
            logger.info("FCI graph computed: %d edges", fci_graph.number_of_edges())
        except Exception as exc:
            logger.warning("FCI discovery failed (non-fatal): %s", exc)

    # --- Merge + validate + store ---
    final_graphs: Dict[str, nx.DiGraph] = {}
    for disease, pcmci_g in pcmci_graphs.items():
        if fci_graph is not None:
            merged = merge_graphs(pcmci_g, fci_graph)
        else:
            merged = pcmci_g

        if validate:
            report = validate_graph(merged, disease, output_dir=graphs_dir)
            if not report["overall_pass"]:
                logger.error("Graph validation FAILED for %s — storing anyway with warnings", disease)

        store.save_graph(disease, merged)
        final_graphs[disease] = merged

    logger.info("Discovery pipeline complete | graphs=%d", len(final_graphs))
    return final_graphs
