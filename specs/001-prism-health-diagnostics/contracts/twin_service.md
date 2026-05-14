# Twin Interface Contract

## Overview
This contract defines the interaction between the UI/Backend and the Digital Twin engine (Layer 3).

## Methods

### `predict_trajectory`
- **Input**:
  - `observations`: JSON mapping of biomarker IDs to values.
  - `timestamps`: List of relative times (seconds from start).
  - `horizon`: Projection period in days (default 30).
- **Output**:
  - `trajectory`: Array of state objects `{t, biomarkers: {id: val, uncertainty}}`.
  - `alerts`: List of critical thresholds reached during projection.

### `simulate_intervention`
- **Input**:
  - `patient_id`: Reference to current state.
  - `intervention_id`: ID of the clinical action.
  - `start_time`: When the intervention begins.
- **Output**:
  - `counterfactual_trajectory`: The predicted outcome path IF the action is taken.
  - `qaly_impact`: Expected quality-of-life improvement.

## Error States
- `INSUFFICIENT_DATA`: Less than 2 observations provided for ODE-RNN.
- `DIVERGED`: ODE solver failed to converge on the manifold.
- `OUT_OF_DOMAIN`: Patient biomarkers outside trained organ twin range.
