"""T022 - Intervention Engine: Pearl's do-calculus via DoWhy."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class InterventionResult:
    treatment_var: str
    treatment_value: float
    outcome_var: str
    baseline_outcome: float
    intervened_outcome: float
    absolute_reduction: float
    relative_reduction_pct: float
    confidence_interval: Tuple[float, float]
    p_value_refutation: float
    is_identifiable: bool

    def to_ode_forcing_fn(self) -> Dict:
        """Convert intervention to Layer 3 Neural ODE forcing function."""
        return {
            "treatment_var": self.treatment_var,
            "effect_magnitude": self.absolute_reduction,
            "onset_delay_days": 1.0,  # default assumed delay
            "duration_days": 30.0,    # default assumed duration
        }


def estimate_intervention_effect(
    patient_data: Dict[str, float],
    treatment_var: str,
    treatment_value: float,
    outcome_var: str,
    disease: str,
    graph_dot: str,
    reference_data: pd.DataFrame,
) -> InterventionResult:
    """Estimate causal effect of an intervention using DoWhy.

    Parameters
    ----------
    patient_data : the patient's current feature vector
    treatment_var : variable to intervene on
    treatment_value : value to set treatment_var to (do-calculus)
    outcome_var : the variable we want to change
    disease : disease context
    graph_dot : causal graph in Graphviz DOT format
    reference_data : background cohort data for backdoor adjustment
    """
    try:
        from dowhy import CausalModel
    except ImportError as e:
        raise ImportError("dowhy not installed. Run: pip install dowhy") from e

    # Ensure all required variables are in the data
    req_vars = [treatment_var, outcome_var]
    if not all(v in reference_data.columns for v in req_vars):
        logger.warning("Missing variables for intervention: %s", req_vars)
        return _empty_intervention(treatment_var, treatment_value, outcome_var)

    baseline_val = patient_data.get(outcome_var, 0.0)

    try:
        model = CausalModel(
            data=reference_data,
            graph=graph_dot.replace("\n", ""),
            treatment=treatment_var,
            outcome=outcome_var,
        )

        identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)

        # We need a point estimate for the patient, but DoWhy gives ATE/CATE
        # For simplicity in MVP, we compute ATE and apply it to the patient's baseline
        estimate = model.estimate_effect(
            identified_estimand,
            method_name="backdoor.linear_regression",
            target_units="ate",
        )

        ate = estimate.value

        # Calculate new outcome based on treatment delta
        current_treatment_val = patient_data.get(treatment_var, 0.0)
        delta_treatment = treatment_value - current_treatment_val
        intervened_val = baseline_val + (ate * delta_treatment)

        abs_reduction = baseline_val - intervened_val
        rel_reduction = (abs_reduction / baseline_val * 100) if baseline_val != 0 else 0.0

        refutation = model.refute_estimate(
            identified_estimand, estimate,
            method_name="random_common_cause",
        )
        pval = getattr(refutation, "refutation_result", {}).get("p_value", 1.0)
        if pval is None: pval = 1.0

        ci = estimate.get_confidence_intervals()
        if ci is not None and len(ci) > 0:
            ci_tuple = (float(ci[0][0]), float(ci[0][1]))
        else:
            ci_tuple = (0.0, 0.0)

        return InterventionResult(
            treatment_var=treatment_var,
            treatment_value=treatment_value,
            outcome_var=outcome_var,
            baseline_outcome=baseline_val,
            intervened_outcome=intervened_val,
            absolute_reduction=abs_reduction,
            relative_reduction_pct=rel_reduction,
            confidence_interval=ci_tuple,
            p_value_refutation=float(pval),
            is_identifiable=not identified_estimand.no_directed_path,
        )

    except Exception as exc:
        logger.warning("Intervention estimation failed: %s", exc)
        return _empty_intervention(treatment_var, treatment_value, outcome_var, baseline_val)


def _empty_intervention(tv: str, val: float, out: str, base: float = 0.0) -> InterventionResult:
    return InterventionResult(
        treatment_var=tv, treatment_value=val, outcome_var=out,
        baseline_outcome=base, intervened_outcome=base, absolute_reduction=0.0,
        relative_reduction_pct=0.0, confidence_interval=(0.0, 0.0),
        p_value_refutation=1.0, is_identifiable=False,
    )
