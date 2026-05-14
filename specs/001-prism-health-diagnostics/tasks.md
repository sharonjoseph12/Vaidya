# Tasks: PRISM Layer 3+4 (Digital Twin & RL Optimizer)

**Input**: Design documents from `/specs/001-prism-health-diagnostics/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/twin_service.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story, focusing on the Deep Learning Engineer's scope (Layer 3 and Layer 4).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure for the deep learning environment.

- [x] T001 Create project structure `prism/layer3_twin`, `prism/layer4_rl`, `prism/data` per implementation plan
- [x] T002 Initialize Python environment and `requirements.txt` with `torchdiffeq`, `pytorch-lightning`, `stable-baselines3`
- [x] T003 [P] Create data download scripts in `prism/data/download_nhanes.py`
- [x] T004 [P] Setup Weights & Biases (W&B) logging configuration

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Latent ODE architecture that MUST be complete before specialized organ twins can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Implement `ODEFunc` (defining dx/dt) in `prism/layer3_twin/latent_ode/ode_func.py`
- [x] T006 Implement `ODERNNEncoder` (handling irregular time series) in `prism/layer3_twin/latent_ode/encoder.py`
- [x] T007 Implement `PatientLatentODE` (combining encoder and ODE solver) in `prism/layer3_twin/latent_ode/latent_ode_model.py`
- [x] T008 [P] Define `PatientLatentState` and `TrajectoryPrediction` data classes in `prism/layer3_twin/data_models.py`

**Checkpoint**: Core ODE foundation ready - specialized twin implementation (US3) can now begin.

---

## Phase 3: User Story 3 - Health Trajectory Projection (Priority: P3)

**Goal**: Simulate future health trajectories using the Digital Twin under different scenarios.

**Independent Test**: Can train the Metabolic Twin on NHANES data and accurately predict HbA1c trajectory (MAE < 0.5%).

### Implementation for User Story 3

- [x] T009 [P] [US3] Implement `CardiopulmonaryTwin` and `CardiopulmonaryDataModule` in `prism/layer3_twin/organ_twins/cardiopulmonary_twin.py`
- [x] T010 [P] [US3] Implement `MetabolicTwin` and `MetabolicDataModule` in `prism/layer3_twin/organ_twins/metabolic_twin.py`
- [x] T011 [P] [US3] Implement `InfectiousTwin` and `InfectiousDataModule` in `prism/layer3_twin/organ_twins/infectious_twin.py`
- [x] T012 [US3] Implement PyTorch Lightning training orchestrator in `prism/layer3_twin/trainer.py`
- [x] T013 [US3] Implement the `predict_trajectory` contract from `contracts/twin_service.md` in `prism/layer3_twin/api.py`

**Checkpoint**: At this point, the Digital Twin (Layer 3) should be fully functional, trainable, and independently testable.

---

## Phase 4: User Story 4 - Intervention Optimization (Priority: P4)

**Goal**: Recommend the most cost-effective intervention sequence using RL.

**Independent Test**: The PPO agent can interact with the `PatientHealthEnv` and converge to a policy that prioritizes high QALY / low cost actions.

### Implementation for User Story 4

- [x] T014 [P] [US4] Implement QALY calculation and Ayushman Bharat cost logic in `prism/layer4_rl/rewards.py`
- [x] T015 [US4] Implement `PatientHealthEnv` (Gymnasium environment wrapping the digital twin) in `prism/layer4_rl/env/patient_env.py`
- [x] T016 [US4] Implement PPO agent training script using `stable-baselines3` in `prism/layer4_rl/agents/ppo_agent.py`
- [x] T017 [US4] Implement the intervention recommendation API endpoint in `prism/layer4_rl/api.py`

**Checkpoint**: At this point, the RL Optimizer (Layer 4) is functional and can recommend actions based on twin simulations.

---

## Phase 5: User Story 2 - Causal Rationale (Priority: P2 - Integration)

**Goal**: Interventions must actively modify the Digital Twin's ODE dynamics (Causal Forcing Functions).

**Independent Test**: Running `simulate_intervention` modifies the trajectory appropriately compared to the baseline.

### Implementation for User Story 2

- [x] T018 [US2] Implement causal forcing function logic within the ODE solver in `prism/layer3_twin/causal/intervene.py`
- [x] T019 [US2] Implement the `simulate_intervention` contract from `contracts/twin_service.md` in `prism/layer3_twin/api.py`

**Checkpoint**: Layer 3 now fully supports counterfactual simulations driven by Layer 2's causal engine.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements, optimizations, and finalization for mobile deployment.

- [x] T020 [P] Export trained Latent ODE models to TFLite/ONNX in `prism/scripts/export_models.py`
- [x] T021 [P] Write unit tests for the ODE encoder and solver in `prism/tests/unit/test_latent_ode.py`
- [x] T022 Validate `quickstart.md` commands successfully train a toy model.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS US3.
- **User Story 3 (Phase 3)**: Depends on Foundational phase.
- **User Story 4 (Phase 4)**: Depends on User Story 3 (needs the twin environment to train the RL agent).
- **User Story 2 (Phase 5)**: Depends on User Story 3 (modifies the twin architecture).
- **Polish (Final Phase)**: Depends on all user stories.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- The three specialized organ twins (T009, T010, T011) can be implemented in parallel by different engineers once the Foundational Latent ODE architecture is complete.
- Reward logic (T014) can be implemented in parallel with the twin implementation (US3).

## Implementation Strategy

### Incremental Delivery for Layer 3+4

1. Complete Setup + Foundational ODE Architecture.
2. Add Metabolic Twin (US3) → Test trajectory prediction on NHANES → MVP Digital Twin.
3. Add RL Optimizer (US4) using the Metabolic Twin environment → Demo Intervention Optimizer.
4. Expand to Cardiopulmonary and Infectious Twins (US3).
5. Integrate Causal Forcing Functions (US2) for full counterfactual capability.
