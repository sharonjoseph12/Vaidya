# PRISMCausalEngine API Contract

**Layer**: 2 — REASON | **Version**: 1.0 | **Date**: 2026-05-14

This document defines the binding interface contract for `PRISMCausalEngine`.
All consumers (Layer 3, FastAPI backend) depend on this contract.

---

## Primary Class: `PRISMCausalEngine`

```python
from layer2_reason.causal_engine import PRISMCausalEngine
```

### Constructor

```python
PRISMCausalEngine(
    disease: str,                # "tb" | "anemia" | "dengue" | "pneumonia" |
                                 # "heart_failure" | "general"
    graphs_dir: str = "layer2_reason/graphs/",
    models_dir: str = "layer2_reason/scm_models/",
)
```

- Loads causal graph and SCM model at construction time (no per-call loading).
- Raises `FileNotFoundError` if graph or model files are missing.
- Raises `ValueError` for unsupported `disease` strings.

---

### `full_causal_analysis()`

```python
def full_causal_analysis(
    patient_features: Dict[str, float],
    disease_probability: float,
    top_k_counterfactuals: int = 3,
) -> CausalReport
```

**Input**:
- `patient_features` — flat dict of normalized biomarker + socioeconomic features. See `layer1_layer2_schema.md` for required keys.
- `disease_probability` — float in [0.0, 1.0] from Layer 1 fusion model.
- `top_k_counterfactuals` — number of counterfactuals to generate (default 3, max 5).

**Output**: `CausalReport` dataclass (see `data-model.md`).

**Performance guarantee**: < 200ms median on pre-warmed engine instance.

**Error handling**:
- Missing features: imputed with cohort mean; `warnings` list in report populated.
- Non-identifiable causal effect: computed with backdoor + `is_identifiable=False` flag.
- DiCE failure: returns empty `counterfactuals` list + warning; does not raise.

---

### `batch_analyze()`

```python
def batch_analyze(
    patients: List[Dict[str, float]],
    disease_probability_list: List[float],
) -> List[CausalReport]
```

**Implementation**: `ThreadPoolExecutor(max_workers=4)`.
**Performance**: 100 patients < 15 seconds.

---

### `get_intervention_catalog()`

```python
def get_intervention_catalog(
    disease: str,
) -> List[InterventionOption]
```

Returns pre-computed intervention options for a disease, with cost/feasibility metadata. Used to populate the UI intervention selector without running full analysis.

```python
@dataclass
class InterventionOption:
    treatment_var: str
    treatment_value: float
    label: str              # "Nutritional supplementation to adequate level"
    cost_free_scheme: str   # "ICDS scheme (₹0)" | "None"
    cost_private_inr: int
    feasibility_score: float
    estimated_reduction_pct: float  # population-average estimate
```

---

## Supported Disease Strings

| String | Description |
|--------|-------------|
| `"tb"` | Tuberculosis (PCMCI TB cohort + FCI NFHS) |
| `"anemia"` | Anemia (PCMCI Anemia cohort) |
| `"dengue"` | Dengue fever |
| `"pneumonia"` | Bacterial/viral pneumonia |
| `"heart_failure"` | Congestive heart failure |
| `"general"` | Full population graph (fallback) |

---

## Error Types

| Exception | When |
|-----------|------|
| `ValueError` | Unsupported disease string |
| `FileNotFoundError` | Missing graph or SCM model files |
| `InsufficientFeaturesError` | < 3 non-NaN features provided |
| `CausalIdentificationWarning` | Effect not identifiable (non-fatal) |
