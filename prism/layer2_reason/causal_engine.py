"""T025 - PRISMCausalEngine: Main public API for Layer 2."""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from layer2_reason.counterfactuals.explainer import PRISMExplainer
from layer2_reason.counterfactuals.dice_generator import generate_counterfactuals
from layer2_reason.counterfactuals.counterfactual_ranker import rank_counterfactuals
from layer2_reason.data.feature_validator import validate_features
from layer2_reason.scm.causal_attribution import CausalAttributions
from layer2_reason.scm.intervention_engine import InterventionResult
from layer2_reason.scm.intervention_catalog import InterventionOption, get_catalog
from layer2_reason.scm.uncertainty_reducer import recommend_diagnostic_test
from layer2_reason.causal_discovery.federated_graph_updater import update_causal_graph_from_aggregated_weights

logger = logging.getLogger(__name__)


# Placeholder for US2 (DiCE counterfactuals)
@dataclass
class CounterfactualExplanation:
    changes: Dict[str, Tuple[float, float]]
    new_disease_probability: float
    probability_reduction: float
    n_features_changed: int
    feasibility_score: float
    rank: int


@dataclass
class CausalReport:
    """The complete output of the PRISMCausalEngine."""
    disease: str
    probability: float
    confidence_interval: Tuple[float, float]
    causal_attributions: CausalAttributions
    top_interventions: List[InterventionResult]
    counterfactuals: List[CounterfactualExplanation]
    narrative: str
    causal_graph_dot: str
    processing_time_ms: float
    warnings: List[str]


class PRISMCausalEngine:
    """Core public interface for Layer 2: REASON.

    Transforms Layer 1 biomarker probabilities into causal explanations.
    """

    def __init__(
        self,
        disease: str,
        graphs_dir: str | Path = "layer2_reason/graphs/",
        models_dir: str | Path = "layer2_reason/scm_models/",
    ):
        self.disease = disease
        self.graphs_dir = Path(graphs_dir)
        self.models_dir = Path(models_dir)

        # Validate disease string (must exist in models)
        if not (self.models_dir / f"{disease}_scm.pkl").exists() and disease != "test_synthetic":
            logger.warning("No SCM found for '%s', will fallback or raise during analysis", disease)

        self.scm_pipeline = PRISMSCMPipeline(models_dir=self.models_dir, graphs_dir=self.graphs_dir)
        self.explainer = PRISMExplainer()
        
        # Pre-load graph and model for latency
        try:
            self.scm_pipeline.load_model(disease)
            self._graph_dot = self.scm_pipeline.store.export_dot(disease)
        except Exception as e:
            logger.error("Failed to pre-load models for %s: %s", disease, e)
            self._graph_dot = ""

        logger.info("PRISMCausalEngine initialized for %s", disease)

    def full_causal_analysis(
        self,
        patient_features: Dict[str, float],
        disease_probability: float,
        top_k_counterfactuals: int = 3,
        modality_available: Optional[Dict[str, bool]] = None,
    ) -> CausalReport:
        """Run complete causal analysis for a single patient."""
        start_t = time.perf_counter()
        warnings = []

        # 1. Validate features (US1)
        try:
            clean_features = validate_features(patient_features, modality_available)
        except Exception as e:
            warnings.append(str(e))
            clean_features = patient_features  # Best-effort fallback

        # The target outcome variable is usually `{disease}_susceptibility`
        # In MVP, we map to `wbc` or similar if susceptibility isn't available
        outcome_var = f"{self.disease}_susceptibility"
        if "test" in self.disease:
            outcome_var = "Z"  # synthetic SCM test case

        # 2. Causal attribution & Interventions (US1)
        attributions, interventions = self.scm_pipeline.analyze_patient(
            patient_features=clean_features,
            disease=self.disease,
            outcome_var=outcome_var,
        )

        # 3. Diverse Counterfactuals (US2)
        raw_cfs = generate_counterfactuals(
            patient_data=clean_features,
            disease_model=None, # Passed if DiCE wrapper available
            features_list=list(clean_features.keys()),
            reference_data=self.scm_pipeline._reference_data.get(self.disease, pd.DataFrame()),
            n_cf=5,
        )
        counterfactuals = rank_counterfactuals(raw_cfs)

        # 4. Uncertainty Reduction (US4)
        if 0.4 <= disease_probability <= 0.6:
            test_rec = recommend_diagnostic_test(self.disease, {"prob": disease_probability})
            if test_rec != "clinical_review":
                # Inject as highest priority intervention
                test_iv = InterventionResult(
                    treatment_var=f"diagnostic_test:{test_rec}",
                    treatment_value=1.0,
                    outcome_var="uncertainty",
                    baseline_outcome=1.0,
                    intervened_outcome=0.0,
                    absolute_reduction=999.0, # force top sort
                    relative_reduction_pct=100.0,
                    confidence_interval=(0.0, 0.0),
                    p_value_refutation=0.0,
                    is_identifiable=True,
                )
                interventions.insert(0, test_iv)

        # 5. Narrative Explanation (US1)
        top_intervention = interventions[0] if interventions else None
        top_cf = counterfactuals[0] if counterfactuals else None

        narrative = self.explainer.build_plain_language_narrative(
            disease=self.disease,
            prob=disease_probability,
            attributions=attributions.attributions,
            top_intervention=top_intervention,
            top_counterfactual=top_cf,
        )

        proc_time = (time.perf_counter() - start_t) * 1000

        # Assemble report
        return CausalReport(
            disease=self.disease,
            probability=disease_probability,
            confidence_interval=(max(0.0, disease_probability - 0.1), min(1.0, disease_probability + 0.1)),
            causal_attributions=attributions,
            top_interventions=interventions[:3],
            counterfactuals=counterfactuals[:top_k_counterfactuals],
            narrative=narrative,
            causal_graph_dot=self._graph_dot,
            processing_time_ms=proc_time,
            warnings=warnings,
        )

    def batch_analyze(
        self,
        patients: List[Dict[str, float]],
        disease_probability_list: List[float],
        max_workers: int = 4,
    ) -> List[CausalReport]:
        """Process multiple patients in parallel."""
        if len(patients) != len(disease_probability_list):
            raise ValueError("Mismatched list lengths")

        def _analyze(pt_dict, prob):
            return self.full_causal_analysis(pt_dict, prob)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_analyze, patients, disease_probability_list))
        return results

    def get_intervention_catalog(self) -> List[InterventionOption]:
        """Query available interventions for this disease."""
        return get_catalog(self.disease)

    def apply_federated_update(self, delta_weights: Dict[tuple[str, str], float], epsilon: float = 1.0) -> None:
        """Apply federated learning updates to the causal graph."""
        graph = self.scm_pipeline.store.load_graph(self.disease)
        updated_graph = update_causal_graph_from_aggregated_weights(
            current_graph=graph,
            delta_weights=delta_weights,
            epsilon=epsilon
        )
        self.scm_pipeline.store.save_graph(self.disease, updated_graph)
        self._graph_dot = self.scm_pipeline.store.export_dot(self.disease)
        logger.info("Applied federated update to %s graph", self.disease)
