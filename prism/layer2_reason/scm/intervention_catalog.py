"""T033 - Pre-computed intervention catalog."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

@dataclass
class InterventionOption:
    treatment_var: str
    target_value: float
    cost_free_scheme: str
    cost_private_inr: int
    qaly_gain_estimate: float
    nearest_facility_query_key: str


CATALOGS: Dict[str, List[InterventionOption]] = {
    "tb": [
        InterventionOption(
            treatment_var="nutrition_score",
            target_value=8.0,
            cost_free_scheme="Nikshay Poshan Yojana",
            cost_private_inr=1500,
            qaly_gain_estimate=0.8,
            nearest_facility_query_key="dot_center",
        ),
        InterventionOption(
            treatment_var="crowding_index",
            target_value=1.0,
            cost_free_scheme="None",
            cost_private_inr=5000,
            qaly_gain_estimate=0.5,
            nearest_facility_query_key="none",
        ),
        InterventionOption(
            treatment_var="bmi",
            target_value=22.0,
            cost_free_scheme="ICDS",
            cost_private_inr=1000,
            qaly_gain_estimate=0.6,
            nearest_facility_query_key="phc",
        ),
    ],
    "anemia": [
        InterventionOption(
            treatment_var="nutrition_score",
            target_value=8.0,
            cost_free_scheme="AMB (Anemia Mukt Bharat)",
            cost_private_inr=300,
            qaly_gain_estimate=0.4,
            nearest_facility_query_key="phc",
        ),
    ],
    "heart_failure": [
        InterventionOption(
            treatment_var="smoking_status",
            target_value=0.0,
            cost_free_scheme="NTCP",
            cost_private_inr=0,
            qaly_gain_estimate=1.2,
            nearest_facility_query_key="cessation_clinic",
        ),
        InterventionOption(
            treatment_var="activity_level",
            target_value=5.0,
            cost_free_scheme="None",
            cost_private_inr=0,
            qaly_gain_estimate=0.7,
            nearest_facility_query_key="none",
        ),
    ],
    "dengue": [
        InterventionOption(
            treatment_var="water_quality",
            target_value=5.0,
            cost_free_scheme="Swachh Bharat",
            cost_private_inr=200,
            qaly_gain_estimate=0.2,
            nearest_facility_query_key="none",
        ),
    ],
}


def get_catalog(disease: str) -> List[InterventionOption]:
    """Get the intervention catalog for a disease."""
    # Fallback to general/empty if unknown
    return CATALOGS.get(disease, CATALOGS.get("general", []))
