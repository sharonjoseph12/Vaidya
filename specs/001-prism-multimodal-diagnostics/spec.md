# Feature Specification: PRISM — Passive Readings → Intelligent Scalable Medicine

**Feature Branch**: `001-prism-multimodal-diagnostics`

**Created**: 2026-05-14

**Status**: Draft

**Input**: User description: "PRISM — Complete multimodal AI diagnostic platform using smartphone sensors to detect disease, explain causal pathways, simulate patient health trajectories, and recommend cost-optimal interventions — targeting low-resource clinical settings in India."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Passive Biomarker Capture & Instant Diagnosis (Priority: P1)

A community health worker or patient holds an Android phone and initiates a 30-second scan. Without touching the patient or attaching any device, PRISM captures audio (breathing, cough, voice) through the microphone, extracts heart rate, blood oxygen saturation, and respiratory rate from the facial camera feed, and records motion data from the phone's built-in sensors. At the end of the scan, the system displays the top probable conditions — for example "TB likelihood: 79%" — with a confidence range, entirely on-device with no internet required.

**Why this priority**: This is the core value proposition — zero-hardware, offline-capable, contactless disease screening. Without P1 working, nothing else matters.

**Independent Test**: A PRISM scan on a phone with no SIM card and no Wi-Fi still produces a disease probability output within 60 seconds of scan initiation, drawing only from the phone's microphone, camera, and motion sensors.

**Acceptance Scenarios**:

1. **Given** a patient with confirmed TB (lab-verified), **When** a 30-second PRISM scan is conducted in a quiet room with standard lighting, **Then** the system assigns TB probability ≥ 70% and the result appears within 60 seconds of scan completion.
2. **Given** a healthy control subject, **When** a 30-second PRISM scan is conducted, **Then** the system assigns "healthy" or low-risk probability ≥ 75% with no high-severity alerts.
3. **Given** the phone has no internet connection, **When** a scan is initiated, **Then** the scan completes and a full diagnostic result is displayed without any error or degraded output.
4. **Given** low ambient light (indoor, unlit room), **When** a scan is initiated, **Then** the system surfaces a lighting warning to the user rather than producing a silently inaccurate result.

---

### User Story 2 — Causal Explanation of Diagnosis (Priority: P2)

After receiving a diagnosis, the clinician or health worker taps "Why?" and sees a visual causal chain: which factors (malnutrition, living conditions, prior infection history) are responsible for the detected condition and by what proportion. The screen also shows a counterfactual: "If this patient's nutritional status improves to adequate, TB probability drops from 79% to 31%." This is displayed in plain language, not technical jargon.

**Why this priority**: Correlation-only AI is rejected by clinicians. Causal explanations drive trust, clinical adoption, and enable actionable decisions. This is the primary differentiator from competing systems.

**Independent Test**: Given a patient profile with known risk factors, the explanation panel displays at least 2 causal contributors each with a percentage attribution, and at least 1 counterfactual scenario, without requiring any internet or cloud call.

**Acceptance Scenarios**:

1. **Given** a TB-positive scan result, **When** the user views the explanation panel, **Then** at least 2 contributing causal factors are displayed with quantified attribution percentages that sum to ≥ 80% of explained risk.
2. **Given** a causal explanation is shown, **When** the user selects "What if malnutrition is treated?", **Then** the system shows a revised probability for the primary condition reflecting the counterfactual intervention.
3. **Given** a non-technical community health worker is the user, **When** the causal explanation is displayed, **Then** all terms used are either plain-language or accompanied by a one-tap tooltip definition.

---

### User Story 3 — Health Trajectory Simulation (Digital Twin) (Priority: P2)

The clinician views a timeline chart showing where this patient's key health indicators are projected to go over the next 6–18 months under two scenarios: no intervention and with the recommended intervention. The chart uses the patient's current scan data and, if available, their prior health records from the national health system. The projection includes a confidence band around the trajectory.

**Why this priority**: Trajectory forecasting transforms PRISM from a diagnostic tool into a clinical decision support system — enabling early intervention before irreversible deterioration.

**Independent Test**: With a known patient scan profile, the system generates a dual-trajectory chart (baseline vs. intervention) spanning at least 6 months, with a visible confidence band, in under 30 seconds.

**Acceptance Scenarios**:

