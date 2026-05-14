# Data Model: Explainability & Reporting

## Entities

### 1. SHAPExplanation
- **values**: List[float] (SHAP values per feature)
- **base_value**: float (Expected value of model output)
- **data**: List[float] (Actual feature values)
- **feature_names**: List[str]

### 2. PDFReport
- **patient_id**: String
- **timestamp**: DateTime
- **primary_diagnosis**: String
- **primary_probability**: float
- **causal_narrative**: String
- **disease_probs**: Dict[str, float]
- **interventions**: List[Dict[str, Any]] (Top 3)

### 3. ModelPerformance
- **precision**: float
- **recall**: float
- **f1_score**: float
- **auc_roc**: float
- **report_text**: String (Raw classification report)

## Relationships
- **SHAPExplanation** is derived from a specific **InferenceResult** and the **XGBoostModel**.
- **PDFReport** consolidates data from **SENSE Layer**, **Reason Layer (Causal)**, and **Optimizer Layer**.
- **ModelPerformance** is calculated during validation against a ground-truth dataset.
