# Tasks: PRISM Layer 2 — REASON (Causal AI Engine)

**Branch**: `001-prism-multimodal-diagnostics` | **Date**: 2026-05-14
**Input**: `specs/001-prism-multimodal-diagnostics/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)
**Role**: Person 2 — Causal AI Engineer

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Parallelizable (different files, no dependency on incomplete tasks)
- **[Story]**: User story label [US1]–[US5] from spec.md
- All paths relative to `prism/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton, dependencies, configuration — blocking everything.

- [x] T001 Create directory structure: `layer2_reason/{data,causal_discovery,scm,counterfactuals,graphs,tests}/` with `__init__.py` files
- [x] T002 Add Layer 2 dependencies to `requirements.txt`: dowhy==0.11.1, tigramite==5.2.1.0, causal-learn==0.1.3.8, dice-ml==0.9, causalml==0.15.0, econml==0.15.1, pgmpy==0.1.25, shap==0.44.1, networkx==3.2.1
- [x] T003 [P] Create `configs/causal_config.yaml` with PCMCI params (tau_min, tau_max, pc_alpha), disease cohort ICD-10 definitions, biomarker itemid mappings, physiological bounds
- [x] T004 [P] Create `layer2_reason/tests/conftest.py` with synthetic patient fixture: 50-patient DataFrame with 12 biomarkers at 48h resolution, disease labels, demographics
- [x] T005 [P] Add `.gitignore` entries: `data/raw/`, `data/processed/`, `layer2_reason/scm_models/*.pkl`, `layer2_reason/vae_weights/`
- [x] T006 Create `scripts/download_nfhs.py` — DHS Program NFHS-5 download and extraction to `data/raw/nfhs5/`

**Checkpoint**: `pip install -r requirements.txt` succeeds; synthetic fixture importable

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Data pipeline and validated causal graphs — MUST complete before US2–US5 phases.

**⚠️ CRITICAL**: All later phases depend on processed data and committed graph files.

- [x] T007 Implement `layer2_reason/data/data_validator.py`: schema validation (required columns, physiological bounds table from data-model.md), missing-rate logging per biomarker, cohort-size assertions; raises `DataValidationError` with structured message
- [x] T008 Implement `layer2_reason/data/mimic_preprocessor.py`: load admissions/patients/labevents/chartevents/diagnoses_icd CSVs; extract 12 biomarker timeseries (itemids from causal_config.yaml); ICD-10 label extraction (TB A15–A19, Pneumonia J12–J18, Sepsis A40–A41, HF I50, Anemia D50–D64, Dengue A90–A91); missing value handling (linear interp <4h, ffill 4–12h, NaN >12h); filter ≥48h data with ≥5 readings; output `data/processed/mimic_patients.pkl`
- [x] T009 [P] Implement `layer2_reason/data/nfhs_preprocessor.py`: extract NFHS-5 fields (hv237, hml32, hb56, hb57, s103a–e, hv270, hv025, hv201, hv205, hv216, hv009); compute derived features (crowding_index, anemia_binary, tb_symptom_score); output `data/processed/nfhs_india.pkl`
- [x] T010 Implement `layer2_reason/data/feature_engineering.py`: lag features X_lag1–X_lag20 at 6h intervals; first differences; rolling 24h mean/std/max; StandardScaler per biomarker (save to `data/scalers/biomarker_scalers.pkl`); produce flat panel dataset `data/processed/panel_dataset.pkl`
- [x] T011 Implement `layer2_reason/causal_discovery/causal_graph_store.py`: `save_graph(disease, graph)`, `load_graph(disease) -> nx.DiGraph`, `get_parents(disease, node)`, `get_causal_path(source, target)`, `export_dot(disease) -> str`; JSON serialisation via `nx.node_link_data`
- [x] T012 Implement `layer2_reason/causal_discovery/graph_validator.py`: DAG-ness check (warn only); required-edges validation `[(malnutrition, tb_susceptibility), (low_hb, fatigue), (high_wbc, infection), (fever, infection)]`; forbidden-edges check `[(tb, malnutrition)]`; connectivity check (disease nodes reachable from ≥2 biomarkers); output `validation_report.json`
- [x] T013 Implement `layer2_reason/causal_discovery/pcmci_discoverer.py`: tigramite `pp.DataFrame` from panel dataset; `PCMCI(dataframe, ParCorr())`; `run_pcmci(tau_min=1, tau_max=20, pc_alpha=0.05)`; `run_mci` for final p-values; significant edges (p<0.05 AND |corr|>0.1); separate cohort runs for TB, Anemia, general; output `nx.DiGraph` per cohort; persist to `layer2_reason/graphs/`
- [x] T014 [P] Implement `layer2_reason/causal_discovery/fci_discoverer.py`: causal-learn `fci()` with `fisherz` on NFHS array; background knowledge (required edges via `BackgroundKnowledge`); parse PAG edge types (→, ↔, o→) as edge attributes; output annotated `nx.DiGraph`; persist `graphs/fci_nfhs_graph.json`
- [x] T015 Implement `layer2_reason/causal_discovery/discovery_pipeline.py`: orchestrate PCMCI → FCI → graph merge → validate → store; merge strategy: PCMCI edges with confirmed FCI direction = high-confidence, mark ambiguous; call `graph_validator` and log report
- [x] T016 Create `scripts/run_causal_discovery.py`: CLI entry point — accepts `--diseases`, `--tau-max`, `--panel`, `--output-dir`; runs `discovery_pipeline`; commit-ready graphs output
- [x] T017 Write `layer2_reason/tests/test_data_pipeline.py`: synthetic DataFrame fixtures only (no MIMIC); test mimic_preprocessor column output, label extraction, missing-value handling; test feature_engineering lag count, scaler persistence; test data_validator catches bad bounds
- [x] T018 Write `layer2_reason/tests/test_causal_discovery.py`: synthetic 3-variable known SCM (X→Y→Z); run PCMCI → assert X→Y and Y→Z recovered; assert forbidden reverse edge absent; test graph_store save/load round-trip; test graph_validator required-edge check

