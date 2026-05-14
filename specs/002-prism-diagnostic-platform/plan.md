# Implementation Plan: PRISM Diagnostic Platform

**Branch**: `002-prism-diagnostic-platform` | **Date**: 2026-05-14 | **Spec**: [Link](./spec.md)

**Input**: Feature specification from `/specs/002-prism-diagnostic-platform/spec.md` and user constraint: "If any service is broken → return realistic hardcoded response for the DEMO PATIENT ONLY"

## Summary

PRISM is a smartphone-based, offline-capable, multimodal AI diagnostic platform that detects diseases from passive biomarker observation. The platform architecture consists of a Next.js 14 frontend and a FastAPI backend with Celery workers for asynchronous processing. To ensure robustness during demonstrations, a fallback mechanism is implemented: if any underlying inference service is broken, a realistic hardcoded response is returned for the demo patient.

## Technical Context

**Language/Version**: Python 3.11 (Backend), TypeScript/Node.js (Frontend)

**Primary Dependencies**: FastAPI, Celery, Redis, Next.js 14, Tailwind CSS, Recharts, D3.js, Flower (Federated Learning)

**Storage**: Supabase (PostgreSQL)

**Testing**: Pytest (Backend)

**Target Platform**: Android/Web Browsers (Frontend), Linux/Docker (Backend)

**Project Type**: Web Service + Web Application

**Performance Goals**: <90 seconds total processing time for 30s scan

**Constraints**: Offline-capable for core functionality; fallback hardcoded responses for demo scenarios.

**Scale/Scope**: 4 core layers (SENSE, REASON, PROJECT, ACT), ABDM integration, FL support.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] Clear separation of concerns between Next.js frontend and FastAPI backend.
- [x] No raw media stored persistently.
- [x] Fallback mechanism implemented gracefully as per user requirement.

## Project Structure

### Documentation (this feature)

```text
specs/002-prism-diagnostic-platform/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
prism/
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── workers/
│   ├── models/
│   ├── db/
│   ├── federated/
│   ├── utils/
│   └── tests/
└── frontend/
    ├── app/
    ├── components/
    │   ├── scan/
    │   ├── results/
    │   ├── abdm/
    │   └── dashboard/
    ├── lib/
    ├── public/
    └── package.json
```

**Structure Decision**: The project uses a monorepo approach with separate `frontend` (Next.js) and `backend` (FastAPI) directories under the `prism/` root.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Mock Demo Data | Prevent demo failures | Required to ensure continuous flow during presentations if a complex ML service times out. |
