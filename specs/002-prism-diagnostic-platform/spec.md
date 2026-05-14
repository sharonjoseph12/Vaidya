# Feature Specification: PRISM — Passive Readings → Intelligent Scalable Medicine

**Feature Branch**: `002-prism-diagnostic-platform`

**Created**: 2026-05-14

**Status**: Draft

**Input**: User description: "PRISM — a smartphone-based, offline-capable, multimodal AI diagnostic platform that detects diseases from passive biomarker observation (audio, visual, rPPG, gait), explains diagnoses through causal reasoning, simulates patient health trajectories, and recommends optimal interventions — targeting underserved populations in India with zero hardware cost."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Passive Health Scan (Priority: P1)

A community health worker (ASHA worker) in a rural Indian village opens the PRISM application on a standard Android smartphone. She holds the phone camera facing a patient for 30 seconds. During this passive capture, the system simultaneously extracts heart rate, blood oxygen saturation, respiratory rate, and heart rate variability from the patient's facial video, analyzes ambient cough and breathing sounds through the microphone, and captures visual indicators of anemia, jaundice, and cyanosis from the patient's face. All processing happens on-device — no internet connection is required. The system produces a preliminary health assessment within 60 seconds of the capture completing.

**Why this priority**: This is the foundational user interaction. Without reliable on-device passive sensing, no subsequent layer (causation, trajectory, intervention) can function. This delivers immediate screening value even as a standalone feature.

**Independent Test**: Can be fully tested by performing a 30-second phone scan on a participant and verifying that the system outputs heart rate, SpO2, respiratory rate, and preliminary disease risk scores — all without internet connectivity.

**Acceptance Scenarios**:

1. **Given** a patient is seated in front of the phone camera in normal indoor lighting, **When** the ASHA worker initiates a 30-second passive scan, **Then** the system extracts heart rate (within ±3 BPM of reference), SpO2 (within ±3% of reference), and respiratory rate (within ±3 breaths/min of reference) from facial video alone.
2. **Given** a patient coughs during the capture session, **When** the audio is processed, **Then** the system detects and classifies the cough pattern and outputs a disease probability distribution across supported conditions (TB, pneumonia, COVID, asthma, COPD, whooping cough, healthy, uncertain).
3. **Given** a patient with clinically confirmed anemia (Hb < 10 g/dL), **When** the system analyzes facial and conjunctival pallor from the video, **Then** the system flags anemia risk with at least 85% sensitivity.
4. **Given** the phone has no active internet connection, **When** the passive scan completes, **Then** all sensing and preliminary assessment runs entirely on-device with no errors or degraded functionality.

---

### User Story 2 - Causal Diagnosis Explanation (Priority: P2)

After the passive scan completes, a primary healthcare physician reviews the PRISM diagnostic report on the clinical dashboard. Instead of seeing only "TB probability: 79%", the physician sees a causal attribution breakdown: malnutrition contributes 38% of susceptibility, poor ventilation 24%, prior infection 21%, and genetic factors 17%. The system also presents counterfactual scenarios: "If nutritional status improves from 2/10 to 6/10, TB probability drops from 79% to 31%." This transforms the diagnosis from a black-box correlation into an actionable, explainable causal chain.

**Why this priority**: Explainability is what differentiates PRISM from every other AI diagnostic tool. Clinicians will not trust or adopt a system that cannot explain its reasoning. This is the core competitive moat.

**Independent Test**: Can be tested by providing a patient's biomarker data and verifying that the system outputs a causal attribution graph with percentage contributions and at least 3 diverse counterfactual scenarios.

**Acceptance Scenarios**:

1. **Given** a patient's biomarker data has been extracted by Layer 1, **When** the causal engine processes the data, **Then** the system outputs a causal attribution breakdown listing the top contributing factors with percentage weights that sum to 100%.
2. **Given** a causal model has been fitted, **When** the user requests counterfactual explanations, **Then** the system generates at least 3 diverse counterfactual scenarios showing how changing specific modifiable factors would alter the diagnosis probability.
3. **Given** a patient with multiple risk factors, **When** the causal graph is displayed, **Then** the visualization shows directed causal relationships between factors (not just correlations) with confidence levels for each causal link.

