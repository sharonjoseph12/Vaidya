# Requirements: PRISM App Enhancements

## Introduction

The PRISM clinical AI diagnostic platform frontend (Next.js 14 App Router) requires a set of enhancements to differentiate its pages, improve usability, and fix existing issues. Currently, the `/patients` and `/federated` pages duplicate dashboard content; the scan page redirects away before showing results; the FL status API has a TypeScript type error; and several platform-wide features (recent scans widget, live health checks, navigation fixes, patient detail breadcrumbs) are missing or incomplete. This feature addresses all six enhancement areas in a coordinated way.

## Requirements

### Requirement 1

**User Story:** As a clinician, I want the sidebar navigation to accurately reflect the app's pages so that I can navigate to the correct destinations without confusion.

#### Acceptance Criteria

1. The sidebar nav item currently labelled "Overview" SHALL be renamed to "Dashboard" in `app/dashboard/layout.tsx`.
2. The broken `/dashboard/fl` nav item SHALL be replaced with `/federated` pointing to the Federated Learning page.
3. The `navItems` array SHALL contain entries for all four top-level routes: `/dashboard`, `/scan`, `/patients`, `/federated`.
4. The active state highlight SHALL apply correctly when the current pathname matches any of the four top-level routes: `/dashboard`, `/scan`, `/patients`, or `/federated`.
5. The page `h1` heading in `app/dashboard/page.tsx` SHALL remain "Dashboard" (unchanged).

---

### Requirement 2

**User Story:** As a clinician, I want a full-featured Patient Management page at `/patients` so that I can search, filter, sort, and manage all registered patients in one place rather than seeing the same limited widget as on the dashboard.

#### Acceptance Criteria

1. The `/patients` page SHALL render a `PatientStatsBar` component showing: total patients, high-risk count, scanned today, and average sessions per patient.
2. The page SHALL render a `PatientManagementTable` component (replacing the existing `PatientQueue` widget).
3. A search input SHALL filter patients by name or ABHA ID with a 300ms debounce before firing the API call.
4. A risk level dropdown SHALL filter by "All", "High", "Medium", or "Low"; the system SHALL validate that the selected value is one of these allowed options before making the API call, and SHALL NOT call `getPatients()` with an invalid filter value.
5. Each patient row SHALL display a risk badge: "High" (red) for `sessions_count >= 10`, "Medium" (amber) for `sessions_count >= 4`, "Low" (green) otherwise — derived client-side without an additional API call.
6. Clicking a column header for Name, Last Scan, Sessions Count, or Created At SHALL toggle sort direction (asc/desc) and pass sort parameters to `getPatients()`.
7. The table SHALL support pagination with Previous/Next buttons, displaying current page number and total page count, with a page size of 20.
8. A header checkbox SHALL select/deselect all visible rows; individual row checkboxes SHALL allow multi-select.
9. When one or more rows are selected, an "Export CSV" button SHALL appear and trigger a browser download of a CSV file containing the selected patients with columns: ID, Name, Age, Sex, Location, ABHA ID, Sessions, Last Scan, Risk Level.
10. CSV patient name fields SHALL be sanitized to prevent CSV injection by stripping leading `=`, `+`, `-`, `@` characters.
11. Each patient row SHALL have a "Scan 📷" button that navigates to `/scan?patientId={patient.id}` without triggering row navigation to the patient detail page.

---

### Requirement 3

**User Story:** As a data scientist or hospital administrator, I want a dedicated Federated Learning operations page at `/federated` so that I can monitor node participation, track privacy budget consumption, inspect per-round details, and trigger new training rounds — all in one place.

#### Acceptance Criteria

1. The `/federated` page SHALL render the existing `FederatedDashboard` convergence chart as one section among several.
2. A `NodeParticipationTable` component SHALL render a table of hospital nodes, each row showing: node ID/name, status (active/idle/offline with colour-coded dot), rounds participated, data samples contributed, DP epsilon spent, and last seen timestamp.
3. A `PrivacyBudgetGauge` component SHALL render a radial SVG arc gauge showing cumulative ε against a maximum of ε = 10, with arc colour green (ε < 5), amber (5 ≤ ε < 8), or red (ε ≥ 8), and SHALL display remaining budget percentage, current δ, and noise multiplier.
4. A `RoundDetailTable` component SHALL render one row per FL round; clicking a row SHALL expand it to show participating nodes, accuracy delta vs previous round, and loss delta — colour-coded green for improvement and red for regression.
5. A `ModelVersionHistory` component SHALL render a table of past model versions with columns: version string, accuracy, loss, training date, and number of participating nodes.
6. A `DPExplainerPanel` component SHALL display current ε, δ, noise multiplier, and mechanism name with a plain-language explanation of the privacy guarantee.
7. A `TrainingControls` component SHALL render a "Trigger New Round" button and a minimum node threshold input (range: 1 to total_nodes); the button SHALL be disabled while a round is in progress and SHALL call `triggerFLRound(minNodes)` on click, showing a success or error toast. The system SHALL allow triggering rounds immediately at startup even with no prior participation history. The backend SHALL reject `triggerFLRound()` calls when a round is already active, providing server-side protection against concurrent round triggers.

---

### Requirement 4

**User Story:** As a clinician performing a scan, I want to see live cough detection feedback during audio recording and view the analysis results inline on the scan page so that I can quickly assess the patient without navigating away.

#### Acceptance Criteria

