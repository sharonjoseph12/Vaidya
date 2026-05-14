# Quickstart: PRISM Diagnostic Platform

## Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Redis (if running Celery locally without Docker)

## Setup
1. **Backend**:
   ```bash
   cd prism/backend
   python -m venv venv
   source venv/bin/activate # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8000
   ```
2. **Workers**:
   ```bash
   cd prism/backend
   celery -A workers.celery_tasks worker --loglevel=info
   ```
3. **Frontend**:
   ```bash
   cd prism/frontend
   npm install
   npm run dev
   ```

## Demo Fallback
If the ML inference service breaks, the system will automatically fall back to serving `DEMO_PATIENT_RESULT` for any requests using the ID `demo-patient-id`.