---

### User Story 3 - Health Trajectory Simulation (Priority: P3)

A physician wants to understand what will happen to a patient over the next 6–12 months. The system's digital twin — trained on hundreds of thousands of patient records — simulates two trajectories: one without intervention and one with the recommended intervention. The physician sees a clear chart: "Without intervention, this patient develops active TB in approximately 5 months. With a nutritional supplementation program, that window extends to approximately 19 months." The trajectory includes calibrated uncertainty bands so the physician understands the range of possible outcomes.

**Why this priority**: Trajectory prediction is a powerful differentiator but depends on Layers 1 and 2 functioning correctly. It transforms PRISM from a diagnostic tool into a prognostic tool — a significant step up.

**Independent Test**: Can be tested by inputting a patient's current biomarker state and verifying the system produces a time-series trajectory chart with confidence intervals for at least 6 months into the future.

**Acceptance Scenarios**:

1. **Given** a patient's current biomarker state and historical records, **When** the digital twin simulation runs, **Then** the system produces a trajectory chart projecting key biomarker values for at least 6 months with 90% confidence intervals.
2. **Given** a simulated intervention (e.g., nutritional supplementation), **When** the intervention is applied to the digital twin, **Then** the system generates a counterfactual trajectory showing the projected impact of that intervention on the patient's health timeline.
3. **Given** a patient with irregular visit history (non-uniform time intervals between observations), **When** the system processes this data, **Then** the trajectory model handles irregular time series without requiring uniformly spaced data points.

---

### User Story 4 - Intervention Recommendation (Priority: P4)

After reviewing the diagnosis, causal explanation, and trajectory, the physician (or ASHA worker) requests an intervention recommendation. The system suggests ranked options: Option A (₹0 — sputum AFB test at the nearest Primary Health Center, 1.2 km away, free under Ayushman Bharat), Option B (₹400 — balanced approach with nutritional supplementation and monitoring), Option C (₹1,400 — maximum health gain with specialist referral). Each option includes expected health outcome improvement, cost, nearest facility, and potential side effects. The system considers the patient's socioeconomic status and available government health schemes.

**Why this priority**: Intervention optimization is the final "so what?" layer that makes PRISM actionable. However, it depends on all prior layers for its inputs.

**Independent Test**: Can be tested by providing a diagnosed patient profile and verifying the system outputs at least 2 ranked intervention options with cost, expected outcome, and nearest facility information.

**Acceptance Scenarios**:

1. **Given** a patient with a completed diagnosis and trajectory projection, **When** the intervention optimizer runs, **Then** the system outputs at least 2 ranked intervention plans with cost estimates (including government scheme coverage), expected health outcome improvement, and nearest facility details.
2. **Given** a patient from a low-income bracket, **When** the system recommends interventions, **Then** free or subsidized options available under government health schemes (e.g., Ayushman Bharat, DOTS) are prioritized and clearly labeled.
3. **Given** diagnostic uncertainty exceeds a defined threshold, **When** the system generates recommendations, **Then** the top recommendation is the single diagnostic test that would most reduce uncertainty, along with an explanation of the expected information gain.

---

### User Story 5 - Health Record Integration (Priority: P5)

A patient with an ABHA (Ayushman Bharat Health Account) ID consents to share their historical health records with PRISM. The system fetches past diagnoses, lab results, and medication history. This historical data enriches the digital twin, making trajectory predictions significantly more accurate. After PRISM completes its assessment, the diagnostic report is pushed back to the patient's ABHA health locker as a standard clinical record, accessible to any future healthcare provider.

**Why this priority**: National health stack integration provides long-term value and competitive differentiation but is not required for core diagnostic functionality.

