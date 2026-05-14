# API Contracts: PRISM Backend

**Date**: 2026-05-14 | **Base URL**: `/api/v1`

## Authentication

All endpoints (except `/health`) require a valid JWT in the `Authorization: Bearer <token>` header. Tokens are issued by Supabase Auth.

---

## Patients API (`/api/v1/patients`)

### POST `/patients`
Create a new patient record.

**Request**:
```json
{
  "abha_id": "91-1234-5678-1234",     // optional
  "demographics": {                    // encrypted server-side
    "name": "Anonymous",
    "age": 32,
    "sex": "M",
    "location": "Mangalore",
    "socioeconomic_tier": "BPL"
  },
  "consent_given": true,
  "consent_purpose": "CAREMGT"
}
```

**Response** `201 Created`:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "abha_id": "91-1234-5678-1234",
  "created_at": "2026-05-14T12:00:00Z",
  "consent_given": true
}
```

**Errors**: `400` (invalid ABHA format), `409` (duplicate ABHA ID)

### GET `/patients/{patient_id}`
Retrieve patient record with decrypted demographics (authorized users only).

**Response** `200 OK`:
```json
{
  "id": "550e8400-...",
  "abha_id": "91-1234-5678-1234",
  "demographics": { "name": "...", "age": 32, ... },
  "sessions_count": 3,
  "last_session_date": "2026-05-14T12:00:00Z"
}
```

---

## Diagnostics API (`/api/v1/diagnostics`)

### POST `/diagnostics/analyze`
Start a full PRISM analysis pipeline. Accepts multipart form data.

**Request** (multipart/form-data):
- `audio_file`: File (optional) — .wav or .mp3, 30+ seconds
- `video_file`: File (optional) — .mp4 or .webm, 30+ seconds
- `patient_id`: string (required) — UUID of registered patient
- `session_type`: string (required) — "full" | "audio_only" | "visual_only" | "rppg_only"
- `patient_features`: JSON string (required) — additional features:
  ```json
  {
    "nutrition_score": 3.0,
    "bmi": 17.5,
    "smoking_status": 0,
    "activity_level": 2,
    "crowding_index": 4.2,
    "monthly_income": 8000
  }
  ```

**Response** `202 Accepted`:
```json
{
  "session_id": "660e8400-...",
  "task_id": "celery-task-uuid",
  "status": "queued",
  "estimated_time_seconds": 10
}
```

**Errors**: `400` (missing required fields), `404` (patient not found), `413` (file too large, max 50MB)

### GET `/diagnostics/results/{session_id}`
Get analysis results for a completed session.

**Response** `200 OK`:
```json
{
  "session_id": "660e8400-...",
  "status": "complete",
  "primary_diagnosis": "TB",
  "confidence_score": 0.84,
  "disease_probabilities": {"TB": 0.79, "Pneumonia": 0.12, ...},
  "sense_results": { ... },      // SenseResult schema
  "causal_results": { ... },     // CausalResult schema
  "twin_trajectory": { ... },   // TwinTrajectory schema
  "intervention_plan": { ... }, // InterventionPlan schema
  "uncertainty_bounds": {"TB": [0.71, 0.86], ...},
  "processing_time_ms": 2800,
  "model_version": "prism-v1.0.0"
}
```

**Errors**: `404` (session not found), `202` (still processing — returns current status)

### GET `/diagnostics/stream/{session_id}`
Server-Sent Events stream for real-time pipeline progress.

**Response**: `text/event-stream`
```
data: {"stage": "sensing", "progress": 0.3, "message": "Analyzing cough patterns..."}

data: {"stage": "reasoning", "progress": 0.5, "message": "Building causal graph..."}

data: {"stage": "projecting", "progress": 0.7, "message": "Simulating trajectory..."}

data: {"stage": "optimizing", "progress": 0.9, "message": "Ranking interventions..."}

