# Tasks: PRISM Platform (Person 4 — Platform Engineer)

**Input**: Design documents from `specs/002-prism-diagnostic-platform/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize project structure, dependencies, and tooling for backend + frontend + Android.

- [x] T001 Create full project directory structure per plan.md (prism/backend/, prism/frontend/, prism/android_app/, prism/tests/, prism/configs/)
- [x] T002 Initialize Python backend with virtual environment and install dependencies (FastAPI, Uvicorn, Celery, Redis, httpx, python-jose, fhir.resources, supabase, cryptography, pydantic) in prism/backend/requirements.txt
- [ ] T003 [P] Initialize Next.js 14 project with App Router, Tailwind CSS, shadcn/ui, Recharts, D3.js, Framer Motion, Zustand in prism/frontend/package.json
- [x] T004 [P] Create environment configuration with Pydantic BaseSettings in prism/backend/config.py (.env support for SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, REDIS_URL, ABDM_CLIENT_ID, ABDM_CLIENT_SECRET, ENCRYPTION_KEY)
- [x] T005 [P] Create docker-compose.yml at prism/docker-compose.yml for backend + Redis services
- [x] T006 [P] Create .env.example files for both backend (prism/backend/.env.example) and frontend (prism/frontend/.env.local.example)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T007 Create Supabase database schema with all tables (patients, diagnostic_sessions, clinical_reports, fl_rounds, hospital_nodes, audit_log) and RLS policies in prism/backend/db/schema.sql
- [x] T008 Implement Supabase client singleton with connection pooling and error handling in prism/backend/db/supabase_client.py
- [x] T009 [P] Implement AES-256 field-level encryption utilities (encrypt_demographics, decrypt_demographics, generate_key) in prism/backend/utils/encryption.py
- [x] T010 [P] Implement JWT authentication middleware using Supabase Auth token validation in prism/backend/utils/auth.py
- [x] T011 [P] Configure structured JSON logging with audit trail support in prism/backend/utils/logging_config.py
- [x] T012 Implement base Pydantic schemas for Patient (PatientCreate, PatientResponse, PatientUpdate) in prism/backend/models/patient.py
- [x] T013 [P] Implement Pydantic schemas for DiagnosticResult (SenseResult, CausalResult, TwinTrajectory, InterventionPlan, FullDiagnosticResult) matching data-model.md JSONB schemas in prism/backend/models/diagnostic_result.py
- [x] T014 [P] Implement Pydantic schemas for ClinicalReport and ABDM types (ABHAProfile, ConsentRequest, HealthRecord) in prism/backend/models/report.py and prism/backend/models/abdm.py
- [x] T015 Create FastAPI application entry point with CORS middleware, router registration, health check endpoint, and exception handlers in prism/backend/main.py
- [x] T016 Configure Celery application with Redis broker and result backend in prism/backend/workers/celery_tasks.py
- [x] T017 Implement Patient CRUD endpoints (POST /patients, GET /patients/{id}, GET /patients with pagination) with encryption/decryption in prism/backend/routers/patients.py
- [x] T018 [P] Setup Next.js root layout with dark theme (background #0a0f1e), Inter + JetBrains Mono fonts, and global CSS design tokens in prism/frontend/app/layout.tsx and prism/frontend/styles/globals.css
- [x] T019 [P] Configure Tailwind with PRISM custom color palette (electric blue #3b82f6, surgical white #f8fafc, glassmorphism utilities) in prism/frontend/tailwind.config.ts
- [x] T020 [P] Create TypeScript type definitions matching all backend Pydantic schemas in prism/frontend/lib/types.ts
- [x] T021 [P] Implement API client with fetch wrappers, error handling, SSE support, and auth token management in prism/frontend/lib/api.ts
- [x] T022 [P] Create utility functions (color scales for disease probabilities, chart formatting helpers, date formatting) in prism/frontend/lib/utils.ts
- [x] T023 [P] Setup pytest configuration with Supabase mock fixtures and synthetic test patient data in prism/backend/tests/conftest.py

**Checkpoint**: Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 — Passive Health Scan (Priority: P1) 🎯 MVP

**Goal**: Build the scan capture interface (camera + audio), connect to backend analysis pipeline, and display preliminary results — enabling on-device passive health assessment.

**Independent Test**: Perform a 30-second scan from the frontend, verify audio/video is uploaded to backend, Celery task is queued, and SSE progress stream delivers stage updates to the UI.

### Implementation for User Story 1

- [x] T024 [US1] Implement diagnostics analysis endpoint (POST /diagnostics/analyze) accepting multipart audio + video + patient_features, saving to Supabase Storage, and queuing Celery task in prism/backend/routers/diagnostics.py
- [x] T025 [US1] Implement diagnostics results endpoint (GET /diagnostics/results/{session_id}) returning full DiagnosticResult from Supabase in prism/backend/routers/diagnostics.py
- [x] T026 [US1] Implement SSE streaming endpoint (GET /diagnostics/stream/{session_id}) with EventSourceResponse for real-time pipeline progress (QUEUED→SENSING→REASONING→PROJECTING→OPTIMIZING→COMPLETE) in prism/backend/routers/diagnostics.py
- [x] T027 [US1] Implement inference orchestration service that chains Layer 1→2→3→4 processing, updates session status at each stage, and stores results in prism/backend/services/inference_service.py
- [x] T027b [US1] Implement demo fallback logic (DEMO_PATIENT_RESULT) for broken inference services based on session/patient ID in prism/backend/services/inference_service.py
- [x] T028 [US1] Implement Celery async task (run_prism_analysis) that calls inference_service and handles errors/retries in prism/backend/workers/celery_tasks.py
- [x] T029 [P] [US1] Build CameraCapture component with MediaDevices API, live camera feed, face detection indicator (green/red ring), scan quality progress bar, 30-second countdown, and state machine (IDLE→DETECTING_FACE→SCANNING→COMPLETE→ERROR) in prism/frontend/components/scan/CameraCapture.tsx
- [x] T030 [P] [US1] Build AudioCapture component with MediaRecorder API, real-time waveform visualization, recording status indicator, and audio level meter in prism/frontend/components/scan/AudioCapture.tsx
- [x] T031 [US1] Build ScanProgress component showing animated progress ring with stage indicators (Sensing, Reasoning, Projecting, Optimizing) driven by SSE events in prism/frontend/components/scan/ScanProgress.tsx
- [x] T032 [US1] Build live scan page integrating CameraCapture + AudioCapture + ScanProgress, handling file uploads via API client, and subscribing to SSE stream in prism/frontend/app/scan/page.tsx
- [x] T033 [US1] Build DiseaseProbabilityCard component displaying disease name, probability bar, trend indicator, confidence interval, and color-coded risk level in prism/frontend/components/results/DiseaseProbabilityCard.tsx
- [x] T034 [US1] Build UncertaintyBands component visualizing conformal prediction intervals as stacked horizontal bars per disease in prism/frontend/components/results/UncertaintyBands.tsx
- [x] T035 [US1] Build patient detail page (shell) with header (patient ID, scan date, risk score), disease probability grid using DiseaseProbabilityCard, and uncertainty visualization in prism/frontend/app/patient/[id]/page.tsx

**Checkpoint**: Full scan → upload → process → stream → display flow is functional. MVP complete.

---

## Phase 4: User Story 2 — Causal Diagnosis Explanation (Priority: P2)

**Goal**: Display causal attribution breakdowns and counterfactual scenarios on the clinical dashboard, making diagnoses explainable.

**Independent Test**: View a completed session's patient detail page and verify the causal attribution pie chart, causal graph visualization, and counterfactual cards render correctly with data from the backend.

### Implementation for User Story 2

- [x] T036 [US2] Build CausalGraphViz component using D3.js force-directed simulation with disease nodes (red), biomarker nodes (blue), risk factor nodes (orange), directed causal arrows with thickness proportional to effect strength, hover tooltips (edge weight + p-value), click-to-highlight causal paths, and animated node entrance in prism/frontend/components/results/CausalGraphViz.tsx
- [x] T037 [US2] Build CausalAttributionChart component displaying a horizontal bar chart of causal factor contributions (percentage weights summing to 100%) with color-coded bars and factor labels in prism/frontend/components/results/CausalAttributionChart.tsx
- [x] T038 [US2] Build CounterfactualCard component showing "what-if" scenarios: original value → changed value, original probability → new probability, feasibility score badge, and number of factors changed in prism/frontend/components/results/CounterfactualCard.tsx
- [x] T039 [US2] Integrate CausalGraphViz, CausalAttributionChart, CounterfactualCard, and narrative explanation section into the patient detail page (causal analysis section) in prism/frontend/app/patient/[id]/page.tsx

**Checkpoint**: Causal explanations are fully visualized. Diagnosis is explainable.

---

## Phase 5: User Story 3 — Health Trajectory Simulation (Priority: P3)

**Goal**: Display digital twin trajectory charts showing disease progression with and without intervention, including confidence bands and interactive intervention toggling.

**Independent Test**: View a patient's trajectory chart showing dual trajectories (baseline vs intervention), confidence shading, "today" marker, and critical threshold annotations.

### Implementation for User Story 3

- [x] T040 [US3] Build TrajectoryChart component using Recharts ComposedChart with: current trajectory line (red dashed), intervention trajectory line (green solid), confidence bands as gray shaded Area, vertical "today" line, vertical "intervention point" line, critical threshold annotation, animated line draw-in, responsive container, dark theme colors (#0a0f1e bg, #22c55e/#ef4444 lines, rgba(100,100,255,0.15) confidence band) in prism/frontend/components/results/TrajectoryChart.tsx
- [x] T041 [US3] Build TrajectoryControls component allowing users to toggle between different intervention scenarios (dropdown), adjust prediction horizon (6/12/18 months slider), and show/hide confidence bands in prism/frontend/components/results/TrajectoryControls.tsx
- [x] T042 [US3] Build DigitalTwinSummary component showing key metrics: months-to-critical (without intervention), months-to-critical (with intervention), selected twin model version, and biomarker trend sparklines in prism/frontend/components/results/DigitalTwinSummary.tsx
- [x] T043 [US3] Integrate TrajectoryChart, TrajectoryControls, and DigitalTwinSummary into the patient detail page (trajectory section) in prism/frontend/app/patient/[id]/page.tsx

**Checkpoint**: Trajectory visualization is fully interactive. Prognostic capability visible.

---

## Phase 6: User Story 4 — Intervention Recommendation (Priority: P4)

**Goal**: Display ranked intervention plans with costs, government scheme availability, expected outcomes, nearest facilities, and Pareto-optimal trade-off options.

**Independent Test**: View a patient's intervention plan showing ranked options with ₹0 FREE badges for government schemes, cost-per-QALY metrics, and nearest facility information.

### Implementation for User Story 4

- [x] T044 [US4] Build InterventionPlan component displaying ranked intervention cards with: intervention name, description, cost (with "₹0 FREE" badge for govt schemes), expected disease probability reduction, QALY gain, time to effect, side effect risk, nearest facility (name + distance), and government scheme label (AB-PMJAY, DOTS, ICDS, NRHM) in prism/frontend/components/results/InterventionPlan.tsx
- [x] T045 [US4] Build ParetoChart component visualizing cost vs health outcome trade-offs as a scatter plot with Pareto frontier line, labeled options (Minimum cost / Maximum QALY / Balanced), and interactive point selection in prism/frontend/components/results/ParetoChart.tsx
- [x] T046 [US4] Build ActiveUncertaintyReduction component showing the single diagnostic test that would most reduce uncertainty, with cost, expected information gain percentage, and rationale in prism/frontend/components/results/ActiveUncertaintyReduction.tsx
- [x] T047 [US4] Integrate InterventionPlan, ParetoChart, and ActiveUncertaintyReduction into the patient detail page (intervention section) in prism/frontend/app/patient/[id]/page.tsx

**Checkpoint**: Interventions are actionable. Full diagnostic report is viewable.

---

## Phase 7: User Story 5 — Health Record Integration (Priority: P5)

**Goal**: Enable ABDM/ABHA integration for fetching patient history and pushing diagnostic reports to the national health stack.

**Independent Test**: Using ABDM sandbox, verify ABHA ID, fetch test patient records, and push a PRISM diagnostic report back to the health locker.

### Implementation for User Story 5

- [x] T048 [US5] Implement ABDMService class with authentication (client credentials flow, token auto-refresh), ABHA verification, consent request creation, consent polling, health information fetch, and FHIR R4 bundle parsing in prism/backend/services/abdm_service.py
- [x] T049 [US5] Implement FHIR R4 DiagnosticReport builder that converts PRISM results to valid FHIR resources (DiagnosticReport + Observations with LOINC codes) and push-to-ABDM method in prism/backend/services/abdm_service.py
- [x] T050 [US5] Implement report generation service that builds PDF clinical reports and FHIR JSON from diagnostic session data in prism/backend/services/report_service.py
- [x] T051 [US5] Implement ABDM router endpoints: POST /abdm/verify/{abha_id}, POST /abdm/fetch-history, POST /abdm/push-report in prism/backend/routers/abdm.py
- [x] T052 [P] [US5] Build ABHAVerification component with ABHA ID input, verification status indicator, and patient profile preview in prism/frontend/components/abdm/ABHAVerification.tsx
- [x] T053 [P] [US5] Build HealthHistoryTimeline component displaying fetched historical records as a timeline with record type icons, dates, and findings in prism/frontend/components/abdm/HealthHistoryTimeline.tsx
- [x] T054 [US5] Build new patient registration page with ABHA verification, consent capture, demographics form, and health history fetch in prism/frontend/app/patient/new/page.tsx
- [x] T055 [US5] Add PDF report download button and ABDM push button with status feedback to the patient detail page in prism/frontend/app/patient/[id]/page.tsx

**Checkpoint**: ABDM integration round-trip is functional. Health records enrich assessment.

---

## Phase 8: User Story 6 — Privacy-Preserving Collaborative Learning (Priority: P6)

**Goal**: Implement Flower federated learning server with differential privacy and hospital client, with management endpoints and monitoring dashboard.

**Independent Test**: Simulate 2 hospital nodes training locally, verify aggregated model improves over rounds, and confirm no raw data is transmitted (only weight updates + DP noise).

### Implementation for User Story 6

- [x] T056 [US6] Implement PRISMFederatedStrategy (custom FedAvg) with differential privacy noise addition (Gaussian mechanism, ε=1.0, δ=1e-5), client quality filtering (reject loss > 3× median), and round metrics logging in prism/backend/federated/fl_server.py
- [x] T057 [US6] Implement differential privacy utilities: noise calibration, sensitivity calculation, privacy budget tracking, gradient clipping helpers in prism/backend/federated/dp_utils.py
- [x] T058 [US6] Implement PRISMHospitalClient (NumPyClient) with local training, gradient clipping (L2 norm ≤ 1.0), and metrics reporting in prism/backend/federated/fl_client.py
- [x] T059 [US6] Implement FL orchestrator service for starting/stopping FL server, registering nodes, and tracking rounds in prism/backend/services/fl_orchestrator.py
- [x] T060 [US6] Implement federated learning router endpoints: GET /federated/status, POST /federated/register-node, GET /federated/rounds in prism/backend/routers/federated.py
- [x] T061 [P] [US6] Build FederatedDashboard component showing FL server status, current round, active nodes, cumulative privacy budget, and per-round accuracy chart in prism/frontend/components/federated/FederatedDashboard.tsx
- [x] T062 [US6] Add federated learning status section to the main dashboard page in prism/frontend/app/dashboard/page.tsx

**Checkpoint**: FL infrastructure is operational. Privacy-preserving learning is demonstrable.

---

## Phase 9: Dashboard & Navigation (Cross-Story Integration)

**Purpose**: Build the main dashboard, navigation, and landing page that tie all user stories together.

- [x] T063 Build dashboard sidebar layout with navigation links (Dashboard, New Scan, Patients, FL Status), PRISM logo, and user profile in prism/frontend/app/dashboard/layout.tsx
- [x] T064 Build PatientQueue component displaying active patients list with status badges (scanning, complete, validated), search/filter, and click-to-navigate in prism/frontend/components/dashboard/PatientQueue.tsx
- [x] T065 [P] Build StatsOverview component showing aggregate cards: total scans today, diseases detected, average confidence, active FL nodes in prism/frontend/components/dashboard/StatsOverview.tsx
- [x] T066 Build main dashboard page integrating StatsOverview + PatientQueue + recent activity feed in prism/frontend/app/dashboard/page.tsx
- [x] T067 Build landing/login page with Supabase Auth integration (email/password), PRISM branding, and redirect to dashboard in prism/frontend/app/page.tsx

**Checkpoint**: Full navigation and dashboard are operational.

---

## Phase 10: Android Integration Module

**Purpose**: Create Android module specification and integration code for on-device TFLite inference.

- [x] T068 Create PRISMModule.kt with TFLite Interpreter initialization for all 4 models (cough_classifier, rppg_processor, visual_classifier, fusion_model), GPU delegate configuration, and lifecycle management in prism/android_app/app/src/main/java/com/prism/PRISMModule.kt
- [x] T069 [P] Create AudioAnalyzer.kt with audio preprocessing (22050 Hz resampling, mel spectrogram computation) and TFLite inference pipeline in prism/android_app/app/src/main/java/com/prism/AudioAnalyzer.kt
- [x] T070 [P] Create VideoAnalyzer.kt with CameraX frame capture, MediaPipe face mesh, rPPG signal extraction, and visual biomarker TFLite inference in prism/android_app/app/src/main/java/com/prism/VideoAnalyzer.kt
- [x] T071 Create FusionRunner.kt implementing on-device multi-modal fusion via TFLite, combining audio + visual + rPPG outputs in prism/android_app/app/src/main/java/com/prism/FusionRunner.kt
- [x] T072 Create ApiClient.kt with Retrofit client for backend API (online mode), offline fallback returning sense-only results, and network availability detection in prism/android_app/app/src/main/java/com/prism/ApiClient.kt
- [x] T073 Create Android Integration Spec README documenting TFLite model input/output tensor shapes, preprocessing requirements, and deployment pipeline for Person 1 in prism/android_app/README.md

**Checkpoint**: Android integration module is specified and scaffolded.

---

## Phase 11: End-to-End Integration & Polish

**Purpose**: Integration tests, cross-cutting concerns, and final polish.

- [x] T074 Write end-to-end integration test: synthetic TB patient → full pipeline → correct diagnosis with assertions on all 4 layer outputs in prism/tests/integration/test_end_to_end.py
- [x] T075 [P] Write offline mode test: Layer 1 only processing without network, verifying sense_result exists and causal/twin/RL results are null in prism/tests/integration/test_offline_mode.py
- [x] T076 [P] Write ABDM sandbox integration test: verify ABHA → fetch records → push report round-trip in prism/tests/integration/test_abdm_sandbox.py
- [x] T077 [P] Write FL simulation test: 2-node round, verify model doesn't degrade > 5%, verify no raw data transmitted in prism/tests/integration/test_fl_round.py
- [x] T078 [P] Write response time test: full pipeline < 3 seconds on server in prism/tests/integration/test_performance.py
- [x] T079 Create comprehensive README.md with project overview, architecture diagram, quickstart instructions, and team integration protocol in prism/README.md
- [x] T080 [P] Add Framer Motion page transitions between dashboard/scan/patient routes in prism/frontend/app/dashboard/layout.tsx
- [x] T081 [P] Add loading skeletons and error boundary components for all async data fetching in prism/frontend/components/ui/LoadingSkeleton.tsx
- [x] T082 Run quickstart.md validation — verify backend starts, frontend connects, and basic scan flow works end-to-end
- [x] T083 Security hardening review: verify RLS policies, encryption, audit logging, no PHI leaks in API responses, CORS configuration

**Checkpoint**: Platform is production-ready for demo and clinical validation.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phases 3–8)**: All depend on Foundational phase completion
  - US1 (Phase 3): Can start immediately after Phase 2
  - US2 (Phase 4): Can start after Phase 2 (independent of US1 backend, but integrates into same patient detail page)
  - US3 (Phase 5): Can start after Phase 2 (independent)
  - US4 (Phase 6): Can start after Phase 2 (independent)
  - US5 (Phase 7): Can start after Phase 2 (independent)
  - US6 (Phase 8): Can start after Phase 2 (independent)
- **Dashboard (Phase 9)**: Can start after Phase 2, benefits from US1 being complete
- **Android (Phase 10)**: Can start after Phase 2, needs Person 1's TFLite models for full testing
- **Integration (Phase 11)**: Depends on all user story phases being complete

### User Story Dependencies

- **US1 (P1)**: Independent — start first (MVP)
- **US2 (P2)**: Independent backend, shares patient detail page with US1 (frontend integration)
- **US3 (P3)**: Independent backend, shares patient detail page with US1/US2
- **US4 (P4)**: Independent backend, shares patient detail page with US1/US2/US3
- **US5 (P5)**: Fully independent (ABDM is a separate system)
- **US6 (P6)**: Fully independent (FL is a separate subsystem)

### Within Each User Story

- Backend endpoints before frontend components
- Components before page integration
- Core implementation before polish

### Parallel Opportunities

- All [P] tasks within a phase can run simultaneously
- US5 (ABDM) and US6 (FL) are fully independent — can run in parallel with US1–US4
- Android module (Phase 10) can be built in parallel with frontend work
- All integration tests (T074–T078) can run in parallel

---

## Parallel Example: User Story 1

```text
# After Phase 2 completes, launch in parallel:
T029: CameraCapture.tsx     (frontend component)
T030: AudioCapture.tsx      (frontend component)