**Independent Test**: Can be tested by using the ABDM sandbox environment to fetch a test patient's records and verify that PRISM enriches its assessment with historical data, then pushes a diagnostic report back to the patient's health locker.

**Acceptance Scenarios**:

1. **Given** a patient provides their ABHA ID and grants data-sharing consent, **When** the system queries the ABDM gateway, **Then** historical health records (diagnoses, lab results, prescriptions) are retrieved and parsed.
2. **Given** historical records have been fetched, **When** the digital twin processes this data, **Then** trajectory prediction accuracy improves measurably compared to the no-history baseline.
3. **Given** a PRISM diagnostic assessment is complete, **When** the report is finalized, **Then** it is pushed to the patient's ABHA health locker as a valid clinical record in the standard health data format.

---

### User Story 6 - Privacy-Preserving Collaborative Learning (Priority: P6)

A hospital administrator agrees to participate in PRISM's federated learning network. A local training client runs on the hospital's server, training the PRISM model on the hospital's patient data without any raw data leaving the hospital. Only encrypted model weight updates are transmitted to the central aggregation server. Over time, all participating hospitals benefit from improved model accuracy without compromising patient privacy or regulatory compliance.

**Why this priority**: Federated learning is essential for long-term model improvement and hospital adoption, but it is not required for the initial product to function. It is the scalability and trust layer.

**Independent Test**: Can be tested by simulating 2+ hospital nodes, each training on local data, and verifying that the aggregated global model improves in accuracy over rounds without any raw patient data being transmitted.

**Acceptance Scenarios**:

1. **Given** a hospital node is configured with local patient data, **When** federated training runs for multiple rounds, **Then** the global model accuracy improves over successive rounds.
2. **Given** the federated learning protocol is active, **When** network traffic is monitored, **Then** no raw patient data or identifiable features are transmitted — only model weight updates.
3. **Given** the privacy budget is set to a defined level, **When** differential privacy noise is applied to model updates, **Then** the formal privacy guarantee is mathematically verifiable.

---

### Edge Cases