data: {"stage": "complete", "progress": 1.0, "session_id": "660e8400-..."}
```

### GET `/diagnostics/report/{session_id}/pdf`
Generate and return a clinical PDF report.

**Response** `200 OK`: `application/pdf` binary

---

## ABDM API (`/api/v1/abdm`)

### POST `/abdm/verify/{abha_id}`
Verify an ABHA ID and retrieve basic profile.

**Response** `200 OK`:
```json
{
  "verified": true,
  "name": "Patient Name",
  "age": 32,
  "gender": "M",
  "abha_address": "patient@abdm"
}
```

**Errors**: `404` (ABHA ID not found), `503` (ABDM gateway unavailable)

### POST `/abdm/fetch-history`
Fetch patient health records from ABDM (requires consent).

**Request**:
```json
{
  "abha_id": "91-1234-5678-1234",
  "date_from": "2023-01-01",
  "date_to": "2026-05-14",
  "hi_types": ["DiagnosticReport", "Prescription", "OPConsultation"]
}
```

**Response** `200 OK`:
```json
{
  "consent_status": "approved",
  "records_count": 5,
  "records": [
    {
      "type": "diagnostic",
      "date": "2025-03-15",
      "findings": "Mild anemia, Hb 10.2 g/dL",
      "codes": ["D50.9"]
    }
  ],
  "twin_enrichment": {
    "historical_biomarkers": [
      {"date": "2025-03-15", "hemoglobin": 10.2, "wbc": 8.5}
    ]
  }
}
```

### POST `/abdm/push-report`
Push PRISM diagnostic report to patient's ABHA health locker.

**Request**:
```json
{
  "session_id": "660e8400-...",
  "abha_id": "91-1234-5678-1234"
}
```

**Response** `200 OK`:
```json
{
  "status": "success",
  "abdm_record_id": "abdm-record-uuid",
  "fhir_resource_type": "DiagnosticReport"
}
```

---

## Federated Learning API (`/api/v1/federated`)

### GET `/federated/status`
Get FL server status and latest round info.

**Response** `200 OK`:
```json
{
  "server_status": "running",
  "current_round": 42,
  "total_nodes": 5,
  "active_nodes": 3,
  "global_model_version": "prism-fl-v42",
  "cumulative_dp_epsilon": 4.2,
  "last_round_metrics": {
    "accuracy": 0.84,
    "loss": 0.32,
    "per_disease_auc": {"TB": 0.87, "Anemia": 0.91, ...}
  }
}
```

### POST `/federated/register-node`
Register a new hospital node for FL participation.

**Request**:
```json
{
  "hospital_name": "KMC Mangalore",
  "location": "Mangalore, Karnataka",
  "estimated_samples": 500
}
```

**Response** `201 Created`:
```json
{
  "node_id": "770e8400-...",
  "client_config": {
    "server_address": "fl.prism-health.app:8080",
    "model_name": "prism_cough_classifier",
    "local_epochs": 3,
    "learning_rate": 0.0001,
    "gradient_clip_norm": 1.0
  }
}
```

### GET `/federated/rounds`
List FL training rounds with metrics.

**Response** `200 OK`:
```json
{
  "rounds": [
    {
      "round_number": 42,
      "participating_nodes": 3,
      "rejected_nodes": 0,
      "metrics": {"accuracy": 0.84},
      "dp_epsilon_spent": 0.1,
      "completed_at": "2026-05-14T10:00:00Z"
    }
  ]
}
```

---

## Health Check

### GET `/health`
No auth required.

**Response** `200 OK`:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected",
  "fl_server": "running"
}
```

---

## Cross-Layer Interface Contracts

These are the data contracts between Person 1/2/3's ML layers and Person 4's platform.

### Layer 1 → Platform (SenseResult)
```python
@dataclass
class SenseResult:
    disease_probabilities: Dict[str, float]  # 12 diseases, each 0–1
    rppg: RPPGResult                         # hr, spo2, hrv_rmssd, hrv_sdnn, lf_hf, rr, confidence
    audio: AudioResult                       # cough_detected, disease_probs, breathing_rate, abnormal_sounds
    visual: VisualResult                     # jaundice, anemia, cyanosis, dengue_flush, pallor scores
    imu: Optional[IMUResult]                 # gait_symmetry, cadence, step_variability (nullable if unavailable)
    uncertainty: Dict[str, Tuple[float, float]]  # per-disease [lower, upper] bounds
    modalities_available: List[str]          # which modalities contributed
    processing_time_ms: int
```

### Layer 2 → Platform (CausalResult)
```python
@dataclass
class CausalResult:
    attributions: Dict[str, float]           # cause → weight, sums to 1.0
    top_intervention: str                    # most impactful actionable intervention
    intervention_effects: Dict[str, float]   # intervention → prob_reduction
    patient_risk_factors: Dict[str, float]   # normalized risk factor scores
    counterfactuals: List[CounterfactualExplanation]
    narrative: str                           # template-generated explanation
    causal_graph_dot: str                    # DOT format for visualization
```

### Layer 3+4 → Platform (TwinRLResult)
```python
@dataclass
class TwinRLResult:
    trajectory: TrajectoryData               # without_intervention + with_best_intervention arrays
    months_to_critical: float                # without intervention
    months_to_critical_with_intervention: float
    intervention_plan: List[InterventionRecommendation]
    qaly_gain_estimate: float
    pareto_options: List[ParetoOption]        # multi-objective trade-offs
    active_uncertainty_reduction: Optional[TestRecommendation]
```
