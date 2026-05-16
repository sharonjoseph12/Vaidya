"""
PRISM API — Lightweight Dev Server
No ML models, no Supabase, no Redis required.
Returns realistic dynamic data for frontend development.
Run: python backend/dev_server.py
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import asyncio
import json
import time
import random
import logging
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prism-dev")

app = FastAPI(
    title="PRISM API (Dev)",
    description="Lightweight dev server — no external services needed.",
    version="1.0.0-dev",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# In-Memory Store
# ============================================================

PATIENTS = {
    "demo-patient-001": {
        "id": "demo-patient-001",
        "abha_id": "91-1234-5678-9012",
        "created_at": "2026-05-14T10:00:00Z",
        "consent_given": True,
        "demographics": {"name": "Rajesh Kumar", "age": 42, "sex": "M", "location": "Mangalore, Karnataka"},
        "sessions_count": 3,
        "last_session_date": "2026-05-14T10:30:00Z",
    },
    "demo-patient-002": {
        "id": "demo-patient-002",
        "abha_id": "91-9876-5432-1098",
        "created_at": "2026-05-13T08:15:00Z",
        "consent_given": True,
        "demographics": {"name": "Priya Sharma", "age": 28, "sex": "F", "location": "Dharwad, Karnataka"},
        "sessions_count": 1,
        "last_session_date": "2026-05-13T09:00:00Z",
    },
    "demo-patient-003": {
        "id": "demo-patient-003",
        "abha_id": "91-5555-6666-7777",
        "created_at": "2026-05-12T14:30:00Z",
        "consent_given": True,
        "demographics": {"name": "Mohammed Ali", "age": 55, "sex": "M", "location": "Udupi, Karnataka"},
        "sessions_count": 2,
        "last_session_date": "2026-05-12T15:45:00Z",
    },
}

SESSIONS = {}

# ============================================================
# Result Builder — realistic but NO hardcoded disease values
# ============================================================

def build_result(session_id: str, patient_features: dict) -> dict:
    """
    Build a diagnostic result using ALL available signals.
    Disease probabilities are computed from:
      1. Symptom questionnaire answers (cough duration, fever, night sweats, weight loss, SOB)
      2. Measured rPPG vitals (HR, SpO2, HRV, RR) — sent by frontend from real camera analysis
      3. No hardcoded disease values — if no signals, returns empty disease_probabilities
    """
    # ── Extract signals ──────────────────────────────────────────────────────
    cough_dur = patient_features.get("cough_duration", "none")
    fever = bool(patient_features.get("fever", False))
    night_sweats = bool(patient_features.get("night_sweats", False))
    weight_loss = bool(patient_features.get("weight_loss", False))
    sob = bool(patient_features.get("shortness_of_breath", False))

    # Real measured vitals from rPPG (sent by frontend LiveVitalsPanel)
    measured_hr = patient_features.get("measured_hr")
    measured_spo2 = patient_features.get("measured_spo2")
    measured_hrv = patient_features.get("measured_hrv")
    measured_rr = patient_features.get("measured_rr")

    has_symptoms = any([cough_dur != "none", fever, night_sweats, weight_loss, sob])
    has_vitals = any([measured_hr, measured_spo2, measured_hrv, measured_rr])

    # ── Use real measured vitals if available, else None ─────────────────────
    hr = float(measured_hr) if measured_hr else None
    spo2 = float(measured_spo2) if measured_spo2 else None
    hrv = float(measured_hrv) if measured_hrv else None
    rr = float(measured_rr) if measured_rr else None

    # ── Disease probability engine ───────────────────────────────────────────
    # Only compute if we have at least symptoms OR vitals
    disease_probs = {}

    if has_symptoms or has_vitals:
        # TB risk: chronic cough + night sweats + weight loss + low SpO2
        tb_score = 0.0
        if cough_dur == ">4weeks": tb_score += 0.40
        elif cough_dur == "1-4weeks": tb_score += 0.18
        elif cough_dur == "<1week": tb_score += 0.05
        if night_sweats: tb_score += 0.18
        if weight_loss: tb_score += 0.18
        if fever: tb_score += 0.08
        if spo2 is not None and spo2 < 94: tb_score += 0.12  # low SpO2 adds risk
        if rr is not None and rr > 22: tb_score += 0.08      # elevated RR
        if tb_score > 0.08:
            disease_probs["TB"] = round(min(0.92, tb_score), 2)

        # Pneumonia: fever + SOB + elevated RR + low SpO2
        pneu_score = 0.0
        if fever: pneu_score += 0.28
        if sob: pneu_score += 0.22
        if cough_dur in ["<1week", "1-4weeks"]: pneu_score += 0.15
        if spo2 is not None and spo2 < 92: pneu_score += 0.20
        if rr is not None and rr > 24: pneu_score += 0.15
        if hr is not None and hr > 100: pneu_score += 0.08  # tachycardia
        if pneu_score > 0.12:
            disease_probs["Pneumonia"] = round(min(0.88, pneu_score), 2)

        # Dengue: fever + no chronic cough + tachycardia
        if fever and cough_dur == "none":
            dengue_score = 0.20
            if hr is not None and hr > 95: dengue_score += 0.15
            if hrv is not None and hrv < 20: dengue_score += 0.10  # low HRV in dengue
            disease_probs["Dengue"] = round(min(0.65, dengue_score), 2)

        # Asthma: SOB + cough + normal/elevated RR
        if sob and cough_dur != "none":
            asthma_score = 0.15
            if rr is not None and rr > 18: asthma_score += 0.12
            if spo2 is not None and spo2 < 96: asthma_score += 0.10
            disease_probs["Asthma"] = round(min(0.60, asthma_score), 2)

        # Cardiac risk: elevated HR + low HRV + SOB
        if hr is not None and hrv is not None:
            cardiac_score = 0.0
            if hr > 100: cardiac_score += 0.20
            if hrv < 15: cardiac_score += 0.20
            if sob: cardiac_score += 0.15
            if spo2 is not None and spo2 < 94: cardiac_score += 0.15
            if cardiac_score > 0.15:
                disease_probs["Cardiac_Risk"] = round(min(0.75, cardiac_score), 2)

        # Anemia: low HRV + tachycardia + pallor (no direct visual yet)
        if hr is not None and hrv is not None:
            anemia_score = 0.0
            if hr > 95: anemia_score += 0.15
            if hrv < 20: anemia_score += 0.10
            if weight_loss: anemia_score += 0.12
            if anemia_score > 0.15:
                disease_probs["Anemia"] = round(min(0.55, anemia_score), 2)

    # ── rPPG vitals for sense_results ────────────────────────────────────────
    primary = max(disease_probs, key=disease_probs.get) if disease_probs else None
    confidence = disease_probs.get(primary, 0.0) if primary else 0.0

    # ── Causal results (only if we have a diagnosis) ─────────────────────────
    causal_results = None
    if primary and confidence > 0.25:
        causal_results = {
            "attributions": {
                "malnutrition": round(random.uniform(0.25, 0.42), 2),
                "poor_ventilation": round(random.uniform(0.15, 0.28), 2),
                "prior_infection": round(random.uniform(0.10, 0.22), 2),
                "genetics_proxy": round(random.uniform(0.08, 0.16), 2),
            },
            "top_intervention": "nutritional_support",
            "intervention_effects": {"nutritional_support": 0.48, "improved_ventilation": 0.19},
            "patient_risk_factors": {k: v for k, v in patient_features.items() if not k.startswith("measured_")},
            "counterfactuals": [{
                "changes": {"nutrition_score": [2, 6]},
                "new_probability": round(confidence * 0.42, 2),
                "feasibility_score": 0.85,
                "n_features_changed": 1,
            }],
            "narrative": (
                f"{primary.replace('_', ' ')} risk: {confidence:.0%}. "
                f"{'Low SpO₂ (' + str(round(spo2, 1)) + '%) detected. ' if spo2 and spo2 < 94 else ''}"
                f"{'Elevated heart rate (' + str(round(hr)) + ' bpm). ' if hr and hr > 100 else ''}"
                f"Primary driver: malnutrition ({round(random.uniform(30, 42))}% contribution). "
                f"Improving nutrition could reduce risk by ~48%."
            ),
            "causal_graph_dot": f"digraph {{ malnutrition -> {primary.lower().replace(' ', '_')}; poor_ventilation -> {primary.lower().replace(' ', '_')}; }}",
        }

    # ── Twin trajectory ───────────────────────────────────────────────────────
    twin_trajectory = None
    if primary and confidence > 0.25:
        twin_trajectory = {
            "without_intervention": [
                {"month": m, "values": {f"{primary.lower().replace(' ', '_')}_prob": min(0.99, confidence + m * 0.022)}}
                for m in [0, 1, 2, 3, 6, 9, 12]
            ],
            "with_best_intervention": [
                {"month": m, "values": {f"{primary.lower().replace(' ', '_')}_prob": max(0.04, confidence - m * 0.055)}}
                for m in [0, 1, 2, 3, 6, 9, 12]
            ],
            "confidence_bands": {f"{primary.lower().replace(' ', '_')}_prob": [0.05, 0.12]},
            "months_to_critical": round(random.uniform(4, 7), 1),
            "months_to_critical_with_intervention": round(random.uniform(15, 24), 1),
            "intervention_applied": "nutritional_support",
        }

    # ── Intervention plan ─────────────────────────────────────────────────────
    intervention_plan = None
    if primary:
        test_map = {"TB": ("sputum_afb_test", 150), "Pneumonia": ("chest_xray", 350), "Dengue": ("ns1_antigen_test", 200)}
        test_name, test_cost = test_map.get(primary, ("blood_cbc", 250))
        intervention_plan = {
            "recommendations": [
                {
                    "rank": 1,
                    "intervention": test_name,
                    "description": f"Confirmatory test for {primary.replace('_', ' ')}",
                    "rationale": f"Confirms/rules out {primary.replace('_', ' ')} at minimal cost",
                    "cost_govt": 0,
                    "cost_private": test_cost,
                    "qaly_gain": 2.3,
                    "time_to_effect_days": 2,
                    "scheme": "RNTCP" if primary == "TB" else "NRHM",
                },
                {
                    "rank": 2,
                    "intervention": "nutritional_support",
                    "description": "ICDS nutrition program",
                    "rationale": "Addresses root cause — malnutrition",
                    "cost_govt": 0,
                    "cost_private": 800,
                    "qaly_gain": 1.8,
                    "time_to_effect_days": 30,
                    "scheme": "ICDS",
                },
            ],
            "pareto_options": [
                {"label": "Minimum cost", "cost": 0, "qaly_gain": 1.8, "risk": 0.02},
                {"label": "Balanced", "cost": 400, "qaly_gain": 2.9, "risk": 0.04},
                {"label": "Maximum benefit", "cost": 1400, "qaly_gain": 3.2, "risk": 0.08},
            ],
            "active_uncertainty_reduction": {
                "recommended_test": test_name.replace("_", " ").title(),
                "cost": 0,
                "expected_uncertainty_reduction": 0.47,
                "rationale": "Will reduce diagnostic uncertainty by 47%",
            },
        }

    return {
        "session_id": session_id,
        "status": "complete",
        "primary_diagnosis": primary,
        "confidence_score": round(confidence, 2) if confidence else None,
        "disease_probabilities": disease_probs,
        "sense_results": {
            "disease_probabilities": disease_probs,
            "rppg": {
                "hr": hr,
                "spo2": spo2,
                "hrv_rmssd": hrv,
                "rr": rr,
                "confidence": {},
            } if has_vitals else None,
            "audio": {
                "cough_detected": cough_dur != "none",
                "cough_count": 0 if cough_dur == "none" else random.randint(1, 5),
                "disease_probs": {},
                "breathing_rate": rr,
                "wheeze_detected": sob and random.random() > 0.6,
                "crackle_detected": fever and random.random() > 0.7,
            },
            "visual": {
                "jaundice_score": round(random.uniform(0.02, 0.10), 2),
                "anemia_score": round(random.uniform(0.04, 0.18), 2),
                "cyanosis_score": round(0.0 if (not spo2 or spo2 >= 94) else random.uniform(0.10, 0.30), 2),
                "dengue_flush_score": round(random.uniform(0.02, 0.12), 2),
                "pallor_score": round(random.uniform(0.04, 0.18), 2),
            },
            "uncertainty": {d: [max(0, p - 0.08), min(1, p + 0.08)] for d, p in disease_probs.items()},
            "modalities_available": (
                ["rppg"] if has_vitals else []
            ) + (["audio"] if cough_dur != "none" else []) + ["visual"],
            "processing_time_ms": random.randint(800, 2000),
        },
        "causal_results": causal_results,
        "twin_trajectory": twin_trajectory,
        "intervention_plan": intervention_plan,
        "uncertainty_bounds": {d: [max(0, p - 0.08), min(1, p + 0.08)] for d, p in disease_probs.items()},
        "processing_time_ms": random.randint(3000, 6000),
        "model_version": "prism-signal-v1.0",
        "offline_mode": False,
    }


# ============================================================
# Health
# ============================================================

@app.get("/health")
@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "version": "1.0.0-dev", "service": "prism-api"}


# ============================================================
# Patients
# ============================================================

@app.get("/api/v1/patients")
async def list_patients(page: int = 1, per_page: int = 20, search: str = "", risk_level: str = "all"):
    patients = list(PATIENTS.values())
    if search:
        q = search.lower()
        patients = [p for p in patients if
                    q in (p.get("demographics", {}).get("name", "") or "").lower() or
                    q in (p.get("abha_id", "") or "").lower()]
    return {"patients": patients, "total": len(patients), "page": page, "per_page": per_page}


@app.get("/api/v1/patients/{patient_id}")
async def get_patient(patient_id: str):
    if patient_id in PATIENTS:
        return PATIENTS[patient_id]
    raise HTTPException(404, "Patient not found")


@app.get("/api/v1/patients/{patient_id}/sessions")
async def get_patient_sessions(patient_id: str):
    return [s["result"] for s in SESSIONS.values()
            if s.get("patient_id") == patient_id and "result" in s]


class PatientCreate(BaseModel):
    abha_id: Optional[str] = None
    demographics: dict
    consent_given: bool = True
    consent_purpose: Optional[str] = None
    device_info: Optional[dict] = None


@app.post("/api/v1/patients", status_code=201)
async def create_patient(patient: PatientCreate):
    pid = f"patient-{uuid4().hex[:8]}"
    record = {
        "id": pid,
        "abha_id": patient.abha_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "consent_given": patient.consent_given,
        "demographics": patient.demographics,
        "sessions_count": 0,
        "last_session_date": None,
    }
    PATIENTS[pid] = record
    return record


# ============================================================
# Diagnostics
# ============================================================

@app.post("/api/v1/diagnostics/analyze", status_code=202)
async def analyze(
    patient_id: str = Form(default="demo-patient-001"),
    patient_features: str = Form(default="{}"),
    audio_file: UploadFile = File(default=None),
    video_file: UploadFile = File(default=None),
):
    session_id = str(uuid4())
    try:
        features = json.loads(patient_features)
    except Exception:
        features = {}

    SESSIONS[session_id] = {
        "status": "queued",
        "patient_id": patient_id,
        "created_at": time.time(),
        "result": build_result(session_id, features),
    }

    if patient_id in PATIENTS:
        PATIENTS[patient_id]["last_session_date"] = datetime.now(timezone.utc).isoformat()
        PATIENTS[patient_id]["sessions_count"] = PATIENTS[patient_id].get("sessions_count", 0) + 1

    logger.info("Analysis queued: session=%s patient=%s", session_id, patient_id)
    return {"session_id": session_id, "task_id": f"task-{uuid4().hex[:8]}", "status": "queued", "estimated_time_seconds": 8}


@app.get("/api/v1/diagnostics/results/{session_id}")
async def get_results(session_id: str):
    if session_id in SESSIONS and "result" in SESSIONS[session_id]:
        return SESSIONS[session_id]["result"]
    return build_result(session_id, {})


@app.get("/api/v1/diagnostics/stream/{session_id}")
async def stream(session_id: str):
    stages = [
        ("sensing", 0.25, "Layer 1 SENSE: Extracting rPPG, audio biomarkers, visual cues..."),
        ("reasoning", 0.50, "Layer 2 REASON: Building causal attribution graph..."),
        ("projecting", 0.75, "Layer 3 PROJECT: Simulating digital twin trajectory..."),
        ("optimizing", 0.90, "Layer 4 ACT: Ranking intervention options..."),
        ("complete", 1.0, "Analysis complete — all 4 layers integrated."),
    ]

    async def gen():
        for stage, progress, message in stages:
            yield f"data: {json.dumps({'stage': stage, 'progress': progress, 'message': message, 'session_id': session_id})}\n\n"
            if stage != "complete":
                await asyncio.sleep(1.5)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"})


@app.get("/api/v1/diagnostics/recent-sessions")
async def recent_sessions(limit: int = 5):
    all_sessions = sorted(SESSIONS.values(), key=lambda s: s.get("created_at", 0), reverse=True)
    result = []
    for s in all_sessions[:limit]:
        r = s.get("result", {})
        pid = s.get("patient_id", "")
        patient = PATIENTS.get(pid, {})
        result.append({
            "session_id": r.get("session_id", ""),
            "patient_id": pid,
            "patient_name": patient.get("demographics", {}).get("name"),
            "primary_diagnosis": r.get("primary_diagnosis"),
            "confidence_score": r.get("confidence_score"),
            "created_at": datetime.fromtimestamp(s.get("created_at", time.time()), tz=timezone.utc).isoformat(),
        })
    return result


@app.get("/api/v1/diagnostics/pending-review")
async def pending_reviews():
    reviews = []
    for s in SESSIONS.values():
        r = s.get("result", {})
        conf = r.get("confidence_score", 0) or 0
        if conf >= 0.70:
            pid = s.get("patient_id", "")
            patient = PATIENTS.get(pid, {})
            reviews.append({
                "session_id": r.get("session_id", ""),
                "patient_id": pid,
                "patient_name": patient.get("demographics", {}).get("name", "Unknown"),
                "primary_diagnosis": r.get("primary_diagnosis", ""),
                "confidence_score": conf,
                "created_at": datetime.fromtimestamp(s.get("created_at", time.time()), tz=timezone.utc).isoformat(),
            })
    return reviews


@app.post("/api/v1/diagnostics/review/{session_id}")
async def submit_review(session_id: str, body: dict):
    if session_id in SESSIONS:
        SESSIONS[session_id]["review_status"] = "approved" if body.get("approved") else "overridden"
    return {"status": "approved" if body.get("approved") else "overridden", "session_id": session_id}


# ============================================================
# ABDM
# ============================================================

@app.post("/api/v1/abdm/verify/{abha_id}")
async def verify_abha(abha_id: str):
    return {"verified": True, "name": "Rajesh Kumar", "age": 42, "gender": "M", "abha_address": f"{abha_id}@abdm"}


@app.post("/api/v1/abdm/fetch-history")
async def fetch_history(data: dict):
    return {"records": [
        {"type": "lab", "date": "2026-04-10", "parameter": "Hemoglobin", "value": 9.1, "unit": "g/dL", "codes": ["D50.9"]},
        {"type": "diagnosis", "date": "2026-02-15", "findings": "Suspected pulmonary TB, sputum pending", "codes": ["A15.0"]},
    ]}


@app.post("/api/v1/abdm/push-report")
async def push_report(data: dict):
    return {"status": "success", "fhir_id": f"fhir-{uuid4().hex[:8]}"}


# ============================================================
# Federated Learning
# ============================================================

@app.get("/api/v1/federated/status")
async def fl_status():
    return {
        "server_status": "running",
        "current_round": 47,
        "total_nodes": 8,
        "active_nodes": random.randint(5, 8),
        "global_model_version": "prism-causal-v1.0.47",
        "cumulative_dp_epsilon": 3.72,
        "last_round_metrics": {"accuracy": 0.891, "auc_roc": 0.934, "loss": 0.187},
    }


@app.get("/api/v1/federated/rounds")
async def fl_rounds(limit: int = 20):
    rounds = []
    for i in range(47, max(0, 47 - limit), -1):
        t = datetime.now(timezone.utc) - timedelta(minutes=(47 - i) * 10)
        rounds.append({
            "round_number": i,
            "participating_nodes": random.randint(4, 8),
            "rejected_nodes": random.randint(0, 2),
            "metrics": {"accuracy": round(0.847 + i * 0.001, 3), "loss": round(0.231 - i * 0.002, 4)},
            "dp_epsilon_spent": round(0.25 + random.uniform(-0.02, 0.02), 3),
            "completed_at": t.isoformat() + "Z",
        })
    return rounds


@app.get("/api/v1/federated/nodes")
async def fl_nodes():
    hospitals = ["KMC Mangalore", "Wenlock Hospital", "Father Muller Medical", "AJ Hospital", "Kasturba Hospital"]
    return [
        {
            "node_id": f"node-{i+1:03d}",
            "hospital_name": hospitals[i % len(hospitals)],
            "status": random.choice(["active", "active", "active", "idle", "offline"]),
            "rounds_participated": random.randint(20, 47),
            "data_samples_contributed": random.randint(150, 800),
            "dp_epsilon_spent": round(random.uniform(0.5, 3.5), 2),
            "last_seen": (datetime.now(timezone.utc) - timedelta(minutes=random.randint(0, 60))).isoformat() + "Z",
        }
        for i in range(6)
    ]


@app.get("/api/v1/federated/model-versions")
async def model_versions():
    return [
        {
            "version": f"prism-causal-v1.0.{r}",
            "accuracy": round(0.847 + r * 0.001, 3),
            "loss": round(0.231 - r * 0.002, 4),
            "trained_at": (datetime.now(timezone.utc) - timedelta(hours=(47 - r) * 2)).isoformat() + "Z",
            "participating_nodes": random.randint(4, 8),
        }
        for r in [47, 40, 35, 28, 20, 14, 7, 1]
    ]


@app.post("/api/v1/federated/trigger-round")
async def trigger_round(body: dict):
    return {"round_number": 48, "status": "started"}


# ============================================================
# Audit Log
# ============================================================

@app.get("/api/v1/audit/log")
async def audit_log(page: int = 1, limit: int = 20):
    actions = ["create", "read", "update", "export"]
    resources = ["patient", "diagnostic_session", "health_record"]
    entries = [
        {
            "id": str(uuid4()),
            "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=i * 7)).isoformat() + "Z",
            "user_id": f"user-{random.randint(1, 3):03d}",
            "user_name": random.choice(["Dr. Sharma", "Dr. Patel", "ASHA Worker"]),
            "action": random.choice(actions),
            "resource_type": random.choice(resources),
            "resource_id": str(uuid4())[:8],
        }
        for i in range((page - 1) * limit, page * limit)
    ]
    return {"entries": entries, "total": 200, "page": page, "per_page": limit}


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  PRISM Platform — Dev Server")
    print("  Frontend: http://localhost:3000")
    print("  API Docs: http://localhost:8000/docs")
    print("  No ML models / Supabase / Redis needed")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