- What happens when the patient is in extremely low lighting conditions (< 50 lux) during the facial video capture?
- How does the system handle significant patient movement (e.g., children, agitated patients) during the 30-second scan?
- What happens when the patient's cough is masked by loud ambient noise (e.g., traffic, crowd)?
- How does the system perform on phone models with lower-quality cameras (< 8 MP, < 30 fps)?
- What happens when the patient has skin conditions or makeup that significantly alters facial color analysis?
- How does the system handle patients with no prior health records (no ABHA history)?
- What happens when the causal model encounters a condition outside its training distribution (out-of-distribution detection)?
- How does the system behave when only a subset of modalities is available (e.g., audio only, no video)?
- What happens if the patient refuses consent for data sharing but still wants a diagnostic assessment?
- How does the system handle concurrent scans on multiple patients at the same facility?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST extract heart rate, blood oxygen saturation (SpO2), heart rate variability (HRV), and respiratory rate from a 30-second facial video captured on a standard smartphone camera (minimum 720p, 24 fps).
- **FR-002**: The system MUST detect and classify cough sounds into at least 8 categories (TB, COVID, pneumonia, whooping cough, asthma, COPD, healthy, uncertain) from ambient audio captured through the phone microphone.
- **FR-003**: The system MUST detect visual indicators of anemia (conjunctival pallor), jaundice (scleral yellowing), and cyanosis (lip discoloration) from facial video analysis.
- **FR-004**: The system MUST perform gait analysis from 10-step walking captures using the phone's accelerometer and gyroscope to detect indicators of neurological conditions (Parkinson's, stroke risk, neuropathy).
- **FR-005**: The system MUST fuse outputs from all available sensor modalities (audio, visual, rPPG, IMU) using a cross-modal attention mechanism to produce a unified disease probability distribution.
- **FR-006**: The system MUST perform all biomarker sensing and preliminary disease classification entirely on-device without requiring an internet connection.
- **FR-007**: The system MUST construct causal attribution graphs showing the directed causal relationships between risk factors and disease outcomes, using structural causal models rather than correlational analysis.
- **FR-008**: The system MUST generate at least 3 diverse counterfactual explanations per diagnosis, showing how modifying specific factors would change the diagnostic outcome.
- **FR-009**: The system MUST simulate patient health trajectories for at least 6 months into the future using a continuous-time dynamical model that handles irregularly spaced observations.
- **FR-010**: The system MUST display calibrated uncertainty bounds (90% confidence intervals) on all trajectory predictions and disease probability estimates using conformal prediction methods.
- **FR-011**: The system MUST recommend ranked intervention plans that include cost estimates, expected health outcome improvements (measured in quality-adjusted life years), nearest facility locations, and potential side effects.
- **FR-012**: The system MUST integrate with India's ABDM/ABHA system to fetch patient health history (with consent) and push diagnostic reports back to the patient's digital health locker.
- **FR-013**: The system MUST support federated learning, enabling hospitals to contribute to model improvement without transmitting raw patient data — only encrypted model weight updates.
- **FR-014**: The system MUST apply differential privacy with a formally defined privacy budget to all federated model updates.
- **FR-015**: The system MUST never write raw audio or video data to persistent storage on the device — all sensor data must be processed in-memory and discarded after feature extraction.
- **FR-016**: The system MUST produce a printable/downloadable clinical diagnostic report (in a standard document format) summarizing diagnosis, causal attribution, trajectory, and recommended interventions.
- **FR-017**: The system MUST perform adaptive lighting normalization (white balance correction, histogram equalization, skin tone calibration) to maintain visual biomarker accuracy across diverse lighting conditions.
- **FR-018**: The system MUST provide graceful degradation when only a subset of modalities is available (e.g., audio-only mode if camera access is denied), clearly communicating reduced confidence to the user.
- **FR-019**: The system MUST display cost information for interventions that reflects availability under Indian government health schemes (Ayushman Bharat, DOTS, ICDS) with the nearest participating facility.
- **FR-020**: The system MUST support clinical validation by maintaining an audit trail of all diagnostic predictions alongside ground-truth outcomes for retrospective accuracy analysis.

### Key Entities