1. **Given** a completed scan, **When** the clinician opens the trajectory view, **Then** two trajectory curves (untreated and treated) are displayed with 90% confidence intervals across a minimum 6-month horizon.
2. **Given** internet connectivity is available and the patient has a national health ID, **When** the digital twin is built, **Then** the system fetches prior health records to improve trajectory accuracy and shows a "history-enriched" indicator.
3. **Given** no prior records are available, **When** trajectory is requested, **Then** the system generates a trajectory using current scan data alone and labels it "baseline estimate only."
4. **Given** the predicted trajectory shows deterioration within 3 months without intervention, **When** this is the case, **Then** an urgent alert is surfaced prominently before the full trajectory view.

---

### User Story 4 — Cost-Optimised Intervention Recommendations (Priority: P3)

After diagnosis and trajectory simulation, the system presents a ranked list of recommended next steps — e.g., "Order sputum test (free at PHC, 1.2 km away)", "Start DOTS treatment (free under RNTCP)", "Nutritional supplementation (free under ICDS scheme)". Each recommendation shows expected health benefit, cost to the patient, and nearest facility. The clinician can select a plan, which is automatically added to the patient's national health record.

**Why this priority**: Without actionable, affordable recommendations, diagnosis alone does not improve outcomes. This closes the loop from detection to care.

**Independent Test**: Given a TB-positive diagnosis in a rural Mangalore district profile, the system outputs at least 3 ranked interventions with cost, nearest facility, and projected health benefit, with at least 1 intervention flagged as ₹0 cost.

**Acceptance Scenarios**:

1. **Given** a disease diagnosis, **When** the intervention panel is opened, **Then** at least 3 ranked intervention options are displayed, each showing: action name, estimated cost to patient, expected health benefit, and nearest facility.
2. **Given** a patient with low income, **When** interventions are displayed, **Then** the top-ranked option is the highest-benefit ₹0-cost action available, not the most expensive option.
3. **Given** the clinician selects an intervention plan, **When** they confirm, **Then** the plan is written to the patient's national health record (if connected) and a printable summary is generated.
4. **Given** the system is uncertain about diagnosis, **When** interventions are displayed, **Then** the recommended action is the single diagnostic test that most reduces uncertainty, with cost and facility shown.

---

### User Story 5 — Privacy-Preserving Hospital Network Participation (Priority: P4)

A hospital IT administrator enrolls their institution in the PRISM federated learning network. The hospital's patient data never leaves its servers — only anonymised model improvements are contributed. The hospital receives a continuously improving diagnostic model in return. The administrator can view contribution statistics and privacy guarantees from the admin console.

**Why this priority**: Hospital adoption at scale requires that institutions trust PRISM with their patients' data. Federated learning resolves the primary barrier to institutional deployment.

**Independent Test**: Two simulated hospital nodes independently train on local data and successfully contribute to a global model update without any raw patient records being transmitted to the central server, verified by network traffic inspection.

**Acceptance Scenarios**:

1. **Given** a hospital enrolls in federated learning, **When** a global model update round occurs, **Then** only aggregated weight updates (not patient records) are transmitted, and the hospital's local data remains on its servers.
2. **Given** a federated learning round completes, **When** the admin views the dashboard, **Then** the dashboard shows: rounds participated, contribution size, current privacy budget consumed (ε value), and model version received.
3. **Given** differential privacy is active, **When** the admin reviews settings, **Then** the privacy guarantee (ε ≤ 1.0, δ ≤ 10⁻⁵) is displayed and enforced, and the system refuses to transmit updates that would exceed the budget.

---

### Edge Cases

- What happens when ambient noise is too high for reliable audio analysis (e.g., busy marketplace)? → System surfaces a noise-level warning and prompts the user to retry in a quieter environment rather than silently returning inaccurate results.
- What happens if the patient's face is obscured (e.g., wearing a mask, extreme skin tones, poor lighting)? → System disables the visual biomarker module, flags which signals were unavailable, and produces a partial diagnosis from remaining modalities with an explicit uncertainty increase.
- What happens if the patient scan produces model outputs near the decision boundary (e.g., 51% TB probability)? → System surfaces the result with a high-uncertainty flag and recommends the single confirmatory diagnostic test rather than a definitive diagnosis.
- What happens if the national health system integration is unavailable? → All features operate in full offline mode; records are queued locally and synced when connectivity is restored.
- What happens if a patient has multiple simultaneous conditions (e.g., TB + anemia)? → All detected conditions above the confidence threshold are reported, each with independent causal explanations and intervention plans.
- What happens if a minor (under 18) initiates a scan? → System requires adult/guardian confirmation of consent before proceeding, as per applicable regulations.
- What happens if model confidence is below minimum threshold for all conditions? → System returns "Insufficient signal — scan quality low" and prompts re-scan rather than outputting a meaningless result.

