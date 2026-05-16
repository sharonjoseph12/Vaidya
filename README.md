# PRISM — Passive Readings → Intelligent Scalable Medicine

> **Turning every $50 smartphone into a contactless, clinical-grade triage clinic for global population health.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://python.org)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-blue)](https://flutter.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)](https://fastapi.tiangolo.com)
[![ABDM Compliant](https://img.shields.io/badge/ABDM-FHIR%20R4-orange)](https://abdm.gov.in)

---

## The Problem

Preventative healthcare is gated behind expensive hardware. The global bottom 4 billion — rural populations across India and beyond — rely on reactive medicine, visiting a clinic only after severe symptoms appear. Existing AI diagnostic tools are **black boxes**: they spit out a risk score with no explanation, generating clinical mistrust. And no solution currently tracks how environmental stressors like poor sanitation silently degrade a community's baseline immune and respiratory health over time.

---

## What is PRISM?

PRISM is a **100% contactless, multimodal health-screening AI** that requires zero external hardware. Using only the standard camera and microphone of a basic Android smartphone, PRISM delivers a complete preventative health scan in under 30 seconds.

Designed for India's public health ecosystem, PRISM empowers a single **ASHA (Accredited Social Health Activist) worker** to proactively screen 50+ villagers per day — mapping local sanitation and stress levels directly to respiratory vulnerability, and feeding into India's Ayushman Bharat Digital Mission (ABDM).

---

## Core Technical Architecture

PRISM processes health data in five tightly integrated phases:

### 1. Contactless Vitals Extraction — Vision Pipeline

Remote Photoplethysmography (rPPG), no hardware sensors required.

- A 10-second face video is captured via the device camera.
- **MediaPipe** isolates high-capillary regions (forehead and upper cheeks).
- The spatial average of the **Green Pixel Channel** is extracted (hemoglobin strongly absorbs green light).
- The raw signal is detrended and passed through a **6th-order Butterworth Bandpass Filter** (0.75 Hz – 4.0 Hz).
- **Fast Fourier Transform (FFT)** extracts clinical-grade:
  - Heart Rate (HR)
  - Heart Rate Variability (HRV via RMSSD)
  - Baseline Stress Index

### 2. Acoustic Fingerprinting — Audio Pipeline

The patient coughs 3 times into the microphone.

- Audio is downsampled to **16 kHz**.
- **Librosa** extracts 13 **Mel-Frequency Cepstral Coefficients (MFCCs)** and **Zero-Crossing Rates (ZCR)**.
- Acoustic features are passed to an **XGBoost classifier** to detect micro-vocal tract abnormalities and assign a **Respiratory Risk Score**.
- A fine-tuned **YAMNet** model further classifies cough severity and TB suspect probability.

### 3. Cross-Modal AI Fusion — The Brain

PRISM reasons like a clinician, cross-referencing signal channels:

- A custom **PyTorch Multi-Head Attention layer** fuses vision and audio features.
- If camera confidence is low (poor lighting), the attention mechanism dynamically **shifts weight to acoustic biomarkers** — preventing false positives and self-balancing for rural environments.

### 4. Glass-Box Explainer — Causal AI via DoWhy

PRISM's defining differentiator: not a black box.

- **DoWhy Causal Inference** generates a **Directed Acyclic Graph (DAG)** mapping root causes.
- The system mathematically proves *why* a patient is at risk with clinician-readable output such as:

  > *"High environmental stress and poor sanitation exposure is severely suppressing HRV, acting as the primary confounder for current respiratory vulnerability."*

- **tigramite PCMCI** runs causal discovery on time-series signals; DoWhy handles short-signal fallback.
- SHAP-based attribution provides an honest lightweight fallback when causal discovery times out.

### 5. Future Trajectory Forecasting — Digital Twin

- A **Neural ODE** (via `torchdiffeq`) simulates the patient's disease progression over 30 days.
- Four intervention scenarios are modeled in parallel: `none`, `medication`, `lifestyle`, `emergency`.
- **Uncertainty quantification**: 50 Monte Carlo runs produce 5th–95th percentile confidence bands.
- A physiologically grounded **Lotka-Volterra style ODE fallback** operates if no pre-trained checkpoint exists.

---

## Visual Biomarker Detection

Beyond vitals, PRISM detects clinical signs from the face:

| Biomarker | Method | ROI |
|-----------|--------|-----|
| Anemia | Conjunctival pallor (LAB color + MobileNetV3) | Inner eyelid landmarks |
| Jaundice | Scleral icterus (LAB color + MobileNetV3) | Sclera around iris |
| Cyanosis | Lip and fingernail color analysis | Lip landmarks |

MediaPipe FaceMesh (468 landmarks) drives ROI extraction. An ensemble of CNN + XGBoost on LAB color features produces a final score per biomarker.

---

## Clinical Interface

Built in **Flutter (Riverpod)** with a cyber-medical dark mode aesthetic:

- **Live Scanning HUD** — real-time facial bounding boxes and acoustic waveform visualization.
- **Causal Flowcharts** — animated dashed lines showing how stress flows into immune suppression.
- **Symptom Questionnaire** — localized in English, Hindi, Kannada, and Tamil with voice prompts via Web Speech API.
- **"God-Mode" Fail-Safe** — a local mock switch bypasses cloud APIs for edge deployments and demo environments with no connectivity.

---

## Real-World Impact

### ASHA Worker Scale
Deploying PRISM on an ASHA worker's phone allows a village of 500 people to be screened weekly at **zero marginal cost**.

### Sanitation Early Warning
By tracking regional clusters of immune suppression and respiratory distress, PRISM functions as an **early-warning radar** for local sanitation failures — e.g., contaminated water causing mass immune degradation.

### Outbreak Detection
Automated cluster analysis runs every 6 hours:

| Alert Type | Trigger |
|------------|---------|
| TB Cluster | ≥ 3 patients in same village with TB risk > 0.60 in 7 days |
| Fever Cluster | ≥ 5 patients reporting fever in 3 days |
| Low SpO₂ Cluster | ≥ 3 patients with SpO₂ < 92% in 5 days |
| Anemia Cluster | ≥ 8 patients with anemia score > 0.65 in 30 days |

District health officers and CMOs are notified via WhatsApp Business API with a structured alert.

### ABDM Compliance
The FastAPI backend outputs **FHIR R4 DiagnosticReport** payloads for full Ayushman Bharat Digital Mission interoperability — generating localized health IDs and clinical registries. LOINC-coded Observation resources cover HR (8867-4), SpO₂ (59408-5), RR (9279-1), and HRV (80404-7).

---

## Federated Learning

Patient data never leaves the device. PRISM uses **Flower (flwr) Federated Averaging** to train the YAMNet cough classifier across distributed PHC/hospital nodes:

- Minimum 3 nodes before a training round starts.
- **Differential privacy**: Gaussian noise (σ = 0.01) applied to model updates before aggregation.
- Privacy budget tracked via **RDP accountant** (max ε = 10.0, DPDP Act compliant).
- Client nodes add local DP noise (ε_local = 2.0) to gradients before transmission.
- Clients require a minimum of 10 local samples before participating.
- Deployable on **Raspberry Pi 4 (2GB RAM)** at a PHC.

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Flutter, Riverpod, fl_chart, google_mlkit |
| **Backend** | Python 3.11, FastAPI, Supabase, PostgreSQL 15, Redis 7 |
| **Machine Learning** | PyTorch, torchdiffeq, DoWhy, tigramite, MediaPipe, Librosa, XGBoost, YAMNet (TFLite) |
| **Android** | Kotlin, Jetpack Compose, CameraX, TFLite, Room, WorkManager, Retrofit |
| **AI Services** | Gemini (SOAP notes, insights, translation), Whisper (multilingual transcription) |
| **Federated Learning** | Flower (flwr), dp-accounting |
| **Deployment** | Railway, Docker, Nginx, GitHub Actions CI/CD |
| **Monitoring** | Prometheus, Grafana, Alertmanager |

---

## API Overview

```
POST   /auth/login                    # Email + password (doctors/admins)
POST   /auth/otp/send                 # Phone OTP (ASHA workers)
POST   /patients/                     # Register patient
GET    /patients/{id}/timeline        # Longitudinal health history
GET    /patients/{id}/vitals-trend    # HR, SpO₂, HRV over time
POST   /scans/                        # Submit scan → triggers async diagnosis
GET    /scans/{id}/status             # Polling: processing | complete | failed
POST   /scans/{id}/export-pdf         # Clinically styled PDF report
POST   /consultations/{id}/process    # Gemini SOAP note generation
GET    /review/queue                  # Unreviewed diagnoses, risk-sorted
POST   /abdm/push/{scan_id}          # Push FHIR bundle to ABDM
GET    /fl/status                     # Federated learning status
GET    /outbreak/alerts               # Active cluster alerts
GET    /health                        # System health check
```

Full OpenAPI docs available at `/docs` when running locally.

---

## Multilingual Support

PRISM supports four languages across the full user experience:

| Language | Code | Primary User |
|----------|------|-------------|
| English | `en` | Doctors, admins |
| Hindi | `hi` | ASHA workers (North India) |
| Kannada | `kn` | ASHA workers (Karnataka) |
| Tamil | `ta` | ASHA workers (Tamil Nadu) |

All symptom questionnaires, scan instructions, risk labels, intervention recommendations, and emergency messages are fully localized. Patient summaries are generated in the patient's language via Gemini with medical terminology awareness.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend build)
- Docker & Docker Compose
- PostgreSQL 15
- Redis 7

### Quickstart

```bash
# Clone the repository
git clone https://github.com/your-org/prism.git
cd prism

# Copy environment configuration
cp .env.example .env
# Edit .env with your API keys and database credentials

# Start all services
docker-compose up -d

# Run database migrations
alembic upgrade head

# Access the API
curl http://localhost:8000/health
```

### Environment Variables

Key variables required in `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/prism

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
JWT_SECRET_KEY=your-secret-key

# AI Services
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key         # For Whisper API fallback

# ABDM
ABDM_CLIENT_ID=your-abdm-client-id
ABDM_CLIENT_SECRET=your-abdm-secret
ABDM_ENVIRONMENT=sandbox               # or production

# WhatsApp Business
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_PHONE_NUMBER_ID=your-id

# SMS (ASHA OTP)
FAST2SMS_API_KEY=your-key

# Frontend
FRONTEND_URL=http://localhost:5173
```

See `.env.example` for the complete list of 40+ variables.

---

## Build Sequence

The project is built in 7 phases across 23 prompts. See [`BUILD_SEQUENCE.md`](BUILD_SEQUENCE.md) for the complete implementation guide.

| Phase | Scope |
|-------|-------|
| Phase 1 | Database schema, auth, core API endpoints, rPPG & cough signal processing |
| Phase 2 | Causal engine, digital twin, RL intervention optimizer |
| Phase 3 | YAMNet cough classifier, visual biomarker detection |
| Phase 4 | Gemini SOAP notes, Whisper transcription, longitudinal timeline |
| Phase 5 | Outbreak early warning, federated learning, PDF reports, ABDM integration |
| Phase 6 | Unified doctor dashboard, multilingual support, WhatsApp sharing, Android app |
| Phase 7 | Full FastAPI assembly, production deployment, CDSCO documentation |

---

## Regulatory & Compliance

PRISM is designed for **CDSCO Class B Medical Device** classification (Software as a Medical Device, SaMD) under Medical Devices Rules 2017. Key compliance points:

- **IEC 62304** — Software lifecycle documentation
- **IEC 62366** — Usability engineering (ASHA worker studies)
- **DPDP Act** — Differential privacy, audit logging, WhatsApp opt-in consent
- **CERT-In Guidelines** — Cybersecurity controls
- **ABDM / FHIR R4** — Health record interoperability
- All AI-generated reports carry the disclaimer: *"This report is AI-generated from smartphone sensors. Clinical confirmation by a qualified doctor is required."*

---

## Acknowledgements

- National Health Authority (NHA) — ABDM / Ayushman Bharat framework
- IISc — Coswara dataset for cough research
- COUGHVID — Open cough audio dataset (Zenodo)
- Google — MediaPipe, YAMNet
- Flower (flwr) — Federated learning framework

---

> *PRISM is not a substitute for professional medical advice, diagnosis, or treatment. All outputs require confirmation by a qualified healthcare provider. Not for medico-legal use.*
