# Implementation Plan: PRISM Layer 3+4 (Digital Twin & RL Optimizer)

**Branch**: `001-prism-health-diagnostics` | **Date**: 2026-05-14 | **Spec**: [spec.md](file:///C:/Users/siddharth/Desktop/Vaidya/specs/001-prism-health-diagnostics/spec.md)

**Input**: Feature specification from `/specs/001-prism-health-diagnostics/spec.md`

**Note**: This plan focuses on **Person 3: Deep Learning Engineer** responsibilities: Layer 3 (Neural ODE Digital Twin) and Layer 4 (RL Intervention Optimizer).

## Summary

This feature implements the trajectory projection and intervention optimization components of PRISM. We will use **Latent Ordinary Differential Equations (Latent ODEs)** to model continuous-time patient physiology from irregular observations (cardiopulmonary, metabolic, and infectious twins). For intervention optimization, we will implement a **Reinforcement Learning (RL) agent using PPO** that recommends clinical actions by maximizing QALY gains relative to costs from the Ayushman Bharat database.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.11

**Primary Dependencies**: `torchdiffeq==0.2.3`, `torchsde==0.2.6`, `pytorch-lightning==2.1.3`, `wandb==0.16.6`, `einops==0.7.0`, `stable-baselines3`, `gymnasium`

**Storage**: Checkpoints (PyTorch), Patient data (PostgreSQL/Parquet for training)

**Testing**: `pytest`, `torch.testing`

**Target Platform**: Cloud (Training), Android (TFLite Inference)

**Project Type**: Deep Learning Module

**Performance Goals**: Latent ODE inference < 200ms per patient

**Constraints**: Offline-capable inference, handle irregular time intervals

**Scale/Scope**: 3 specialized organ twins, 15-action RL optimizer space

## Constitution Check

- [ ] **Modularity**: Layer 3 and Layer 4 must be decoupled to allow independent twin updates.
- [ ] **Explainability**: RL policy must provide a rationale based on QALY/cost.
- [ ] **Efficiency**: Adjoint method must be used for ODE backprop to save memory.
- [ ] **Reproducibility**: All training runs MUST be logged to Weights & Biases (W&B).

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--

```text
prism/
├── layer3_twin/
│   ├── latent_ode/      # Core ODE components (encoder, func, solver)
│   ├── organ_twins/     # Specialized models (cardio, metabolic, infectious)
│   ├── causal/          # Integration with Layer 2 causal graphs
│   └── trainer.py       # PL-based training orchestrator
├── layer4_rl/
│   ├── env/             # PatientHealthEnv (Gymnasium)
│   ├── agents/          # PPO policy and optimizer
│   └── rewards.py       # QALY and Ayushman Bharat cost logic
├── data/                # MIMIC-IV, NHANES preprocessing scripts
└── tests/
    ├── unit/
    └── integration/
```

**Structure Decision**: Using the `prism/` root structure as requested, organized by functional layers (3 and 4) with a dedicated shared data processing module.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
