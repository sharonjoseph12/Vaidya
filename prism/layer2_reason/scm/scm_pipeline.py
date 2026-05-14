"""T023 - SCM Pipeline: orchestration for SCM models."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from layer2_reason.scm.causal_attribution import CausalAttributions, compute_causal_attribution
from layer2_reason.scm.intervention_engine import InterventionResult, estimate_intervention_effect
from layer2_reason.scm.scm_builder import SCMBuilder
from layer2_reason.causal_discovery.causal_graph_store import CausalGraphStore
from layer2_reason.scm.intervention_catalog import get_catalog

logger = logging.getLogger(__name__)


class PRISMSCMPipeline:
    """Manages loading and querying SCMs for all diseases."""

    def __init__(self, models_dir: str | Path, graphs_dir: str | Path):
        self.models_dir = Path(models_dir)
        self.graphs_dir = Path(graphs_dir)
        self.store = CausalGraphStore(self.graphs_dir)
        self.scms: Dict[str, SCMBuilder] = {}
        self._reference_data: Dict[str, pd.DataFrame] = {}

    def load_model(self, disease: str) -> None:
        """Load SCM and graph for a specific disease."""
        if disease in self.scms:
            return
        scm_path = self.models_dir / f"{disease}_scm.pkl"
        if not scm_path.exists():
            raise FileNotFoundError(f"SCM model not found: {scm_path}")
        self.scms[disease] = SCMBuilder.load(scm_path)
        logger.info("Loaded SCM for %s", disease)

    def load_reference_data(self, disease: str, panel_path: str | Path) -> None:
        """Load background cohort data for DoWhy adjustments."""
        if disease in self._reference_data:
            return
        # In MVP, we load the full panel and filter
        import pickle
        with open(panel_path, "rb") as f:
            panel = pickle.load(f)
        if "disease_label" in panel.columns:
            self._reference_data[disease] = panel[panel["disease_label"] == disease].copy()
            if len(self._reference_data[disease]) < 10:
                self._reference_data[disease] = panel  # fallback
        else:
            self._reference_data[disease] = panel
        logger.info("Loaded reference data for %s: %d rows", disease, len(self._reference_data[disease]))

    def analyze_patient(
        self,
        patient_features: Dict[str, float],
        disease: str,
        outcome_var: str,
    ) -> Tuple[CausalAttributions, List[InterventionResult]]:
        """Run attribution and intervention analysis for a patient."""
        self.load_model(disease)
        graph = self.store.load_graph(disease)
        graph_dot = self.store.export_dot(disease)

        ref_data = self._reference_data.get(disease)
        if ref_data is None:
            # Create dummy reference if missing (for testing)
            ref_data = pd.DataFrame([patient_features] * 10)

        # 1. Attribution
        attributions = compute_causal_attribution(
            patient_data=patient_features,
            disease=disease,
            outcome_var=outcome_var,
            causal_graph=graph,
            graph_dot=graph_dot,
            reference_data=ref_data,
        )

        # 2. Pre-computed catalog interventions (US3)
        interventions = []
        catalog = get_catalog(disease)
        for opt in catalog:
            res = estimate_intervention_effect(
                patient_data=patient_features,
                treatment_var=opt.treatment_var,
                treatment_value=opt.target_value,
                outcome_var=outcome_var,
                disease=disease,
                graph_dot=graph_dot,
                reference_data=ref_data,
            )
            interventions.append(res)
            
        interventions.sort(key=lambda x: x.absolute_reduction, reverse=True)

        return attributions, interventions
