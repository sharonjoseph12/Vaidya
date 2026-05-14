# Data Model: PRISM Layer 2 — Causal AI Engine

**Feature**: `001-prism-multimodal-diagnostics` | **Phase**: 1 — Design
**Date**: 2026-05-14

---

## Core Entities

### PatientTimeseries
Represents a single patient's preprocessed biomarker time series extracted from MIMIC-IV.

```python
@dataclass
class PatientTimeseries:
    patient_id: str
    timeseries: pd.DataFrame        # columns: [time_hours, hemo, wbc, creat, temp, hr, spo2, rr, sbp, glucose, crp, bili, platelet]
    labels: List[str]               # ICD-10 disease labels, e.g. ["A15", "D50"]
    disease_names: List[str]        # Human-readable: ["tb", "anemia"]
    demographics: Dict[str, float]  # {age, sex_binary, admission_weight, bmi}
    missing_rate: Dict[str, float]  # {biomarker: fraction_missing}
```

**Validation rules**:
- `len(timeseries) >= 48` (minimum 48 hours of data)
- At least 5 distinct biomarker readings across all variables
- `time_hours` must be monotonically increasing
- All biomarker values within physiological bounds (checked in `data_validator.py`)

---

### PanelDataset
Flat analysis-ready dataset for causal discovery — all patients, all timepoints.

```python
@dataclass
class PanelDataset:
    data: pd.DataFrame              # shape: (n_patients × n_timepoints, n_features)
                                    # features = biomarkers + lag1..lag20 + rolling stats
    feature_names: List[str]
    disease_labels: pd.Series       # aligned disease label per row
    scalers: Dict[str, StandardScaler]  # per-biomarker scalers
    n_patients: int
    n_timepoints_per_patient: int   # mean (irregular — varies)
```

---

### CausalGraph
A validated causal graph for a specific disease cohort, stored as networkx DiGraph.

```python
@dataclass
class CausalGraph:
    disease: str                    # "tb" | "anemia" | "general" | ...
    graph: nx.DiGraph               # nodes=biomarker names; edges with attributes
    discovery_method: str           # "pcmci" | "fci" | "merged"
    validation_status: str          # "passed" | "warned" | "failed"
    validation_report: Dict         # per-check pass/fail
    timestamp: datetime

# Edge attributes on nx.DiGraph:
# {
#   "lag_hours": float,         # PCMCI temporal lag
#   "correlation": float,       # MCI partial correlation coefficient
#   "p_value": float,
#   "edge_type": str,           # "direct" | "bidirected" | "possible_direct" (FCI)
#   "confidence": str           # "high" | "medium" | "uncertain"
# }
```

**State transitions**: `discovered` → `validated` → `merged` → `committed`

---

### SCMModel
Fitted Structural Causal Model for a disease cohort.

```python
@dataclass
class SCMModel:
    disease: str
    node_models: Dict[str, Any]     # {node_name: fitted sklearn model}
    noise_params: Dict[str, Tuple[float, float]]  # {node: (mean, std)}
    causal_graph: CausalGraph
    feature_names: List[str]
    training_cohort_size: int
    fit_r2_scores: Dict[str, float] # {node: R² on training data}
```

---

### InterventionResult
Result of a Pearl do-calculus intervention estimate.

```python
@dataclass
class InterventionResult:
    treatment_var: str              # e.g. "nutrition_score"
    treatment_value: float          # the intervened value
    outcome_var: str                # e.g. "tb_probability"
    baseline_outcome: float         # patient's current value
    intervened_outcome: float       # estimated value after intervention
    absolute_reduction: float       # baseline − intervened
    relative_reduction_pct: float   # reduction as % of baseline
    confidence_interval: Tuple[float, float]   # 95% CI
    p_value_refutation: float       # from random_common_cause refutation
    is_identifiable: bool           # whether backdoor criterion was met
```

---

### CounterfactualExplanation
A single actionable counterfactual — how to change the patient's features to reach healthy state.

```python
@dataclass
class CounterfactualExplanation:
    changes: Dict[str, Tuple[float, float]]  # {feature: (current_value, cf_value)}
    new_disease_probability: float
    probability_reduction: float             # original − new
    n_features_changed: int
    feasibility_score: float                 # 0.0–1.0
    rank: int                                # 1 = most feasible/impactful
```

---

### CausalAttributions
Decomposition of disease probability into causal factor contributions.

```python
@dataclass
class CausalAttributions:
    disease: str
    patient_id: Optional[str]
    attributions: Dict[str, float]  # {cause: weight}, normalised to sum 1.0
    top_cause: str                  # highest-weight factor
    top_cause_weight: float
    method: str                     # "causal_shap"
```

---

### CausalReport
The complete output of `PRISMCausalEngine.full_causal_analysis()`. This is the primary output consumed by Layer 3 and the API.

```python
@dataclass
class CausalReport:
    disease: str
    probability: float                              # from Layer 1
    confidence_interval: Tuple[float, float]        # from Layer 1 conformal prediction
    causal_attributions: CausalAttributions
    top_interventions: List[InterventionResult]     # sorted by absolute_reduction DESC
    counterfactuals: List[CounterfactualExplanation]  # sorted by feasibility DESC
    narrative: str                                  # plain language, deterministic
    causal_graph_dot: str                           # Graphviz DOT string
    processing_time_ms: float
    warnings: List[str]                             # e.g. "Effect not identifiable for ..."
```

---

## NFHS Feature Schema

Socioeconomic and environmental variables extracted from NFHS-5 (India-specific):

| Feature Name | Source Variable | Type | Description |
|---|---|---|---|
| `nutrition_score` | hv237, hml32 | float 0–10 | Composite food security + malnutrition |
| `hemoglobin` | hb56 | float g/dL | Measured hemoglobin |
| `anemia_level` | hb57 | int 0–3 | 0=none, 1=mild, 2=moderate, 3=severe |
| `tb_symptom_score` | s103a–s103e | int 0–5 | Count of TB symptom flags |
| `wealth_index` | hv270 | int 1–5 | Household wealth quintile |
| `urban_rural` | hv025 | binary | 1=urban, 0=rural |
| `water_source` | hv201 | int | WHO water source classification |
| `sanitation_type` | hv205 | int | WHO toilet type classification |
| `crowding_index` | derived | float | hv009 (members) / hv216 (rooms) |
| `anemia_binary` | derived | binary | Hb < 11 (children) or < 12 (women) |

---

## Biomarker Physiological Bounds (Validation)

| Biomarker | Min | Max | Unit |
|-----------|-----|-----|------|
| hemoglobin | 3.0 | 20.0 | g/dL |
| wbc | 0.5 | 100.0 | ×10³/μL |
| creatinine | 0.1 | 20.0 | mg/dL |
| temperature | 32.0 | 42.5 | °C |
| heart_rate | 20 | 300 | BPM |
| spo2 | 50 | 100 | % |
| respiratory_rate | 4 | 60 | breaths/min |
| sbp | 50 | 250 | mmHg |
| glucose | 20 | 600 | mg/dL |
| crp | 0.0 | 500.0 | mg/L |
| bilirubin_total | 0.1 | 50.0 | mg/dL |
| platelet | 5 | 1500 | ×10³/μL |

Values outside these ranges are flagged as `outlier` and excluded from causal discovery training but logged for audit.
