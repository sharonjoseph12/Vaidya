# Tasks: PRISM App Enhancements

## Overview

Implementation tasks derived from the design and requirements documents. Tasks are ordered to minimise blocking dependencies: foundational type/API changes first, then new components, then page-level wiring.

---

## Tasks

- [ ] 1. Fix TypeScript types in lib/api.ts and lib/types.ts
  - [ ] 1.1 Add explicit return type `Promise<FLStatus>` to `getFLStatus` in `lib/api.ts`
  - [ ] 1.2 Add explicit return type `Promise<FLRound[] | { rounds: FLRound[] }>` to `getFLRounds` in `lib/api.ts`
  - [ ] 1.3 Add `FLNode` interface to `lib/types.ts` with fields: `node_id`, `hospital_name`, `status`, `rounds_participated`, `data_samples_contributed`, `dp_epsilon_spent`, `last_seen?`
  - [ ] 1.4 Add `ModelVersion` interface to `lib/types.ts` with fields: `version`, `accuracy`, `loss`, `trained_at`, `participating_nodes`
  - [ ] 1.5 Add `RecentSession` interface to `lib/types.ts` with fields: `session_id`, `patient_id`, `patient_name?`, `primary_diagnosis?`, `confidence_score?`, `created_at`
  - [ ] 1.6 Add `HealthStatus` interface to `lib/types.ts` with fields: `status`, `version?`, `uptime_seconds?`
  - [ ] 1.7 Add `getRecentSessions(limit?: number): Promise<RecentSession[]>` to `lib/api.ts` calling `GET /diagnostics/sessions?limit={limit}`
  - [ ] 1.8 Add `healthCheck(): Promise<HealthStatus>` to `lib/api.ts` calling `GET /health`
  - [ ] 1.9 Add `getFLNodes(): Promise<FLNode[]>` to `lib/api.ts` calling `GET /federated/nodes`
  - [ ] 1.10 Add `getModelVersionHistory(): Promise<ModelVersion[]>` to `lib/api.ts` calling `GET /federated/model-versions`
  - [ ] 1.11 Add `triggerFLRound(minNodes: number): Promise<{ round_number: number; status: string }>` to `lib/api.ts` calling `POST /federated/trigger-round`
  - [ ] 1.12 Extend `getPatients` signature to accept optional `search`, `riskLevel`, `sortField`, `sortDir` query parameters
  - [ ] 1.13 Verify `tsc --noEmit` passes without errors (especially in `StatsOverview.tsx` and `FederatedDashboard.tsx`)

- [ ] 2. Fix sidebar navigation in app/dashboard/layout.tsx
  - [ ] 2.1 Rename the "Overview" nav item to "Dashboard"
  - [ ] 2.2 Replace the broken `/dashboard/fl` nav item with `/federated` labelled "Federated Learning"
  - [ ] 2.3 Verify all four nav items (`/dashboard`, `/scan`, `/patients`, `/federated`) are present with correct paths and icons
  - [ ] 2.4 Verify active state highlighting works for all four routes

- [ ] 3. Build Patient Management page components
  - [ ] 3.1 Create `components/patients/PatientStatsBar.tsx` — renders four stat cards (total, high-risk, scanned today, avg sessions) from a `PatientStats` prop
  - [ ] 3.2 Create `lib/utils.ts` helper `deriveRiskLevel(patient: Patient): "high" | "medium" | "low"` — High if sessions_count ≥ 10, Medium if ≥ 4, Low otherwise
  - [ ] 3.3 Create `lib/utils.ts` helper `generatePatientCSV(patients: Patient[]): string` — returns CSV string with header row and sanitized data rows
  - [ ] 3.4 Create `components/patients/PatientManagementTable.tsx` with internal state for `filters` (search, riskLevel, location), `sort` (field, direction), `page`, and `selectedIds`
  - [ ] 3.5 Implement search input with 300ms debounce in `PatientManagementTable`
  - [ ] 3.6 Implement risk level dropdown with validation (only "all", "high", "medium", "low" are valid before API call)
  - [ ] 3.7 Implement sortable column headers with directional arrow indicators
  - [ ] 3.8 Implement pagination controls (Previous/Next buttons, page number display, page size 20)
  - [ ] 3.9 Implement bulk select (header checkbox + row checkboxes) and "Export CSV" button that triggers browser download
  - [ ] 3.10 Implement risk badge column using `deriveRiskLevel`
  - [ ] 3.11 Implement Quick Scan button per row navigating to `/scan?patientId={id}` with `e.stopPropagation()`
  - [ ] 3.12 Wire `onStatsChange` callback to update `PatientStatsBar` with derived stats from the loaded patient list

- [ ] 4. Build Patient Management page
  - [ ] 4.1 Replace `app/patients/page.tsx` content with `PatientStatsBar` + `PatientManagementTable` layout
  - [ ] 4.2 Remove the "Back to Dashboard" button (page is a primary nav destination)
  - [ ] 4.3 Add error banner with retry button for API failures

