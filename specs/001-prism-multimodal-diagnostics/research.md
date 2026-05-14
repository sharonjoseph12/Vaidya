# Research: PRISM Layer 2 — Causal AI Engine

**Feature**: `001-prism-multimodal-diagnostics` | **Phase**: 0 — Research
**Date**: 2026-05-14

---

## 1. Causal Discovery Algorithm Selection

### Decision: PCMCI for temporal data, FCI for cross-sectional

**Rationale**:
- Patient biomarker data is a time series (MIMIC-IV hourly readings). PCMCI correctly handles lagged dependencies and autocorrelation, which are fatal for naive PC algorithm application to time series.
- Clinical settings always have unmeasured confounders (genetics, socioeconomic background). FCI is the only constraint-based algorithm that remains correct under this assumption. PC assumes causal sufficiency (no latent confounders) — clinically unrealistic.
- FCI output is a PAG (Partial Ancestral Graph) — more conservative but honest about what can actually be identified.

**Alternatives considered**:
- **PC algorithm**: Rejected — assumes no latent variables, unacceptable for clinical data.
- **Granger causality**: Rejected — linear-only, VAR-based, no latent variable handling.
- **LiNGAM**: Rejected — assumes linear non-Gaussian noise; strong assumption for multi-disease data.
- **DYNOTEARS**: Considered — differentiable, but less interpretable than PCMCI for clinical validation.

**Implementation**: `tigramite>=5.2` for PCMCI; `causal-learn>=0.1.3.8` for FCI.

---

## 2. Independence Test Selection

### Decision: ParCorr for speed; CMIknn for nonlinear validation

**Rationale**:
- `ParCorr` (partial correlation with analytic significance) runs fast and is exact for Gaussian variables. Sufficient for development and linear-first hypothesis.
- `CMIknn` (conditional mutual information via k-nearest neighbours) is nonparametric — detects nonlinear dependencies. Required for publication-quality results and as validation that ParCorr didn't miss structure.
- Run ParCorr first (hours), validate with CMIknn on significant edges only (reduces runtime).

**Alternatives considered**:
- `GPDC` (Gaussian Process distance correlation): More powerful but extremely slow on large N.
- `RCoT` (randomised conditional correlation test): Faster nonparametric option — viable fallback.

---

## 3. SCM Functional Form

### Decision: GradientBoostingRegressor (production), LinearRegression (debug)

**Rationale**:
- Clinical relationships between biomarkers are nonlinear (e.g., hemoglobin–fatigue relationship has a threshold, not linear). GBM captures this without specifying the form.
- Linear SCM is provided as a fast debug/interpretability mode — readable coefficients for domain experts to validate.
- Gaussian Process regression was considered but rejected: too slow for inference (<200ms target) and doesn't scale to 12 disease nodes × 10 parents.

**Noise model**: Gaussian fitted to residuals (standard assumption; acceptable for continuous biomarkers after normalisation).

---

## 4. Do-Calculus Implementation

### Decision: DoWhy with backdoor linear regression estimator

**Rationale**:
- DoWhy is the de facto Python library for causal inference with automatic adjustment set identification, multiple estimators, and built-in refutation tests.
- Backdoor linear regression is fast, interpretable, and valid when the backdoor criterion is satisfied (which our validated DAGs ensure).
- `proceed_when_unidentifiable=True` with a logged warning handles edge cases — the estimate is still computed but flagged as potentially biased.

**Refutation strategy**:
- `random_common_cause`: Add a random variable — if effect changes significantly, estimate is spurious.
- `placebo_treatment_refuter`: Permute treatment — effect should disappear.
- Both tests run for every published intervention estimate.

**Alternatives considered**:
- `EconML` DoubleML: More powerful for heterogeneous treatment effects (HTE). Reserved for Phase 2 (heterogeneous patient subgroups, post-MVP).
- `CausalML` meta-learners (T-learner, S-learner): Useful for uplift modelling — noted for future personalisation features.

---

## 5. Counterfactual Method

### Decision: DiCE genetic algorithm

