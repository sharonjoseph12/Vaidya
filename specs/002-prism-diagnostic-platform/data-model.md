# Data Model: PRISM Diagnostic Platform

The system leverages standard Pydantic models in the backend and TypeScript interfaces in the frontend.

## Entities

### `DiagnosticResult`
The aggregate model representing the outcome of a session.
- `session_id`: String (UUID or "demo-patient-id")
- `primary_diagnosis`: String
- `disease_probabilities`: Dict[String, Float]
- `uncertainty_bounds`: Dict[String, Tuple[Float, Float]]
- `causal_results`: `CausalAnalysisResult`
- `twin_trajectory`: `TwinTrajectory`
- `intervention_plan`: `InterventionPlan`
- `status`: String

### `DEMO_PATIENT_RESULT`
A predefined constant mock matching the `DiagnosticResult` schema, injected when an exception occurs for the demo patient.
```python
DEMO_PATIENT_RESULT = {
    "disease_probabilities": {"TB": 0.79, "Anemia": 0.71, "Pneumonia": 0.12, "Healthy": 0.05},
    "uncertainty_bounds": {"TB": [0.70, 0.88], "Anemia": [0.65, 0.78]},
    "primary_diagnosis": "TB",
    "causal_results": {
        "attributions": {"malnutrition": 0.38, "poor_ventilation": 0.24, "prior_infection": 0.21, "genetic_factors": 0.17},
        "narrative": "Based on causal inference, the high risk of TB is predominantly driven by malnutrition and poor ventilation.",
        "causal_graph_dot": "digraph G { malnutrition -> TB [weight=0.38]; poor_ventilation -> TB [weight=0.24]; }",
        "counterfactuals": [{
            "changes": {"malnutrition": ["Severe", "Normal"]},
            "original_probability": 0.79,
            "new_probability": 0.31,
            "feasibility_score": 0.85
        }]
    },
    "twin_trajectory": {
        "months_to_critical": 5.0,
        "months_to_critical_with_intervention": 19.0,
        "intervention_applied": "Nutritional_Supplementation",
        "without_intervention": [
            {"month": 0, "values": {"tb_prob": 0.79}},
            {"month": 3, "values": {"tb_prob": 0.85}},
            {"month": 6, "values": {"tb_prob": 0.92}}
        ],
        "with_best_intervention": [
            {"month": 0, "values": {"tb_prob": 0.79}},
            {"month": 3, "values": {"tb_prob": 0.65}},
            {"month": 6, "values": {"tb_prob": 0.45}}
        ]
    },
    "intervention_plan": {
        "recommendations": [
            {
                "rank": 1,
                "intervention": "Nutritional_Supplementation_and_DOTS",
                "description": "Provide caloric support and initiate DOTS therapy.",
                "cost_private": 400,
                "cost_govt": 0,
                "qaly_gain": 2.5,
                "time_to_effect_days": 30,
                "side_effect_risk": 0.05,
                "scheme": "Nikshay Poshan Yojana",
                "nearest_facility": {"name": "Primary Health Center", "distance_km": 1.2}
            }
        ],
        "pareto_options": [
            {"cost": 0, "qaly_gain": 2.0, "label": "Free Government Treatment"},
            {"cost": 1400, "qaly_gain": 3.0, "label": "Private Specialist"}
        ],
        "active_uncertainty_reduction": {
            "recommended_test": "Sputum AFB Smear",
            "cost": 0,
            "expected_uncertainty_reduction": 0.45,
            "rationale": "High certainty requirement for definitive DOTS initiation."
        }
    }
}
```
