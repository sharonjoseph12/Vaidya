# Feature Specification: PRISM Diagnostic Platform

**Feature Branch**: `001-prism-platform`  
**Created**: 2026-05-14  
**Status**: Draft  

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Clinical Diagnostic Scan via Smartphone (Priority: P1)

A patient or health worker records a 30-second passive capture of the patient (audio, facial video, IMU gait). PRISM processes the multimodal data on the edge device and immediately outputs disease probabilities and trajectory predictions.

**Why this priority**: It is the core value proposition of PRISM—hardware-free, offline-capable disease detection.

**Independent Test**: Can be fully tested by feeding 30-second pre-recorded video/audio samples and verifying output probabilities and causal graph structures match expected medical baselines.

**Acceptance Scenarios**:

1. **Given** a patient with TB-like cough and pallor, **When** the smartphone captures 30 seconds of video/audio, **Then** the application outputs an expected TB probability with a 90% confidence interval.
2. **Given** a patient with no internet access, **When** the 30-second capture is completed, **Then** the inference engine successfully completes the processing and visualization offline within 30 seconds.

---

### User Story 2 - Causal Intervention and Trajectory Planning (Priority: P2)

A clinician reviews a patient's output on the PRISM dashboard. They view the underlying causal graph (e.g., poor nutrition causing anemia), and select an AI-recommended optimal intervention strategy based on cost-per-QALY. The platform simulates the post-intervention health trajectory.

**Why this priority**: Differentiates PRISM from simple correlational AI by explaining *why* the patient is ill and dynamically simulating intervention outcomes.

**Independent Test**: Can be independently tested by providing mock patient data and observing the RL optimizer's recommendations and the Neural ODE twin's shifted trajectory curve.

**Acceptance Scenarios**:

1. **Given** a patient with high TB probability, **When** the clinician selects "Nutritional Supplementation", **Then** the system updates the trajectory graph to reflect delayed/prevented disease onset.

---

### User Story 3 - ABDM Integration (Priority: P3)

A clinician finishes a diagnostic session and synchronizes the diagnostic report directly to the patient's Ayushman Bharat Health Account (ABHA).

**Why this priority**: Required for national-scale deployability and longitudinal data collection.

**Independent Test**: Can be tested by pushing a mock FHIR R4 DiagnosticReport payload to the ABDM sandbox API and successfully verifying its persistence.

**Acceptance Scenarios**:

1. **Given** a confirmed PRISM diagnostic result, **When** the sync button is pressed, **Then** the report is securely stored in the patient's ABHA health locker.

---

### Edge Cases

- What happens when lighting conditions are too poor for accurate rPPG facial extraction? (System should prompt user to move to a well-lit area or gracefully fallback to audio/IMU-only models).
- How does system handle intense background noise during audio capture? (Audio augmentation/filtering handles normal noise, but above a decibel threshold, the app must warn the user).
- What happens if the patient has no ABHA ID? (The app can still perform a local assessment and print/export a PDF report).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract physiological signals (HR, SpO2, HRV, RR) from facial video using remote photoplethysmography (rPPG).
- **FR-002**: System MUST classify audio waveforms to detect disease markers (cough, breathing, voice) using an ensemble model.
- **FR-003**: System MUST identify visual facial cues (pallor, cyanosis, jaundice) and gait patterns.
- **FR-004**: System MUST combine all modalities via Cross-Modal Attention Fusion to output a final disease prediction.
- **FR-005**: System MUST discover and generate Structural Causal Models (SCMs) and explain disease causes.
- **FR-006**: System MUST simulate future patient health trajectories using a Neural ODE Digital Twin.
- **FR-007**: System MUST provide an RL-optimized intervention plan factoring in Ayushman Bharat cost databases.
- **FR-008**: System MUST run its SENSE layer inference 100% offline on an Android device via quantized TFLite models.
- **FR-009**: System MUST support Federated Learning so hospital nodes can train models without sharing raw patient data.
- **FR-010**: System MUST sync output FHIR R4 reports with ABDM patient accounts.

### Key Entities

- **Biomarker Profile**: Collected multi-modal metrics (SpO2, heart rate, cough frequency, visual signs).
- **Causal Graph**: Discovered network of variables linking patient risk factors and disease outcomes.
- **Digital Twin**: Continuous state vector processed by Neural ODEs to forecast future health.
- **Intervention**: A recommended medical or lifestyle action, including its associated cost and QALY gain.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: TB detection model achieves >82% sensitivity and >79% specificity.
- **SC-002**: Mobile inference model completes processing within 30 seconds entirely offline on a standard Android phone.
- **SC-003**: Neural ODE Digital twin predicts HbA1c trajectory with MAE < 0.4% at 6 months.
- **SC-004**: TFLite compiled models consume less than 15MB of storage on device.
- **SC-005**: All diagnostic probabilities output a valid conformal confidence interval guaranteeing 90% coverage.

## Assumptions

- Assumes users (health workers/patients) possess an Android smartphone with a working camera and microphone.
- Assumes patient ABHA sandbox accounts are provisioned during demonstrations.
- Assumes the TFLite runtime is capable of supporting Cross-Modal Attention operations.
