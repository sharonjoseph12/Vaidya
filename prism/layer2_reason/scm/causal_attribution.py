"""T021 - Causal Attribution: decompose probability into causal factors."""
from __future__ import annotations

import functools
import hashlib
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from layer2_reason.scm.intervention_engine import estimate_intervention_effect

logger = logging.getLogger(__name__)


@dataclass
class CausalAttributions:
    disease: str
    patient_id: Optional[str]
    attributions: Dict[str, float]
    top_cause: str
    top_cause_weight: float
    method: str = "causal_shap"


def _hash_patient(patient_data: Dict[str, float]) -> str:
    """Create a hash for a patient feature dict to use as cache key."""
    # Sort keys for consistent hashing
    sorted_items = tuple(sorted(patient_data.items()))
    return hashlib.md5(json.dumps(sorted_items).encode()).hexdigest()


# In-memory LRU cache to avoid recomputing similar profiles
_ATTRIBUTION_CACHE: Dict[Tuple[str, str], CausalAttributions] = {}
CACHE_SIZE = 512


def compute_causal_attribution(
    patient_data: Dict[str, float],
    disease: str,
    outcome_var: str,
    causal_graph,  # nx.DiGraph
    graph_dot: str,
    reference_data: pd.DataFrame,
) -> CausalAttributions:
    """Compute relative contribution of each parent node to the outcome.

    Parameters
    ----------
    patient_data : the patient's current feature vector
    disease : disease context
    outcome_var : the target variable (e.g., 'tb_susceptibility' or 'wbc')
    causal_graph : networkx DiGraph
    graph_dot : causal graph in Graphviz DOT format
    reference_data : background cohort data
    """
    patient_hash = _hash_patient(patient_data)
    cache_key = (patient_hash, disease)

    if cache_key in _ATTRIBUTION_CACHE:
        return _ATTRIBUTION_CACHE[cache_key]

    if outcome_var not in causal_graph:
        logger.warning("Outcome var %s not in causal graph", outcome_var)
        return _empty_attributions(disease)

    parents = list(causal_graph.predecessors(outcome_var))
    if not parents:
        return _empty_attributions(disease)

    attributions: Dict[str, float] = {}

    for cause in parents:
        if cause not in reference_data.columns:
            continue
        
        # Intervene: set cause to population baseline (mean)
        baseline_val = reference_data[cause].mean()
        
        try:
            effect = estimate_intervention_effect(
                patient_data=patient_data,
                treatment_var=cause,
                treatment_value=baseline_val,
                outcome_var=outcome_var,
                disease=disease,
                graph_dot=graph_dot,
                reference_data=reference_data,
            )
            # Attribution = how much outcome drops if we fix the cause
            attributions[cause] = max(0.0, effect.absolute_reduction)
        except Exception as e:
            logger.debug("Failed to compute attribution for %s: %s", cause, e)
            attributions[cause] = 0.0

    # Normalize to sum to 1.0
    total = sum(attributions.values())
    if total > 0:
        attributions = {k: v / total for k, v in attributions.items()}
    else:
        # Fallback to equal weights
        attributions = {k: 1.0 / len(attributions) for k in attributions}

    top_cause = max(attributions.items(), key=lambda x: x[1])[0] if attributions else "unknown"
    top_weight = attributions.get(top_cause, 0.0)

    result = CausalAttributions(
        disease=disease,
        patient_id=None,
        attributions=attributions,
        top_cause=top_cause,
        top_cause_weight=top_weight,
    )

    # Update cache
    if len(_ATTRIBUTION_CACHE) >= CACHE_SIZE:
        _ATTRIBUTION_CACHE.pop(next(iter(_ATTRIBUTION_CACHE)))
    _ATTRIBUTION_CACHE[cache_key] = result

    return result


def _empty_attributions(disease: str) -> CausalAttributions:
    return CausalAttributions(
        disease=disease,
        patient_id=None,
        attributions={},
        top_cause="unknown",
        top_cause_weight=0.0,
    )