- **Patient**: The individual being assessed. Attributes include demographics (age, sex, location, socioeconomic tier), ABHA ID (optional), biomarker readings (current and historical), active conditions, and intervention history.
- **Diagnostic Session**: A single assessment instance. Captures the timestamp, raw biomarker features (not raw media), disease probability distribution, causal attribution graph, trajectory projections, intervention recommendations, uncertainty bounds, and the model version used.
- **Disease Model**: A supported diagnostic condition with its associated causal graph, biomarker feature set, classification thresholds, and clinical validation metrics. Examples: TB, anemia, pneumonia, dengue, cardiac risk, Parkinson's (early), COPD, asthma.
- **Intervention Plan**: A recommended action with cost, expected outcome, risk, nearest facility, and alignment with government health schemes.
- **Causal Graph**: A directed acyclic graph representing discovered causal relationships between risk factors and disease outcomes, with edge confidence levels and temporal lag information.
- **Digital Twin**: A patient-specific dynamical model representing the patient's health state as a continuous trajectory in latent space, capable of forward simulation and counterfactual intervention.
- **Hospital Node**: A participating institution in the federated learning network, with its own local data, training client, and privacy configuration.
- **Clinical Report**: A structured diagnostic output containing diagnosis, causal explanation, trajectory chart, intervention options, and uncertainty quantification — compliant with standard health data exchange formats.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The system detects TB from passive biomarker observation (audio + visual + rPPG) with at least 82% sensitivity and 79% specificity, validated against a cohort of at least 50 patients with confirmed diagnoses.
- **SC-002**: The system detects anemia from conjunctival and facial pallor analysis with at least 85% sensitivity and 82% specificity.
- **SC-003**: Heart rate extracted via remote photoplethysmography is within ±3 BPM of a reference pulse oximeter reading in 90% of test cases under standard indoor lighting.
- **SC-004**: SpO2 extracted via remote photoplethysmography is within ±3% of a reference pulse oximeter reading in 85% of test cases.
- **SC-005**: The complete passive scan and on-device assessment completes in under 90 seconds (30-second capture + 60-second processing) on a mid-range Android smartphone (2020 or newer, 4 GB RAM).
- **SC-006**: The system operates fully offline (no internet connection) for all core diagnostic functions (sensing, causal attribution, and preliminary risk scoring).
- **SC-007**: Trajectory predictions for key biomarkers (e.g., HbA1c for metabolic conditions) achieve a mean absolute error of less than 0.5 units at the 6-month prediction horizon.
- **SC-008**: At least 80% of clinicians reviewing PRISM's causal explanations rate them as "clinically useful" or "highly useful" in a structured feedback survey.
- **SC-009**: The system correctly identifies the most impactful modifiable risk factor (the factor whose modification produces the largest reduction in disease probability) in at least 75% of validated cases.
- **SC-010**: Intervention cost estimates are accurate to within ±15% of actual costs at government and private facilities.
- **SC-011**: The on-device compressed model size does not exceed 50 MB total across all diagnostic modules.
- **SC-012**: Federated learning across 2+ simulated hospital nodes demonstrates measurable model accuracy improvement (at least 2 percentage points) over 10 training rounds without any raw patient data leaving the hospital node.
- **SC-013**: The complete diagnostic report is generated and available for download or ABDM push within 3 minutes of scan completion.
- **SC-014**: The system achieves an overall diagnostic AUC-ROC of at least 0.83 across all supported conditions when evaluated on a held-out test set.

## Assumptions

- **Target devices**: The primary deployment target is Android smartphones (2020 or newer) with at least a 720p front camera, a functional microphone, and accelerometer/gyroscope sensors. iOS support is out of scope for the initial version.
- **Lighting conditions**: Facial video capture assumes standard indoor lighting (approximately 200–1000 lux). Performance in extreme low-light or direct sunlight is expected to degrade and will be communicated to the user.
- **Patient cooperation**: The 30-second passive scan assumes the patient can remain relatively still and seated. Pediatric patients or patients who cannot remain still will have reduced accuracy, and the system will alert the user.
- **Language**: The user interface is in English for the initial version. Hindi and Kannada localization are future enhancements.
- **Clinical validation scope**: Initial clinical validation is limited to a 50-patient retrospective cohort from a single hospital. Broader multi-site validation is a post-launch activity.
- **ABDM integration**: ABDM integration initially uses the sandbox environment. Production ABDM integration requires separate registration as a Health Information Provider (HIP), which is a post-launch regulatory process.
- **Disease scope**: The initial release targets 8 conditions: TB, pneumonia, anemia, jaundice/hepatitis, dengue, COPD, asthma, and cardiac risk. Additional conditions (Parkinson's, depression, neuropathy) are future enhancements.
- **Data collection**: The proprietary India-specific dataset (target: 500 samples) is collected under IRB approval from the partnering medical institution with full informed consent and data de-identification.
- **Model training compute**: Training is performed on cloud GPU instances (e.g., Colab Pro). On-device inference uses compressed/quantized models.
- **Regulatory status**: The initial version is a research prototype for hackathon demonstration and clinical validation study. Regulatory approval (CDSCO Class B medical device) is a separate, post-competition process.
- **Consent model**: All patient data collection and ABDM record access requires explicit, informed consent compliant with India's Digital Personal Data Protection Act 2023.
- **Internet for advanced features**: While core diagnostic sensing and causal attribution work offline, advanced features (trajectory simulation with cloud models, ABDM integration, federated learning participation) require internet connectivity.
