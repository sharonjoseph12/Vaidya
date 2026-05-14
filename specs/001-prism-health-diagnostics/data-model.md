# Data Model: PRISM Layer 3+4

## Core Entities

### PatientLatentState
- **ID**: UUID (links to ABHA ID)
- **Z_Vector**: Tensor[32] (The compressed latent physiological representation)
- **Z_LogVar**: Tensor[32] (Uncertainty of the latent state)
- **Last_Observation_Time**: Timestamp
- **Organ_Specialization**: Enum (Cardio, Metabolic, Infectious)

### TrajectoryPrediction
- **Patient_ID**: UUID
- **Time_Points**: List[Timestamp]
- **Predicted_Mean**: Tensor[T, D] (D = number of biomarkers)
- **Predicted_Uncertainty**: Tensor[T, D]
- **Confidence_Interval**: List[Range] (Calibrated 90% bounds)

### ClinicalIntervention
- **Action_ID**: Int (1-15)
- **Action_Type**: String (e.g., "Sputum Test", "Nutritional Support")
- **Estimated_QALY_Gain**: Float
- **Estimated_Cost**: Float (INR)
- **Facility_Type**: Enum (PHC, District Hospital, Private)

## Relationships
- A `PatientLatentState` is the input to a `TrajectoryPrediction`.
- A `TrajectoryPrediction` is used by the RL `ClinicalIntervention` engine to calculate rewards.
- `PatientLatentState` is updated when new `Biomarkers` are sensed in Layer 1.

## State Transitions
- **Observation Update**: `(z_t, obs) -> z_{t+1}` via ODERNNEncoder.
- **Natural Evolution**: `z_t -> z_{t+dt}` via ODEFunc.
- **Intervention**: `z_t -> z'_t` via Causal Forcing Function.