---

## Requirements *(mandatory)*

### Functional Requirements

**Sensing & Biomarker Extraction**

- **FR-001**: The system MUST extract heart rate, blood oxygen saturation, and respiratory rate from a standard front-facing phone camera during a 30-second facial video capture, without any external sensors.
- **FR-002**: The system MUST detect and classify cough sounds, breathing patterns, and voice characteristics from the phone microphone during the scan session.
- **FR-003**: The system MUST detect motion patterns (gait, movement) from the phone's built-in motion sensors during the scan session.
- **FR-004**: The system MUST normalise for varying lighting conditions, skin tones, and ambient noise levels and indicate when environmental quality is insufficient for reliable measurement.
- **FR-005**: The system MUST produce all biomarker extractions entirely on-device without transmitting audio or video data to any external service.

**Diagnosis**

- **FR-006**: The system MUST fuse signals from all available sensing modalities (audio, visual, physiological, motion) to produce disease probability scores for at least 8 target conditions: TB, Pneumonia, Anemia, Jaundice, Dengue, Heart Failure, Asthma/COPD, and Healthy.
- **FR-007**: Every disease probability output MUST be accompanied by a calibrated confidence interval (minimum 90% coverage guarantee).
- **FR-008**: The system MUST operate fully offline — producing complete diagnostic output with no internet connection — on Android devices manufactured from 2018 onwards.
- **FR-009**: The system MUST communicate clearly when a modality is unavailable and adjust uncertainty accordingly rather than failing silently.

**Causal Explanation**

- **FR-010**: For every diagnosis above a minimum confidence threshold, the system MUST display a causal breakdown showing at least 2 contributing factors with percentage attribution.
- **FR-011**: The system MUST generate at least 1 counterfactual scenario per diagnosis: "If [modifiable factor] changes to [value], condition probability becomes [revised probability]."
- **FR-012**: Causal explanations MUST be expressed in plain language accessible to non-clinical users, with optional detail expansion for clinicians.

**Trajectory Simulation**

- **FR-013**: The system MUST generate a minimum 6-month health trajectory projection from current scan data, showing at least two scenarios: no intervention and top-recommended intervention.
- **FR-014**: Trajectory projections MUST display 90% confidence bands.
- **FR-015**: When a patient's trajectory predicts critical deterioration within 90 days, the system MUST surface an urgent alert before displaying the full trajectory.
- **FR-016**: When national health record integration is available and consented, the system MUST use prior longitudinal records to improve trajectory accuracy.

**Intervention Optimisation**

- **FR-017**: For every diagnosed condition, the system MUST generate a ranked list of at least 3 intervention options, each displaying: action description, patient cost, expected health benefit, and nearest available facility.
- **FR-018**: The intervention ranking MUST prioritise cost-effectiveness — the highest benefit-to-cost ratio action must appear first.
- **FR-019**: When diagnostic uncertainty is above a defined threshold, the system MUST recommend the single confirmatory test that most reduces uncertainty rather than a treatment plan.
- **FR-020**: Selected intervention plans MUST be exportable as a printable summary and, when connected, pushed to the patient's national health record.

**National Health Integration**

- **FR-021**: The system MUST support patient lookup and record retrieval using the national health ID (ABHA ID) when the patient consents and connectivity is available.
- **FR-022**: Completed diagnostic reports MUST be pushable to the patient's national health record in standard clinical data interchange format.
- **FR-023**: All national health system integration MUST be fully optional — the system MUST be fully functional without any national health system connection.

**Privacy & Security**

- **FR-024**: Audio and video captured during scanning MUST be processed in memory only and MUST NOT be written to persistent storage on the device.
- **FR-025**: All patient identifiers MUST be pseudonymised before transmission to any external service.
- **FR-026**: The system MUST comply with India's Digital Personal Data Protection Act 2023, including explicit consent capture before any data processing.
- **FR-027**: The federated learning subsystem MUST enforce a formal differential privacy guarantee (ε ≤ 1.0, δ ≤ 10⁻⁵) on all model update transmissions.

**Clinical Validation**

