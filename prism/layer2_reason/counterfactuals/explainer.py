"""T024 - Explainer: narrative generation for causal reports."""
from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# User-friendly names for biomarkers
FEATURE_NAMES: Dict[str, str] = {
    "nutrition_score": "nutritional status",
    "crowding_index": "household crowding",
    "bmi": "body mass index",
    "wbc": "white blood cell count",
    "hemoglobin": "hemoglobin level",
    "temperature": "body temperature",
    "heart_rate": "heart rate",
    "spo2": "oxygen saturation",
    "smoking_status": "smoking status",
    "activity_level": "physical activity",
    "water_quality": "water quality",
    "jaundice_index": "jaundice severity",
}


def get_plain_language_factor_name(feature_key: str) -> str:
    return FEATURE_NAMES.get(feature_key, feature_key.replace("_", " "))


class PRISMExplainer:
    """Generates deterministic, plain-language narratives from causal outputs."""

    def build_plain_language_narrative(
        self,
        disease: str,
        prob: float,
        attributions: Dict[str, float],
        top_intervention: Optional[Any] = None,  # InterventionResult
        top_counterfactual: Optional[Any] = None, # CounterfactualExplanation
    ) -> str:
        """Build the narrative template string. No LLM used."""
        disease_name = disease.replace("_", " ").title()
        if disease.lower() == "tb":
            disease_name = "Tuberculosis"

        lines = [f"{disease_name} probability: {prob:.0%}."]

        # Attribution
        if attributions:
            top_cause_key = max(attributions.items(), key=lambda x: x[1])[0]
            top_weight = attributions[top_cause_key]
            cause_name = get_plain_language_factor_name(top_cause_key)
            lines.append(f"Primary driver: {cause_name} ({top_weight:.0%} contribution).")

        # Intervention
        if top_intervention and top_intervention.absolute_reduction > 0:
            tv_name = get_plain_language_factor_name(top_intervention.treatment_var)
            reduction = top_intervention.relative_reduction_pct
            new_prob = max(0.0, prob - top_intervention.absolute_reduction)
            lines.append(
                f"Highest-impact single action: Optimising {tv_name} "
                f"reduces probability by {reduction:.0f}% (from {prob:.0%} to {new_prob:.0%})."
            )

        # Counterfactual (added in US2, placeholder for US1)
        if top_counterfactual and top_counterfactual.probability_reduction > 0:
            changes = top_counterfactual.changes
            if len(changes) == 1:
                feat = list(changes.keys())[0]
                _, target = changes[feat]
                fname = get_plain_language_factor_name(feat)
                lines.append(
                    f"Recommended path: If {fname} improves to {target:.1f}, "
                    f"probability drops to {top_counterfactual.new_disease_probability:.0%}."
                )
            else:
                lines.append(
                    f"Recommended path: Modifying {len(changes)} lifestyle factors "
                    f"reduces probability to {top_counterfactual.new_disease_probability:.0%}."
                )

        return " ".join(lines)
