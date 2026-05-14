# Quickstart: PRISM Layer 2 — Causal AI Engine

**Role**: Person 2 — Causal AI Engineer | **Date**: 2026-05-14

---

## Prerequisites

- Python 3.11
- Git + access to `001-prism-multimodal-diagnostics` branch
- MIMIC-IV access (PhysioNet credentialing — apply on Day 1)
- ~16GB RAM for PCMCI on full MIMIC-IV; 8GB sufficient for development subset

---

## 1. Environment Setup

```bash
# Clone and switch branch
git clone <repo-url> prism
cd prism
git checkout 001-prism-multimodal-diagnostics

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt
```

---

## 2. Data Acquisition

### MIMIC-IV (critical path — do this on Day 1)
1. Register at https://physionet.org/register/
2. Complete CITI training (required, ~2 hours)
3. Request access to `mimiciv/2.2` dataset
4. Download these tables only (saves time/space):
   ```
   admissions.csv.gz, patients.csv.gz, labevents.csv.gz,
   chartevents.csv.gz, diagnoses_icd.csv.gz
   ```
5. Extract to `data/raw/mimic_iv/`

### NFHS-5 (India)
```bash
python scripts/download_nfhs.py
# Downloads from DHS Program, extracts to data/raw/nfhs5/
```

---

## 3. Data Preprocessing (Phase 2.1)

```bash
# Preprocess MIMIC-IV → patient timeseries
python -m layer2_reason.data.mimic_preprocessor \
  --input data/raw/mimic_iv/ \
  --output data/processed/mimic_patients.pkl \
  --min-hours 48

# Preprocess NFHS-5 → India features
python -m layer2_reason.data.nfhs_preprocessor \
  --input data/raw/nfhs5/ \
  --output data/processed/nfhs_india.pkl

# Build panel dataset + lagged features
python -m layer2_reason.data.feature_engineering \
  --input data/processed/mimic_patients.pkl \
  --output data/processed/panel_dataset.pkl \
  --save-scalers data/scalers/

# Validate data
python -m layer2_reason.data.data_validator \
  --panel data/processed/panel_dataset.pkl
```

Expected output:
```
[INFO] Patients processed: 45,231
[INFO] Disease cohort sizes: TB=1,842 Anemia=8,441 HeartFailure=12,330 ...
[INFO] Missing rate per biomarker: hemoglobin=12.3% creatinine=8.7% ...
[INFO] Validation PASSED
```

---

## 4. Causal Discovery (Phase 2.2)

```bash
# Run full discovery pipeline (2–6 hours on first run; saves graphs)
python scripts/run_causal_discovery.py \
  --panel data/processed/panel_dataset.pkl \
  --nfhs data/processed/nfhs_india.pkl \
  --output-dir layer2_reason/graphs/ \
  --diseases tb anemia general \
  --tau-max 20

# Validate discovered graphs
python -m layer2_reason.causal_discovery.graph_validator \
  --graphs-dir layer2_reason/graphs/
```

**Note**: PCMCI runtime scales with `tau_max × n_variables². Set `--tau-max 5` for quick iteration during development.

Commit graphs after validation:
```bash
git add layer2_reason/graphs/
git commit -m "feat: add validated causal graphs for TB, anemia, general cohort"
```

---

## 5. SCM Training (Phase 2.3)

```bash
# Fit SCMs on discovered graphs
python -m layer2_reason.scm.scm_builder \
  --panel data/processed/panel_dataset.pkl \
  --graphs-dir layer2_reason/graphs/ \
  --output-dir layer2_reason/scm_models/ \
  --diseases tb anemia general
```

Expected output per disease:
```
[INFO] Fitting TB SCM on 1,842 patients
[INFO] Node R² scores: hemoglobin=0.71 wbc=0.68 temperature=0.52 ...
[INFO] SCM saved: layer2_reason/scm_models/tb_scm.pkl
```

---

## 6. CausalVAE Training (Phase 2.4)

```bash
# Train on MIMIC panel dataset (~2 hours on Colab Pro A100)
python scripts/train_causal_vae.py \
  --panel data/processed/panel_dataset.pkl \
  --latent-dim 8 \
  --hidden-dim 128 \
  --epochs 200 \
  --beta 4.0 \
  --output layer2_reason/vae_weights/causal_vae.pt
```

For local CPU testing (smoke test only):
```bash
python scripts/train_causal_vae.py --epochs 5 --max-patients 500
```

---

## 7. Running Tests

```bash
# All tests (no MIMIC required — synthetic fixtures)
pytest layer2_reason/tests/ -v --cov=layer2_reason

# Specific test file
pytest layer2_reason/tests/test_causal_engine.py -v

# Performance test only
pytest layer2_reason/tests/test_causal_engine.py -v -k "performance"

# Expected coverage: >80% across all modules
```

---

## 8. Using the Engine (Quick Example)

```python
from layer2_reason.causal_engine import PRISMCausalEngine

# Initialise (loads graph + SCM at construction)
engine = PRISMCausalEngine(disease="tb")

# Patient feature vector (from Layer 1)
patient = {
    "heart_rate": 98.0,
    "spo2": 94.0,
    "cough_tb_prob": 0.74,
    "jaundice_index": 0.1,
    "nutrition_score": 2.5,
    "crowding_index": 3.8,
    "wealth_index": 2.0,
    "age": 32.0,
    # ... (see contracts/layer1_layer2_schema.md for full list)
}

# Run full causal analysis
report = engine.full_causal_analysis(
    patient_features=patient,
    disease_probability=0.79,
    top_k_counterfactuals=3
)

print(report.narrative)
# → "TB probability: 79%. Primary driver: nutrition_score (38% contribution).
#    Highest-impact action: nutrition_score set to 6.0 reduces probability
#    by 48% (from 79% to 31%)."

print(report.causal_attributions.attributions)
# → {"nutrition_score": 0.38, "crowding_index": 0.24, "prior_infection": 0.21, ...}
```

---

## 9. Integration Test with Person 1 (Layer 1 → Layer 2)

```bash
pytest tests/integration/test_layer1_layer2.py -v
# Requires layer1_sense package to be installed (coordinate with Person 1)
```

---

## 10. Monthly Dev Checkpoints

| Month | Command to verify |
|-------|------------------|
| 1 | `pytest layer2_reason/tests/test_data_pipeline.py` |
| 2 | `python scripts/run_causal_discovery.py --diseases tb` |
| 3 | `pytest layer2_reason/tests/test_scm.py -k "intervention"` |
| 4 | `pytest layer2_reason/tests/test_counterfactuals.py` |
| 5 | `pytest layer2_reason/tests/test_causal_engine.py -k "performance"` |
| 6 | `pytest tests/integration/test_layer1_layer2.py` |