# Then sequentially:
T024-T028: Backend endpoints + inference service
T031-T035: Remaining frontend components + page assembly
```

## Parallel Example: User Stories 5 & 6

```text
# These can run completely in parallel:
Developer A: T048-T055 (ABDM integration)
Developer B: T056-T062 (Federated Learning)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Passive Health Scan)
4. **STOP and VALIDATE**: Test scan → upload → process → display flow
5. Deploy/demo if ready — this alone has value as a screening tool

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Scan) → Test → Deploy (MVP!)
3. Add US2 (Causal) → Test → Deploy (explainable diagnosis)
4. Add US3 (Trajectory) → Test → Deploy (prognostic capability)
5. Add US4 (Intervention) → Test → Deploy (actionable recommendations)
6. Add US5 (ABDM) → Test → Deploy (health stack integration)
7. Add US6 (FL) → Test → Deploy (collaborative learning)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With Person 4 solo:
1. Phase 1 + 2 first (foundation)
2. US1 (MVP) — prioritize end-to-end flow
3. US5 + US6 can be interleaved since they're fully independent
4. US2/US3/US4 are frontend-heavy — batch together
5. Android module when Person 1 delivers TFLite models

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Person 4 consumes ML model outputs from Persons 1–3 as imported modules/TFLite artifacts
