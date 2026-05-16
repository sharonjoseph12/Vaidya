# Plan: Explainability & Professional Reporting (PRISM)

Integrate SHAP for clinical explainability and ReportLab for professional PDF diagnostic reports.

## Technical Context
- **Explainability**: `shap`, `matplotlib`.
- **Reporting**: `reportlab`.
- **Evaluation**: `scikit-learn`.
- **Integration**: Streamlit (`app.py`).

## Constitution Check
- **Explainability**: SHAP provides "local" explanations per patient, increasing clinical trust.
- **Reporting**: PDF reports ensure that results are portable and can be shared with specialists or stored in ABHA health lockers.
- **Evaluation**: Real-world metrics (AUC-ROC) provide empirical proof of model robustness.

## Proposed Changes

### UI & Reporting Layer

#### [MODIFY] [app.py](file:///c:/Users/Sharon/OneDrive/Desktop/Vaidya/app.py)
- Import `shap`, `reportlab`, `matplotlib`.
- Implement `show_shap()`: Renders waterfall plots with PRISM dark theme.
- Implement `generate_pdf_report()`: Creates medical-grade PDF using ReportLab canvas.
- Integrate into `tab1`:
    - Add "Why this prediction?" subheader with SHAP plot.
    - Add "Download PDF Report" button.

---

### Evaluation Layer

#### [NEW] [evaluate_model.py](file:///c:/Users/Sharon/OneDrive/Desktop/Vaidya/scripts/evaluate_model.py)
- Load trained XGBoost model and test dataset.
- Compute precision, recall, F1, and AUC-ROC.
- Print classification report for pitch deck screenshot.

## Verification Plan

### Automated Tests
- Run `evaluate_model.py` and verify metrics are printed.
- Trigger PDF generation via smoke test script and check file existence.

### Manual Verification
- Open Streamlit app, perform an assessment, and verify SHAP plot appears.
- Download the generated PDF and verify layout and data accuracy.
