# Research: Explainability (SHAP) & Reporting (PDF)

## Decisions

### 1. Explainability Framework
- **Decision**: SHAP (SHapley Additive exPlanations) using `TreeExplainer`.
- **Rationale**: SHAP provides medically defensible feature attribution by assigning each feature an importance value for a specific prediction. `TreeExplainer` is highly optimized for XGBoost models.
- **Alternatives**: LIME (less stable), Permutation Importance (global only, not instance-specific).

### 2. PDF Generation Library
- **Decision**: ReportLab.
- **Rationale**: ReportLab is the industry standard for programmatic PDF generation in Python. It allows for precise control over layout, which is essential for professional medical reports. It is lightweight and has no external dependencies like wkhtmltopdf.
- **Alternatives**: FPDF (simpler but less powerful), WeasyPrint (requires HTML/CSS, heavier).

### 3. Performance Metrics
- **Decision**: Classification Report (Precision, Recall, F1) + AUC-ROC.
- **Rationale**: For medical diagnostics, sensitivity (recall) is critical for screening, while AUC-ROC measures the model's ability to distinguish between classes across all thresholds.
- **Multiclass**: Use `ovr` (One-vs-Rest) for AUC-ROC calculation as per common practice for diagnostic models.

## Best Practices
- **SHAP Visualization**: Use dark-themed plots (`#0a0f1e`, `#111827`) to match the PRISM UI aesthetic.
- **PDF Layout**: Include a clear header, primary diagnosis box with high-contrast color (Red for high risk), and a summary of all probabilities.
- **Performance Evaluation**: Use a dedicated test set (e.g., COUGHVID) to report "real" numbers rather than training performance.