**Checkpoint**: `pytest layer2_reason/tests/test_data_pipeline.py layer2_reason/tests/test_causal_discovery.py` — all pass with synthetic fixtures. Discovery pipeline ready for real MIMIC data (gated on PhysioNet access).

---

## Phase 3: User Story 1 — Passive Biomarker Capture & Instant Diagnosis (P1) 🎯 MVP

**Goal**: `PRISMCausalEngine` accepts Layer 1 feature vector + disease probability → produces `CausalReport` with validated causal attributions. Core engine functional end-to-end.

**Independent Test**: Feed synthetic patient features with known high-malnutrition profile → `CausalReport` returns `causal_attributions` with `nutrition_score` as top contributor; `narrative` is non-empty deterministic string; processing < 200ms.

### Implementation

- [x] T019 [P] [US1] Implement `layer2_reason/data/feature_validator.py`: validate incoming Layer 1 feature dict against schema in `contracts/layer1_layer2_schema.md`; coerce out-of-range values to NaN with warning; raise `InsufficientFeaturesError` if <3 non-NaN features across ≥2 modalities; apply confidence-threshold masking (confidence < 0.4 → NaN for that modality's features)
- [x] T020 [US1] Implement `layer2_reason/scm/scm_builder.py`: for each node in causal graph fit `GradientBoostingRegressor(n_estimators=100, max_depth=3)` on disease-cohort panel data; fit Gaussian noise from residuals; persist `scm_models/{disease}_scm.pkl`; `LinearRegression` debug mode via `mode="debug"` flag; log R² per node
- [x] T021 [US1] Implement `layer2_reason/scm/causal_attribution.py`: for each causal parent of disease node estimate `attribution[cause] = P(disease|obs) − P(disease|do(cause=baseline))` via `intervention_engine`; normalise to sum 1.0; `functools.lru_cache` keyed on `(patient_hash, disease)`; return `CausalAttributions` dataclass
- [x] T022 [US1] Implement `layer2_reason/scm/intervention_engine.py`: `estimate_intervention_effect(patient_data, treatment_var, treatment_value, outcome_var, disease) -> InterventionResult`; build DoWhy `CausalModel` from stored DOT graph; `identify_effect(proceed_when_unidentifiable=True)`; `estimate_effect("backdoor.linear_regression", target_units="ate")`; `refute_estimate("random_common_cause")`; return `InterventionResult` dataclass (all fields from data-model.md)
- [x] T023 [US1] Implement `layer2_reason/scm/scm_pipeline.py`: `PRISMSCMPipeline` — `load(models_dir, disease)`, `analyze_patient(patient_features, disease_prob, disease) -> SCMResult`; pre-compute intervention catalog for supported diseases (TB, Anemia, Dengue, Heart) at init time
- [x] T024 [US1] Implement `layer2_reason/counterfactuals/explainer.py`: `PRISMExplainer.build_plain_language_narrative(disease, prob, attributions, top_intervention) -> str`; deterministic template — no LLM, no randomness; `explain(patient, disease, disease_prob) -> ExplanationBundle`
- [x] T025 [US1] Implement `layer2_reason/causal_engine.py`: `PRISMCausalEngine(disease, graphs_dir, models_dir)`; `full_causal_analysis(patient_features, disease_probability, top_k=3) -> CausalReport`; load graph + SCM at `__init__`; assemble `CausalReport` from attribution + intervention + narrative + DOT string; populate `processing_time_ms` and `warnings`
- [x] T026 [US1] Write `layer2_reason/tests/test_scm.py`: synthetic SCM-generated data; test `scm_builder` fits without error; test `causal_attribution` returns dict summing to 1.0; test `estimate_intervention_effect` returns positive `absolute_reduction` when removing high-risk factor; test narrative determinism (same input → identical string)
- [x] T027 [US1] Write `layer2_reason/tests/test_causal_engine.py` — performance test: instantiate engine with pre-built graph + model; run `full_causal_analysis` on 100 synthetic patients; assert mean time <200ms; assert all `CausalReport` fields populated with correct types

**Checkpoint**: `pytest layer2_reason/tests/test_scm.py layer2_reason/tests/test_causal_engine.py -k "performance or attribution or narrative"` — all pass. `PRISMCausalEngine` is the MVP deliverable for Month 3.

---

## Phase 4: User Story 2 — Causal Explanation of Diagnosis (P2)

**Goal**: Engine produces human-readable causal explanations with ≥2 contributors and ≥1 counterfactual, usable by non-clinical users.

**Independent Test**: Given a TB-positive profile with malnutrition + crowding, `CausalReport.causal_attributions` has ≥2 factors; `CausalReport.counterfactuals` has ≥1 entry; all terms in `narrative` are plain language (no acronyms except "TB").

### Implementation

- [x] T028 [P] [US2] Implement `layer2_reason/counterfactuals/dice_generator.py`: `generate_counterfactuals(patient, disease_model, n=5, actionable_features=[...]) -> List[CounterfactualExplanation]`; DiCE `method="genetic"`, `proximity_weight=1.5`, `diversity_weight=1.0`; `compute_feasibility(changes)` with hardcoded feature weights (nutrition=0.9, activity=0.8, bmi=0.7, water=0.6, smoking=0.5, crowding=0.2); `parse_dice_output` → `CounterfactualExplanation` dataclass; sort by `feasibility DESC`; handle DiCE failure gracefully (return `[]` + warning)
- [x] T029 [P] [US2] Implement `layer2_reason/counterfactuals/counterfactual_ranker.py`: composite rank score `0.5×feasibility + 0.3×impact + 0.2×(1/n_changes)`; filter: only CFs where disease prob drops below threshold; `rank_counterfactuals(cfs: List[CounterfactualExplanation]) -> List[CounterfactualExplanation]`
- [x] T030 [US2] Update `layer2_reason/causal_engine.py` `full_causal_analysis()`: integrate `dice_generator` call; pass top-k to `counterfactual_ranker`; populate `CausalReport.counterfactuals`; graceful degradation if DiCE fails (empty list, not crash)
- [x] T031 [US2] Extend `layer2_reason/counterfactuals/explainer.py`: expand narrative template to include top counterfactual scenario ("If {feature} improves from {current} to {cf_value}, probability drops from {prob:.0%} to {new_prob:.0%}."); add `get_plain_language_factor_name(feature_key) -> str` lookup table (maps `nutrition_score` → "nutritional status", `crowding_index` → "household crowding", etc.)
- [x] T032 [US2] Write `layer2_reason/tests/test_counterfactuals.py`: test `dice_generator` returns `List[CounterfactualExplanation]` with valid types; test `feasibility_score` in [0,1]; test `counterfactual_ranker` output is sorted correctly; test DiCE failure → empty list, no exception; test `n_features_changed` is minimal for proximity-weighted run

**Checkpoint**: `pytest layer2_reason/tests/test_counterfactuals.py` — all pass. `CausalReport` now includes full counterfactual set with ranked, plain-language explanations.

---

## Phase 5: User Story 3 — Health Trajectory Simulation (P2)

**Goal**: Layer 2 exposes intervention effects as structured data that Layer 3 (Digital Twin) uses as forcing functions on the Neural ODE.

**Independent Test**: `get_intervention_catalog("tb")` returns ≥3 `InterventionOption` objects each with `treatment_var`, `cost_free_scheme`, `estimated_reduction_pct`, `feasibility_score` populated.

### Implementation

- [x] T033 [P] [US3] Implement `layer2_reason/scm/intervention_catalog.py`: pre-computed `InterventionOption` list per disease (TB: nutrition, ventilation, BMI; Anemia: iron, diet; Heart: smoking, activity; Dengue: vector_control, hydration); include `cost_free_scheme` field from Ayushman Bharat/ICDS/RNTCP schemes; `get_catalog(disease) -> List[InterventionOption]`
- [x] T034 [US3] Expose `PRISMCausalEngine.get_intervention_catalog(disease) -> List[InterventionOption]` — loads from `intervention_catalog`; allows Layer 3 to query available interventions without running full analysis
- [x] T035 [US3] Add `InterventionResult.to_ode_forcing_fn() -> Dict` method: returns serialisable dict `{treatment_var, effect_magnitude, onset_delay_days, duration_days}` for Layer 3 Neural ODE integration; document schema in `contracts/causal_engine_api.md`
- [x] T036 [US3] Write integration test `tests/integration/test_layer2_layer3.py`: mock Layer 3 twin interface; `full_causal_analysis()` → extract `top_interventions[0].to_ode_forcing_fn()` → assert correct keys present and values in valid range

**Checkpoint**: `pytest tests/integration/test_layer2_layer3.py` — all pass. Layer 3 can query Layer 2's causal output to parameterise trajectory simulations.

---

## Phase 6: User Story 4 — Cost-Optimised Intervention Recommendations (P3)

**Goal**: Engine recommendations include cost, nearest facility, and expected health benefit — consumable by the API layer (Person 4).

**Independent Test**: For a TB-positive profile in rural Mangalore, `get_intervention_catalog("tb")` top-ranked item has `cost_free_scheme != "None"` and `estimated_reduction_pct > 0`.

### Implementation

- [x] T037 [P] [US4] Extend `InterventionOption` dataclass in `layer2_reason/scm/intervention_catalog.py`: add `cost_private_inr: int`, `qaly_gain_estimate: float`, `nearest_facility_query_key: str` (for Person 4's ABDM facility lookup); update all disease catalogs with Ayushman Bharat pricing data
- [x] T038 [US4] Implement `layer2_reason/scm/uncertainty_reducer.py`: `recommend_diagnostic_test(uncertainty_set: Dict[str, float], available_tests: List[str]) -> str`; compute expected information gain per test = `mutual_information(current_belief, expected_posterior_after_test)`; cost-adjusted: `info_gain / test_cost[test]`; return highest cost-adjusted IG test
- [x] T039 [US4] Update `PRISMCausalEngine.full_causal_analysis()`: when `disease_probability` is between 0.4–0.6 (uncertain), invoke `uncertainty_reducer.recommend_diagnostic_test()` and include recommendation in `CausalReport.top_interventions` as highest-priority item
- [x] T040 [US4] Write `layer2_reason/tests/test_scm.py` additions: test `recommend_diagnostic_test` returns a string from `available_tests`; test uncertain probability (0.5) triggers diagnostic recommendation as top intervention

**Checkpoint**: `pytest layer2_reason/tests/test_scm.py -k "uncertainty"` — passes. API layer (Person 4) can display cost-annotated recommendations.

---

## Phase 7: User Story 5 — Privacy-Preserving Hospital Network (P4)

**Goal**: Causal graphs can be updated from federated learning rounds without raw patient data leaving hospital nodes.

**Independent Test**: `update_causal_graph_from_aggregated_weights(delta_weights)` applies weight update and `graph_validator` still passes — no forbidden edges introduced.

### Implementation

- [x] T041 [P] [US5] Implement `layer2_reason/causal_discovery/federated_graph_updater.py`: `update_causal_graph_from_aggregated_weights(disease, delta_weights: Dict) -> CausalGraph`; apply differential-privacy-noised weight deltas to edge strengths; re-run `graph_validator` post-update; reject update if validator finds forbidden edges; log privacy budget consumed
- [x] T042 [US5] Expose `PRISMCausalEngine.apply_federated_update(delta_weights)` method: delegates to `federated_graph_updater`; reloads graph in-place without restart; logs model version bump
- [x] T043 [US5] Write `layer2_reason/tests/test_causal_discovery.py` additions: test `federated_graph_updater` with synthetic weight delta; assert graph still passes validator; assert forbidden edge not introduced even with adversarial delta; test privacy budget tracking

**Checkpoint**: `pytest layer2_reason/tests/test_causal_discovery.py -k "federated"` — passes. Ready for Person 4 (FL server) integration.

---

## Phase 8: Causal VAE (Novel Research Contribution)

**Goal**: Trained `CausalVAE` that learns disentangled latent disease factors — publishable arXiv contribution.

**Independent Test**: `CausalVAE.do_intervention(x, {0: 0.0})` returns reconstruction with shape `(batch, input_dim)`; loss decreases over 5 training steps on synthetic data; DAG penalty `h(A)` converges toward 0.

### Implementation

- [x] T044 [P] [US1] Implement `layer2_reason/counterfactuals/causal_vae.py`: `CausalVAE(input_dim=15, latent_dim=8, hidden_dim=128)`; encoder → per-factor (mu, logvar) ModuleList; `reparameterize`; learned lower-triangular `causal_mask` Parameter; `causal_forward(z_ind)` using `torch.linalg.solve`; `do_intervention(x, {idx: val})`; decoder; `forward` returning `(x_recon, mu, logvar, z_causal)`
- [x] T045 [P] [US1] Implement `causal_vae_loss(x_recon, x, mu, logvar, causal_mask, beta=4.0, lambda_dag=1.0)`: reconstruction MSE + β·KL + NOTEARS DAG penalty `h(A) = tr(e^{A∘A}) − d`
- [x] T046 Create `scripts/train_causal_vae.py`: CLI — `--panel`, `--latent-dim`, `--epochs`, `--beta`, `--output`; Adam lr=1e-3; log loss components per epoch; save best checkpoint by val loss; smoke-test mode `--max-patients 500 --epochs 5`
- [x] T047 Write `layer2_reason/tests/test_counterfactuals.py` additions: test `CausalVAE` forward pass output shapes; test loss decreases over 3 steps on synthetic 15-dim data; test `do_intervention` output shape; test DAG penalty `h(A)` is scalar ≥ 0

**Checkpoint**: `pytest layer2_reason/tests/test_counterfactuals.py -k "vae"` — all pass. Full training run in `scripts/train_causal_vae.py --epochs 5 --max-patients 500` completes without error.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [x] T048 [P] Add type hints and docstrings to all public functions in `layer2_reason/` (enforce with `mypy --strict` on public API surface)
- [x] T049 [P] Add structured logging (`logging` stdlib, not `print`) to all pipeline modules — log patient counts, timing, errors; no PHI in log messages
- [x] T050 Run full test suite: `pytest layer2_reason/tests/ -v --cov=layer2_reason --cov-report=term-missing`; target ≥80% coverage
- [x] T051 [P] Write `tests/integration/test_layer1_layer2.py`: simulate Layer 1 output dict (all 38 features from contract schema); feed to `PRISMCausalEngine`; assert `CausalReport` all fields populated; assert `processing_time_ms < 200`
- [x] T052 Validate `quickstart.md` commands against actual repo state — run each command, verify expected output matches documentation
- [x] T053 [P] Export `PRISMCausalEngine` interface summary to `contracts/causal_engine_api.md` — add `to_ode_forcing_fn()` schema and federated update method added in later phases
- [x] T054 Performance profiling: `cProfile` on `full_causal_analysis()` for 10 patients; identify top-3 slowest operations; add LRU cache or pre-computation where beneficial

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user story phases
- **Phase 3 (US1 — Core Engine)**: Depends on Phase 2 — primary MVP deliverable
- **Phase 4 (US2 — Explanations)**: Depends on Phase 3 (needs `PRISMCausalEngine`)/
- **Phase 5 (US3 — Trajectory Interface)**: Depends on Phase 3 (coordinate with Person 3)
- **Phase 6 (US4 — Cost Recommendations)**: Depends on Phase 3
- **Phase 7 (US5 — Federated)**: Depends on Phase 2 (graph store); coordinate with Person 4
- **Phase 8 (CausalVAE)**: Independent of US2–US5; can run in parallel from Phase 2 completion
- **Phase 9 (Polish)**: Depends on all desired phases complete

### Critical Path (MIMIC-IV gated)

```
Day 1:  Apply PhysioNet → Phase 1 (Setup) begins
Week 1: Phase 1 complete; NFHS download; synthetic data pipeline tested
Week 2: MIMIC access received → Phase 2 real data run begins
Month 2: Phase 2 complete; TB + Anemia graphs committed
Month 3: Phase 3 complete — PRISMCausalEngine MVP
Month 4: Phase 4 + Phase 8 in parallel
Month 5: Phase 5 + 6 + 7; full integration with other layers
Month 6: Phase 9 polish; clinical validation data feeds into graphs
```

### Parallel Opportunities Within Phases

**Phase 2**: T007, T009, T011, T012 can run in parallel (different files)
**Phase 3**: T019 (validator), T026 (tests), T027 (perf test) can run in parallel with implementation tasks
**Phase 4**: T028, T029 run in parallel (different files)
**Phase 8**: T044, T045 run in parallel

---

## Parallel Execution Examples

### Phase 2 Parallel Launch
```
Task: "T007 data_validator.py"
Task: "T009 nfhs_preprocessor.py"          [parallel with T007]
Task: "T011 causal_graph_store.py"         [parallel with T007, T009]
Task: "T012 graph_validator.py"            [parallel with T007, T009, T011]
```

### Phase 3 Parallel Launch (after T020–T023 complete)
```
Task: "T024 explainer.py"                  [parallel with T025]
Task: "T026 test_scm.py"                   [parallel with T024, T025]
```

---

## Implementation Strategy

### MVP First (Month 3 target)
1. Complete Phase 1 + Phase 2
2. Complete Phase 3 (`PRISMCausalEngine.full_causal_analysis()` working)
3. **STOP and VALIDATE**: `pytest layer2_reason/tests/ -k "attribution or performance or narrative"` — all pass
4. Hand off `CausalReport` schema to Person 3 (Digital Twin) and Person 4 (FastAPI)

### Incremental Delivery
- Month 3: Phase 3 → Core engine + causal attribution (US1)
- Month 4: Phase 4 + 8 → Counterfactuals + CausalVAE (US2 + research)
- Month 5: Phase 5 + 6 + 7 → Trajectory interface + cost catalog + federated (US3–US5)
- Month 6: Phase 9 → Polish, integration tests, clinical data update

---

## Task Count Summary

| Phase | Tasks | Parallelizable | User Story |
|-------|-------|----------------|------------|
| Phase 1: Setup | 6 | 3 | — |
| Phase 2: Foundational | 12 | 5 | — |
| Phase 3: US1 Core Engine | 9 | 3 | US1 |
| Phase 4: US2 Explanations | 5 | 2 | US2 |
| Phase 5: US3 Trajectory Interface | 4 | 1 | US3 |
| Phase 6: US4 Cost Recommendations | 4 | 1 | US4 |
| Phase 7: US5 Federated | 3 | 1 | US5 |
| Phase 8: CausalVAE | 4 | 2 | US1 (research) |
| Phase 9: Polish | 7 | 4 | — |
| **Total** | **54** | **22** | — |

---

## Notes

- [P] tasks target different files — safe to run in parallel
- MIMIC-IV access is the single external blocker; all synthetic-fixture tests pass without it
- `CausalReport` is the integration contract — do not change its field names without coordinating with Person 3 and Person 4
- Commit causal graphs (`layer2_reason/graphs/*.json`) after Phase 2 — they are the project's primary training artifact that all team members share
- No LLM anywhere in this layer — every output is deterministic and auditable
