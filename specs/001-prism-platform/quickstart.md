# Quickstart: Explainability & Reporting

## Test Scenario 1: Generate SHAP Waterfall Plot
**Goal**: Verify SHAP logic produces a valid matplotlib figure for Streamlit.

1. **Setup**:
   ```python
   import shap
   import xgboost as xgb
   model = xgb.XGBClassifier().load_model("models/sense/audio_model.json")
   X_sample = ... # load sample
   ```
2. **Execute**:
   ```python
   from app import show_shap
   show_shap(model, X_sample, feature_names)
   ```
3. **Verify**:
   - Figure is rendered in Streamlit tab.
   - Background colors match PRISM dark theme.

## Test Scenario 2: Generate PDF Report
**Goal**: Verify a medical-grade PDF is generated in the root directory.

1. **Execute**:
   ```python
   from app import generate_pdf_report
   results = {
       "sense": {"disease_probs": {"TB": 0.85, "COVID": 0.1}},
       "causal": {"narrative": "Primary driver: Crowding Index..."},
       "interventions": [{"name": "nutritional_support", "cost": 0}]
   }
   pdf_path = generate_pdf_report(results, "DEMO-001")
   ```
2. **Verify**:
   - `PRISM_Report_DEMO-001.pdf` exists.
   - Contains header, primary diagnosis box, and intervention list.

## Test Scenario 3: Evaluate Model Performance
**Goal**: Get real accuracy and AUC-ROC numbers for the pitch deck.

1. **Execute**:
   ```bash
   uv run python scripts/evaluate_model.py
   ```
2. **Verify**:
   - Classification report printed to console.
   - AUC-ROC > 0.85 (target).