- [ ] 5. Build Federated Learning Operations page components
  - [ ] 5.1 Create `components/federated/NodeParticipationTable.tsx` — renders table of `FLNode[]` with status dot, rounds, data samples, epsilon, last seen
  - [ ] 5.2 Create `components/federated/PrivacyBudgetGauge.tsx` — SVG radial arc gauge with green/amber/red colour thresholds at ε = 5 and ε = 8, showing remaining budget %, δ, and noise multiplier
  - [ ] 5.3 Create `components/federated/RoundDetailTable.tsx` — expandable rows per `FLRound` showing participating nodes, accuracy delta, loss delta with colour-coded badges
  - [ ] 5.4 Create `components/federated/ModelVersionHistory.tsx` — table of `ModelVersion[]` with version, accuracy, loss, date, node count
  - [ ] 5.5 Create `components/federated/DPExplainerPanel.tsx` — displays ε, δ, noise multiplier, mechanism name with plain-language explanation
  - [ ] 5.6 Create `components/federated/TrainingControls.tsx` — "Trigger New Round" button (disabled while round in progress), min nodes slider, success/error toast on API response; allows triggering at startup with no prior history
  - [ ] 5.7 Add polling for `getFLNodes()` every 30s in the FL ops page

- [ ] 6. Build Federated Learning Operations page
  - [ ] 6.1 Replace `app/federated/page.tsx` content with multi-section layout: metrics grid, `NodeParticipationTable`, `PrivacyBudgetGauge`, `RoundDetailTable`, `ModelVersionHistory`, `DPExplainerPanel`, `TrainingControls`, and existing `FederatedDashboard` convergence chart
  - [ ] 6.2 Remove the "Back to Dashboard" button (page is a primary nav destination)

- [ ] 7. Build Scan page cough detection components
  - [ ] 7.1 Extract `detectCoughEvent(buffer: Float32Array, sampleRate: number, threshold?: number): boolean` as a pure exported function in `lib/audio-utils.ts`
  - [ ] 7.2 Create `components/scan/CoughDetectionPanel.tsx` — accepts `isRecording` and `audioAnalyser: AnalyserNode | null`; draws scrolling time-domain waveform on canvas; detects cough events using `detectCoughEvent`; renders red vertical markers at cough timestamps; shows live cough count badge and sound type label ("cough" / "breathing" / "silence")
  - [ ] 7.3 Handle the case where `audioAnalyser` is null (microphone permission denied) — show "Microphone access required" message with retry guidance
  - [ ] 7.4 Expose `analyserRef` from `AudioCapture.tsx` via a callback prop `onAnalyserReady: (analyser: AnalyserNode) => void` so `ScanContent` can pass it to `CoughDetectionPanel`

- [ ] 8. Build Scan page inline results component
  - [ ] 8.1 Add `getVitalStatus(metric: "hr" | "spo2" | "hrv" | "rr", value: number): "normal" | "warning" | "critical" | "unreliable"` to `lib/utils.ts` with clinical thresholds and physiological validity ranges
  - [ ] 8.2 Create `components/scan/ScanResultsPanel.tsx` — renders rPPG vitals row, audio results row, visual scores row, disease probability mini bar chart, "View Full Report" button, and "Scan Again" button
  - [ ] 8.3 Implement vitals validation: values outside physiological ranges show "⚠ Unreliable" label instead of status chip
  - [ ] 8.4 Implement error state in `ScanResultsPanel` for when `getResults()` fails — show error message with "View Full Report" button still enabled

- [ ] 9. Wire Scan page enhancements
  - [ ] 9.1 Add `pageState: "results"` to the `PageState` union type in `app/scan/page.tsx`
  - [ ] 9.2 Add `scanResult` state (`DiagnosticResult | null`) and `analyserNode` state (`AnalyserNode | null`) to `ScanContent`
  - [ ] 9.3 On `stage === "complete"`, call `getResults(sessionId)`, set `scanResult`, and transition to `"results"` state instead of redirecting
  - [ ] 9.4 Render `CoughDetectionPanel` alongside `AudioCapture` during the capture phase, passing `analyserNode`
  - [ ] 9.5 Render `ScanResultsPanel` in the `"results"` state, passing `scanResult`, `sessionId`, and `onScanAgain` callback
  - [ ] 9.6 Implement `onScanAgain` to reset `pageState` to `"capture"`, clear `videoBlob`, `audioBlob`, and `scanResult`

- [ ] 10. Build dashboard enhancement components
  - [ ] 10.1 Create `components/dashboard/RecentScans.tsx` — calls `getRecentSessions(5)` on mount; renders up to 5 rows with patient name/ID, primary diagnosis badge, confidence score, timestamp; each row links to `/patient/[session_id]`
  - [ ] 10.2 Create `components/dashboard/SubsystemHealth.tsx` — calls `healthCheck()` on mount and every 30s; derives FL status from `getFLStatus()` with fallback to "Unknown" (amber) on failure; displays latency (ms) alongside each status indicator; ABDM shows "Standby" by default

- [ ] 11. Wire dashboard enhancements
  - [ ] 11.1 Add `RecentScans` component to `app/dashboard/page.tsx` below the Quick Actions / Subsystem Status grid
  - [ ] 11.2 Replace the hardcoded subsystem status panel in `app/dashboard/page.tsx` with `SubsystemHealth`
  - [ ] 11.3 Verify `OfflineBanner` is present in `app/layout.tsx` (no regression)

- [ ] 12. Enhance patient detail page
  - [ ] 12.1 Add `getPatient(id)` call alongside `getResults(id)` in `app/patient/[id]/page.tsx` using `Promise.allSettled` to handle independent failures
  - [ ] 12.2 Add "← Patients" breadcrumb link above the header card, navigating to `/patients`
  - [ ] 12.3 Display patient demographics (name, age, sex, location, ABHA ID) in the header card when `patient.demographics` is available; show "Demographics unavailable" fallback when `getPatient()` fails or demographics is absent