**Rationale**:
- DiCE (`method="genetic"`) produces **diverse** counterfactuals — multiple actionable paths, not just the nearest one. Clinically important: patients need options, not a single path.
- Proximity weight ensures minimal feature changes (clinically feasible).
- Genetic algorithm is more robust than gradient-based for mixed continuous/categorical features (smoking status is categorical).

**Feasibility scoring**: Custom scoring by feature mutability:
- `nutrition_score: 0.9` — India's ICDS scheme makes this accessible
- `activity_level: 0.8` — lifestyle intervention, moderate barrier
- `bmi: 0.7` — achievable via nutrition + activity
- `water_quality: 0.6` — government schemes available
- `smoking_status: 0.5` — addiction barrier is real
- `crowding_index: 0.2` — housing is nearly immutable in rural India

**Alternatives considered**:
- `DICE gradient` method: Faster but gradient-based — doesn't handle categorical features cleanly.
- `Wachter et al.` (nearest CF): Single CF, not diverse. Rejected.
- `FACE` (feasible actionable CF): Promising but not in a stable Python library.

---

## 6. Causal VAE

### Decision: NOTEARS DAG constraint in latent space (Yang et al. 2021 CausalVAE)

**Rationale**:
- Standard VAE assumes independent latent factors — wrong for health biomarkers (malnutrition causes low hemoglobin causes fatigue — these are causally structured).
- CausalVAE encodes a DAG structure in the latent space: each factor can causally influence downstream factors. The NOTEARS constraint `h(A) = tr(e^{A∘A}) − d = 0` makes DAG-ness differentiable.
- This is the **publishable novelty**: applying Causal VAEs to multimodal health biomarkers has not been done in the Indian clinical population context.

**Architecture choices**:
- `latent_dim=8`: Enough factors for 6 major disease dimensions (TB susceptibility, nutritional status, immune function, cardiac load, respiratory function, metabolic state) + 2 residual.
- Lower-triangular `causal_mask` initialisation: Ensures DAG at initialisation (avoids early training collapse from acyclicity penalty).
- β=4.0 (disentanglement weight): β-VAE style — promotes independent encoding before causal flow.

**Training data**: MIMIC-IV panel dataset (processed); batch_size=256; Adam lr=1e-3; 200 epochs.

---

## 7. Narrative Generation

### Decision: Deterministic template strings

**Rationale**:
- LLMs introduce non-determinism, hallucination risk, latency, and internet dependency — all unacceptable for a clinical tool.
- Template strings are auditable: clinicians and regulators can inspect exactly what logic produces any given output.
- Templates are parameterised by attribution percentages and intervention effects — they are concise and accurate.

Example template:
```
"{disease} probability: {prob:.0%}. Primary driver: {top_cause} 
({top_weight:.0%} contribution). Highest-impact action: {top_intervention} 
reduces probability by {reduction:.0f}% (from {prob:.0%} to {new_prob:.0%})."
```

---

## 8. Data Access

| Dataset | Access Method | Timeline |
|---------|--------------|----------|
| MIMIC-IV | PhysioNet credentialing (apply Day 1) | ~2 weeks approval |
| NFHS-5 | DHS Program data request (free) | ~1 week |
| Coswara (IISc) | Direct download | Immediate |
| KMC Mangalore data | Ethics committee approval (Month 1) | Month 2–3 |

**Critical path**: MIMIC-IV access. Apply on Day 1 — 2-week delay blocks Phase 2.2 start.
Fallback: use NHANES + synthetic data to validate pipeline structure while waiting.

---

## 9. Performance Analysis

| Operation | Expected Time | Mitigation |
|-----------|--------------|------------|
| PCMCI discovery (1k patients) | 2–6 hours (one-time) | Run on Colab Pro A100; save graph |
| SCM fitting per disease | 5–20 min (one-time) | Cache `scm_models/` |
| `estimate_intervention_effect()` | 50–150ms | LRU cache for repeated profiles |
| `generate_counterfactuals()` (n=5) | 100–500ms | Pre-filter actionable features |
| `full_causal_analysis()` end-to-end | Target <200ms | Graph + SCM pre-loaded at startup |

All training is one-time (cloud). Inference is CPU-only on-device.
