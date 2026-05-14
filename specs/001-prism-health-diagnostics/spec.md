# Feature Specification: PRISM — Passive Readings for Intelligent Scalable Medicine

**Feature Branch**: `001-prism-health-diagnostics`

**Created**: 2026-05-14

**Status**: Draft

**Input**: User description: "PRISM — Complete Project Specification..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Passive Health Screening (Priority: P1)

A user in a rural area with no medical infrastructure uses their smartphone to perform a 30-second passive scan (facial video and audio). The system provides a diagnostic assessment for conditions like TB, anemia, or pneumonia without requiring expensive hardware or internet.

**Why this priority**: This is the core vision of PRISM—democratizing diagnostics for the 65% of India without access to labs.

**Independent Test**: Can be tested by running the "SENSE" layer on a phone with recorded patient data and verifying the biomarker extraction (HR, SpO2, RR) and initial classification.

**Acceptance Scenarios**:

1. **Given** a user with symptoms of TB, **When** they complete a 30-second scan, **Then** the system detects TB biomarkers with >80% sensitivity.
2. **Given** a user with anemia, **When** the system analyzes their conjunctiva and voice, **Then** it identifies anemia risk correctly.

---

### User Story 2 - Causal Rationale and Explainability (Priority: P2)

A clinician or patient reviews a diagnosis and asks "Why?". The system presents a causal graph showing how factors like malnutrition, home ventilation, and physiological biomarkers interact to lead to the current health state.

**Why this priority**: Increases clinical trust and allows for targeted interventions rather than just "black box" predictions.

**Independent Test**: Verify that for a given diagnosis, the "REASON" engine outputs a Causal SCM and CausalSHAP values that correlate with known medical pathways.

**Acceptance Scenarios**:

1. **Given** a TB diagnosis, **When** the user views the report, **Then** the system attributes the risk to specific factors (e.g., "61% Malnutrition").
2. **Given** a suggested intervention, **When** the user asks for justification, **Then** the system shows the counterfactual impact (e.g., "If nutrition improves, TB probability drops to 31%").

---

### User Story 3 - Health Trajectory Projection (Priority: P3)

A patient with a chronic or infectious condition wants to see their future health outlook. The system uses a "Digital Twin" to simulate their health trajectory over the next 6-12 months under different scenarios.

**Why this priority**: Enables proactive care and motivates patient adherence to treatment.

**Independent Test**: Use the "PROJECT" layer (Neural ODE) on historical patient data (e.g., MIMIC-IV) and verify trajectory prediction accuracy.

**Acceptance Scenarios**:

1. **Given** a patient's current biomarkers, **When** the simulation is run, **Then** the system predicts time-to-event (e.g., "Active TB in 5 months") with calibrated uncertainty.
2. **Given** a potential treatment plan, **When** the twin is updated, **Then** it shows the modified trajectory (e.g., "Health stabilized for 18 months").

---

### User Story 4 - Intervention Optimization (Priority: P4)

A community health worker needs to decide the best next step for a patient with limited resources. The system recommends the most cost-effective intervention sequence (e.g., PHC referral, sputum test, or nutritional support).

**Why this priority**: Optimizes resource allocation in low-resource settings.

**Independent Test**: Verify that the RL "ACT" engine recommends actions with the highest QALY gain per rupee spent based on the Ayushman Bharat cost database.

**Acceptance Scenarios**:

1. **Given** a high-risk patient, **When** the system recommends a test, **Then** it prioritizes free/covered tests (e.g., AB-PMJAY sputum test) over private alternatives.
2. **Given** a list of actions, **When** the user selects "Minimum Cost", **Then** the system provides the most impactful zero-cost intervention.

---

### Edge Cases

- **Noisy Environments**: How does the system handle cough detection in a noisy home or clinic?
- **Low Light**: How does the rPPG/Visual engine handle poor lighting for skin/eye analysis?
- **Unknown Diseases**: How does the system signal uncertainty when it encounters a pattern it doesn't recognize?
- **Inconsistent History**: How does the Digital Twin handle large gaps in patient health records?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract HR, SpO2, HRV, and RR from facial video using chrominance-based rPPG (CHROM).
- **FR-002**: System MUST classify cough sounds into multi-class categories (TB, COVID, Pneumonia, Healthy) using an ensemble of acoustic deep learning models.
- **FR-003**: System MUST detect conjunctival pallor and scleral jaundice from facial images using specialized computer vision models optimized for medical imaging.
- **FR-004**: System MUST perform causal discovery (FCI/PCMCI) on longitudinal patient data to establish disease pathways.
- **FR-005**: System MUST generate diverse counterfactual explanations (DiCE) to suggest actionable health changes.
- **FR-006**: System MUST simulate patient digital twins using Neural ODEs (Latent ODE) for cardiopulmonary, metabolic, and infectious diseases.
- **FR-007**: System MUST optimize intervention plans using Reinforcement Learning (PPO) against a QALY-based reward function.
- **FR-008**: System MUST integrate with the ABDM/ABHA health stack for fetching history and pushing diagnostic reports (FHIR R4).
- **FR-009**: System MUST support privacy-preserving collaborative learning to allow hospitals to contribute to global model improvement without exposing raw patient data.
- **FR-010**: All sensing and initial inference MUST be capable of running fully offline on the mobile device to ensure accessibility in areas without connectivity.

### Key Entities *(include if feature involves data)*

- **Patient**: Represents the individual, including demographics, ABHA ID, and current physiological state.
- **Biomarker**: A quantitative measurement (Acoustic, Visual, rPPG, or IMU) extracted from sensors.
- **Causal Graph**: A DAG representing the relationships between health factors and outcomes.
- **Digital Twin**: A mathematical model (Neural ODE) of a patient's physiological state over time.
- **Intervention**: A clinical or lifestyle action (e.g., test, treatment, counseling) with associated cost and impact.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: TB detection sensitivity >82% and specificity >79% in clinical validation with 50+ patients.
- **SC-002**: Passive sensing (Layer 1) completes processing in under 45 seconds on a mid-range Android phone.
- **SC-003**: Neural ODE trajectory prediction achieves MAE <0.5% for HbA1c over 6 months (metabolic twin).
- **SC-004**: Zero raw patient data leaves the device for Layer 1 sensing; zero raw data leaves hospital nodes during Federated Learning.

## Assumptions

- **Hardware**: Users have access to a smartphone with at least a 720p camera and 44.1kHz microphone.
- **Data Access**: Permission will be obtained to access MIMIC-IV and NHANES datasets for model training.
- **Clinical Partnership**: KMC Mangalore will serve as the validation site and provide ground-truth diagnostic data.
- **Regulatory**: The system is intended as a screening/support tool, not a final diagnostic device (initially CDSCO Class B pathway).
