# PRISM Layer 2: Causal Engine API

This document describes the interface contract exposed by `PRISMCausalEngine` to the rest of the PRISM architecture (specifically Layer 3 Digital Twin and Person 4 API layer).

## Instantiation

```python
from layer2_reason.causal_engine import PRISMCausalEngine

engine = PRISMCausalEngine(
    disease="tb", 
    graphs_dir="layer2_reason/graphs/",
    models_dir="layer2_reason/scm_models/"
)
```

## Core Analysis

Provides causal attribution, deterministic explanations, and ranked counterfactuals.

```python
report = engine.full_causal_analysis(
    patient_features={"nutrition_score": 4.0, "wbc": 12.0},
    disease_probability=0.85,
    top_k_counterfactuals=3,
    modality_available={"labs": True, "vitals": True}
)
```

**`CausalReport` Schema:**
- `disease` (str)
- `probability` (float)
- `causal_attributions` (`CausalAttributions`)
  - `top_cause` (str)
  - `attributions` (Dict[str, float] summing to 1.0)
- `top_interventions` (List[`InterventionResult`])
- `counterfactuals` (List[`CounterfactualExplanation`])
- `narrative` (str) — Plain language string
- `causal_graph_dot` (str) — Graphviz string for UI
- `processing_time_ms` (float)
- `warnings` (List[str])

## Layer 3 Integration (ODE Forcing Functions)

Get deterministic intervention catalogs and export effects for the Neural ODE.

```python
# 1. Query available interventions without patient data
catalog = engine.get_intervention_catalog()

# 2. During analysis, extract ODE forcing parameter map
if report.top_interventions:
    forcing_fn = report.top_interventions[0].to_ode_forcing_fn()
    # Returns: {
    #   "treatment_var": "nutrition_score", 
    #   "effect_magnitude": 0.2, 
    #   "onset_delay_days": 14.0, 
    #   "duration_days": 30.0
    # }
```

## Layer 4 Integration (Federated Learning)

Apply differentially-private weight updates from the federated server without restarting.

```python
engine.apply_federated_update(
    delta_weights={("nutrition_score", "bmi"): 0.15},
    epsilon=1.5
)
```