1. A `CoughDetectionPanel` component SHALL be rendered alongside `AudioCapture` during the capture phase, showing a scrolling time-domain waveform (not frequency bars).
2. Red vertical markers SHALL appear on the waveform at detected cough event timestamps.
3. A cough count badge SHALL increment in real time as coughs are detected.
4. A sound type label SHALL display the current classification: "cough", "breathing", or "silence".
5. The `detectCoughEvent(buffer, sampleRate)` function SHALL be a pure function that returns `true` when RMS energy > 0.15 AND zero-crossing rate is between 0.1 and 0.45, and `false` otherwise.
6. When `stage === "complete"` is received from the SSE stream, `getResults(sessionId)` SHALL be called and a `ScanResultsPanel` component SHALL render on the scan page — the page SHALL NOT automatically redirect to `/patient/[sessionId]`. If `getResults()` fails or returns no data, the `ScanResultsPanel` SHALL still render, showing an error state with a message and the "View Full Report" button still enabled.
7. The `ScanResultsPanel` SHALL display rPPG vitals (HR, SpO2, HRV RMSSD, RR) as metric cards with colour-coded status chips using clinical thresholds: HR normal 60–100 bpm, SpO2 normal ≥ 95%, HRV normal 20–80 ms, RR normal 12–20 breaths/min. Before display, vitals SHALL be validated against physiological possibility ranges (HR: 20–300 bpm, SpO2: 50–100%, HRV: 0–300 ms, RR: 4–60 breaths/min); values outside these ranges SHALL be shown with a "⚠ Unreliable" label instead of a status chip.
8. The `ScanResultsPanel` SHALL display audio results: cough count, wheeze detected badge, and crackle detected badge.
9. The `ScanResultsPanel` SHALL display visual scores (jaundice, anemia, cyanosis) as labelled progress bars sourced from `result.sense_results.visual`.
10. The `ScanResultsPanel` SHALL display a horizontal bar chart of the top 5 disease probabilities using `DISEASE_LABELS` for names and `getRiskColor()` for bar colours.
11. A "View Full Report" button SHALL navigate to `/patient/[sessionId]`.
12. A "Scan Again" button SHALL reset the scan page to the capture state, clearing videoBlob, audioBlob, and results.

---

### Requirement 5

**User Story:** As a developer, I want the FL API functions to have correct TypeScript return types so that the TypeScript compiler does not report errors and IDE tooling works correctly.

#### Acceptance Criteria

1. `getFLStatus` in `lib/api.ts` SHALL have the explicit return type `Promise<FLStatus>`, with `FLStatus` imported from `lib/types.ts`.
2. `getFLRounds` in `lib/api.ts` SHALL have the explicit return type `Promise<FLRound[] | { rounds: FLRound[] }>`, with `FLRound` imported from `lib/types.ts`.
3. The TypeScript error "flStatus is of type unknown" in `StatsOverview.tsx` SHALL be resolved exclusively through proper API function return type annotations — type assertions (`as FLStatus`) or `any` casting SHALL NOT be used as the fix.
4. Running `tsc --noEmit` on the project SHALL pass without errors related to these functions.

---

### Requirement 6

**User Story:** As a clinician, I want the dashboard to show recent scan activity and live system health, the patient detail page to show patient demographics and a back-navigation breadcrumb, and the offline banner to work reliably across all pages.

#### Acceptance Criteria

1. The `OfflineBanner` component SHALL remain rendered in `app/layout.tsx` and SHALL appear at the top of every page when `offlineStore.isOffline` is `true`.
2. A `RecentScans` component SHALL be added to `app/dashboard/page.tsx`, calling `getRecentSessions(5)` on mount and rendering up to 5 rows each showing: patient name (or ID if no name), primary diagnosis, confidence score, and timestamp — each row linking to `/patient/[session_id]`.
3. `getRecentSessions(limit?: number)` SHALL be added to `lib/api.ts` calling `GET /diagnostics/sessions?limit={limit}`.
4. A `SubsystemHealth` component SHALL replace the hardcoded status panel in `app/dashboard/page.tsx`, calling `healthCheck()` on mount and every 30 seconds and displaying latency (ms) alongside each status indicator.
5. `healthCheck()` SHALL be added to `lib/api.ts` calling `GET /health` and returning `Promise<HealthStatus>`.
6. FL node status in `SubsystemHealth` SHALL be derived from `getFLStatus()` (active_nodes > 0 → "Active", active_nodes === 0 → "Idle"); if `getFLStatus()` fails or returns stale/inconsistent data, the FL node status SHALL fall back to "Unknown" with an amber indicator rather than crashing or showing a misleading status.
7. A "← Patients" breadcrumb link SHALL be rendered at the top of `app/patient/[id]/page.tsx`, navigating to `/patients` when clicked.
8. `getPatient(id)` SHALL be called alongside `getResults(id)` on the patient detail page, and the patient's name, age, sex, location, and ABHA ID (if present) SHALL be displayed in the header card when the data is available; if `getPatient()` fails, the page SHALL still render with the diagnostic results and the demographics section SHALL show a graceful fallback (e.g., "Demographics unavailable"). When `getPatient()` succeeds, the page SHALL conditionally render the demographics section only if the returned patient object contains a `demographics` field.
9. The following interfaces SHALL be added to `lib/types.ts`: `FLNode`, `ModelVersion`, `RecentSession`, and `HealthStatus` with the fields specified in the design document.