- **FR-028**: The system MUST be validated against a minimum of 50 clinically confirmed cases (ground-truth diagnoses from lab or imaging) before any public deployment.
- **FR-029**: Sensitivity and specificity for each supported condition MUST be documented and published alongside the system.

### Key Entities

- **Patient Scan Session**: A single 30-second capture event — includes raw sensor data (held in memory), extracted biomarker features, device metadata (model, OS version, lighting quality score), and session timestamp.
- **Diagnostic Report**: The output of a scan session — includes condition probabilities with confidence intervals, causal attribution breakdown, counterfactual scenarios, trajectory projections, and ranked intervention plan. Persisted locally and optionally in the national health record.
- **Patient Profile**: An optional longitudinal record for a patient — links multiple scan sessions over time, references national health ID (ABHA) if enrolled, contains consent flags and intervention history.
- **Causal Graph**: A structured model of disease causation specific to a patient — encodes which factors contribute to which conditions, at what magnitude, and how interventions modify those relationships.
- **Digital Twin**: A patient-specific health simulation model — initialised from current scan biomarkers and enriched with historical records when available, used to generate trajectory projections.
- **Intervention Plan**: A ranked, actionable set of next steps — each item has a type (test, treatment, referral, lifestyle), cost bracket, expected benefit in health-years, and associated facility.
- **Federated Node**: A participating institution in the learning network — has a local model, contribution history, privacy budget tracker, and sync status with the central aggregator.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A complete scan-to-report cycle (capture → biomarker extraction → diagnosis → causal explanation → trajectory → intervention plan) completes in under 90 seconds on a mid-range Android device (≤ ₹15,000 retail price).
- **SC-002**: Diagnostic sensitivity for TB detection is ≥ 82% and specificity is ≥ 79% on the 50-patient clinical validation cohort, exceeding standard symptom-based screening benchmarks.
- **SC-003**: Diagnostic sensitivity for anemia detection is ≥ 88% and specificity is ≥ 85% on the clinical validation cohort, exceeding standard conjunctival examination benchmarks.
- **SC-004**: The system operates fully offline — 100% of core features (scan, diagnose, explain, trajectory, interventions) complete without internet — verified on a device in airplane mode.
- **SC-005**: Trajectory projections achieve mean absolute error < 15% versus actual 6-month outcomes on held-out validation patients from the clinical dataset.
- **SC-006**: Community health workers with no prior medical training can complete a full patient scan and interpret the diagnostic report after a training session of ≤ 30 minutes, with a task-completion rate ≥ 85%.
- **SC-007**: In the federated learning setup, no raw patient data is transmitted during any training round — verified by independent network audit.
- **SC-008**: Conformal prediction confidence intervals achieve ≥ 90% empirical coverage on the calibration set — meaning reported uncertainty bands are statistically valid.
- **SC-009**: The system is deployable on any Android device running OS version ≥ 8.0 released after 2018 without requiring additional hardware or app permissions beyond microphone and camera.
- **SC-010**: The research findings, clinical validation results, and methodology are submitted to a public preprint server before the end of the project period, establishing academic legitimacy.

---

## Assumptions

- Target users are community health workers, primary care clinicians, and patients in rural/semi-urban India; they may have limited digital literacy but own or have access to an Android smartphone.
- The primary deployment device is an Android smartphone with a front-facing camera, microphone, and motion sensors — iOS support is out of scope for v1.
- Clinical ground-truth data for model training and validation will be sourced from KMC Mangalore OPD under a valid ethics committee approval; without this approval, validation is limited to synthetic and public datasets.
- Public datasets (COUGHVID, Coswara, MIMIC-IV, NHANES, PhysioNet) are accessible under their respective data use agreements; access to MIMIC-IV in particular requires a credentialing application.
- The national health system (ABHA/ABDM) integration uses the sandbox API during development and requires production API registration before public deployment; this integration is fully optional for core diagnostic functionality.
- Federated learning assumes participating hospitals have sufficient local compute (standard server hardware) to run local model training; no GPU is required on hospital nodes.
- The system targets 12 disease conditions for v1; additional conditions can be added in future versions without architectural changes.
- Model training occurs on cloud compute (GPU instances) during development; on-device inference only uses compressed, quantised models.
- Regulatory approval (CDSCO Class B medical device) is a post-competition goal; the system will be demonstrated as a research tool, not a certified medical device, during the competition phase.
- All user-facing text, alerts, and reports will be available in English for v1; regional language support (Kannada, Hindi) is a v2 priority.
