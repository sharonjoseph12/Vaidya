# Research: PRISM Diagnostic Platform

## Context & Unknowns
The implementation plan for PRISM outlines a robust Next.js and FastAPI architecture. A new requirement mandates a fallback mechanism: "If any service is broken → return realistic hardcoded response for the DEMO PATIENT ONLY". 

### 1. Hardcoded Demo Response Handling
**Decision**: Implement a fallback mechanism inside the `inference_service.py` or the Celery worker task (`run_prism_analysis`) that catches exceptions and returns a predefined `DEMO_PATIENT_RESULT` if the request originates for a demo patient session.
**Rationale**: This ensures that during critical presentations, any timeout or failure in the complex ML pipelines (audio, visual, trajectory) does not break the frontend experience.
**Alternatives considered**:
- Frontend mock: Rejected because the frontend should remain agnostic to whether the data is real or mocked to test the full API layer.
- Static JSON file: Rejected in favor of a Python dictionary constant (`DEMO_PATIENT_RESULT`) within the service layer for easier maintenance and type-safety with Pydantic models.

### 2. Demo Patient Identification
**Decision**: Use a specific session ID or patient ID prefix (e.g., `demo-patient-id`) to toggle the fallback logic.
**Rationale**: Avoids accidentally serving mock data to real clinical assessments.
**Alternatives considered**:
- Environment variable toggle: Too broad; affects all requests.
- Header flag: Could work, but using the existing `session_id` or `patient_id` passed during the analysis invocation is simpler.

## Conclusion
The `DEMO_PATIENT_RESULT` will be integrated into the backend service layer to gracefully handle failures for demo scenarios. All other needs are resolved.
