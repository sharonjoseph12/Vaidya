"""
PRISM API — Standalone Development Server
No Supabase, Redis, or Celery required. All data in-memory with demo fixtures.
Integrates Layer 1 (SENSE), Layer 2 (REASON), Layer 3 (PROJECT), Layer 4 (ACT).
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
from uuid import uuid4
import asyncio
import json
import time
import logging
import random
import tempfile
import os
from datetime import datetime, timedelta, timezone

from prism.layer2_reason.causal_engine import full_causal_report
from layer1_sense.sense_pipeline import PRISMSensePipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prism-standalone")

# Initialize real ML Pipeline
try:
    sense_pipeline = PRISMSensePipeline()
    logger.info("PRISMSensePipeline initialized.")
except Exception as e:
    logger.error(f"Failed to initialize PRISMSensePipeline: {e}")
    sense_pipeline = None

app = FastAPI(
    title="PRISM API (Standalone)",
    description="All 4 layers integrated — no external services needed.",
    version="1.0.0-standalone",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# In-Memory Data Store
# ============================================================

PATIENTS: Dict[str, dict] = {
    "demo-patient-001": {
        "id": "demo-patient-001",
        "abha_id": "91-1234-5678-9012",
        "created_at": "2026-05-14T10:00:00Z",
        "consent_given": True,
        "demographics": {
            "name": "Rajesh Kumar",
            "age": 42,
            "sex": "M",
            "location": "Mangalore, Karnataka",
            "socioeconomic_tier": "BPL",
        },
        "sessions_count": 3,
        "last_session_date": "2026-05-14T10:30:00Z",
    },
    "demo-patient-002": {
        "id": "demo-patient-002",
        "abha_id": "91-9876-5432-1098",
        "created_at": "2026-05-13T08:15:00Z",
        "consent_given": True,
        "demographics": {
            "name": "Priya Sharma",
            "age": 28,
            "sex": "F",
            "location": "Dharwad, Karnataka",
            "socioeconomic_tier": "APL",
        },
        "sessions_count": 1,
        "last_session_date": "2026-05-13T09:00:00Z",
    },
    "demo-patient-003": {
        "id": "demo-patient-003",
        "abha_id": "91-5555-6666-7777",
        "created_at": "2026-05-12T14:30:00Z",
        "consent_given": True,
        "demographics": {
            "name": "Mohammed Ali",
            "age": 55,
            "sex": "M",
            "location": "Udupi, Karnataka",
            "socioeconomic_tier": "BPL",
        },
        "sessions_count": 2,
        "last_session_date": "2026-05-12T15:45:00Z",
    },
}

SESSIONS: Dict[str, dict] = {}

# ============================================================
# Full 4-Layer Demo Result (matches frontend DiagnosticResult type exactly)
# ============================================================

def build_dynamic_result(session_id: str, patient_features: dict, sense_result, has_audio: bool, has_video: bool) -> dict:
    """Build a complete 4-layer diagnostic result using the real Causal Engine and Sense Pipeline."""
    
    # 1. Map SENSE ML Results
    if sense_result:
        disease_probs = sense_result.disease_probabilities
        # Map some physical/audio indicators to features for causal engine
        patient_features['cough_detected'] = int(sense_result.audio.cough_detected)
        patient_features['hr'] = sense_result.rppg.hr
        patient_features['spo2'] = sense_result.rppg.spo2
        
        # Check for data quality warnings to flag bad inputs
        is_bad_quality = False
        visual_warnings = getattr(sense_result.visual, 'uncertainty_flags', [])
        if "low_light_detected" in visual_warnings or getattr(sense_result.audio, 'noise_level_high', False):
            is_bad_quality = True
            
        sense_payload = sense_result.to_dict()
        processing_time = sense_result.processing_time_ms
    else:
        # Fallback if pipeline fails
        disease_probs = {"TB": 0.5, "Anemia": 0.5, "Pneumonia": 0.2, "Dengue": 0.1}
        is_bad_quality = False
        sense_payload = {}
        processing_time = 0

    # Layer 2: REASON (Real DoWhy Causal Engine)
    causal_out = full_causal_report(disease_probs, patient_features)
    
    # Layer 3 & 4 (Simulated based on real causal output)
    top_disease = causal_out.get('disease', 'TB')
    top_prob = causal_out.get('probability', 0.5)
    
    twin_traj = [
        {"month": i, "values": {f"{top_disease.lower()}_prob": min(0.99, top_prob + (i*0.02))}}
        for i in [0, 1, 2, 3, 4, 5, 6, 9, 12]
    ]
    
    best_iv = causal_out.get('best_intervention')
    if best_iv:
        iv_traj = [
            {"month": i, "values": {f"{top_disease.lower()}_prob": max(0.01, top_prob - (i*0.05))}}
            for i in [0, 1, 2, 3, 4, 5, 6, 9, 12]
        ]
    else:
        iv_traj = twin_traj

    # Format recommendations for frontend
    frontend_recs = []
    for idx, iv in enumerate(causal_out.get('interventions', [])):
        frontend_recs.append({
            "rank": idx + 1,
            "intervention": iv['treatment'].replace("_", " ").title(),
            "description": f"Targeting {iv['treatment'].replace('_', ' ')} to reduce probability to {iv['intervened_prob']:.0%}.",
            "rationale": f"Expected reduction of {iv['reduction_pct']}% in {top_disease} risk.",
            "cost_govt": 0,
            "cost_private": random.randint(100, 1000),
            "qaly_gain": round(random.uniform(1.0, 3.0), 1),
            "scheme": "Govt Health Scheme" if idx == 0 else "Out of pocket"
        })

    return {
        "session_id": session_id,
        "status": "complete",
        "primary_diagnosis": top_disease,
        "confidence_score": top_prob,
        "disease_probabilities": disease_probs,
        "offline_mode": False,
        "model_version": "prism-v2.0.0-full-ml",
        "processing_time_ms": processing_time,
        "data_quality_rejected": is_bad_quality, # Flag for FL Orchestrator

        "sense_results": sense_payload,

        "causal_results": {
            "attributions": causal_out.get('attributions', {}),
            "top_intervention": best_iv['treatment'] if best_iv else None,
            "intervention_effects": {iv['treatment']: iv['reduction_pct']/100 for iv in causal_out.get('interventions', [])},
            "patient_risk_factors": patient_features,
            "counterfactuals": [{
                "changes": {best_iv['treatment']: [patient_features.get(best_iv['treatment'], 0), 0]},
                "new_probability": best_iv['intervened_prob'],
                "feasibility_score": 0.85,
                "n_features_changed": 1
            }] if best_iv else [],
            "narrative": causal_out.get('narrative', ''),
            "causal_graph_dot": causal_out.get('causal_graph_dot', '')
        },

        "twin_trajectory": {
            "without_intervention": twin_traj,
            "with_best_intervention": iv_traj,
            "confidence_bands": {f"{top_disease.lower()}_prob": [0.05, 0.12]},
            "months_to_critical": 5.0,
            "months_to_critical_with_intervention": 999,
            "intervention_applied": best_iv['treatment'] if best_iv else "None",
        },

        "intervention_plan": {
            "recommendations": frontend_recs or [
                {
                    "rank": 1,
                    "intervention": "General Consultation",
                    "description": "Consult doctor.",
                    "rationale": "No specific causal interventions identified.",
                    "cost_govt": 0, "cost_private": 500, "qaly_gain": 0.5
                }
            ],
            "active_uncertainty_reduction": {
                "recommended_test": "Lab Test Panel",
                "cost": 0,
                "expected_uncertainty_reduction": 0.3,
                "rationale": "To reduce diagnostic uncertainty."
            }
        },
        "uncertainty_bounds": {d: [max(0, p-0.1), min(1, p+0.1)] for d, p in disease_probs.items()}
    }


# ============================================================
# Health Check
# ============================================================

@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "version": "1.0.0-standalone", "service": "prism-api", "layers": ["SENSE", "REASON", "PROJECT", "ACT"]}


# ============================================================
# Patient Endpoints
# ============================================================

@app.get("/api/v1/patients", tags=["patients"])
async def list_patients(page: int = 1, per_page: int = 20):
    all_patients = list(PATIENTS.values())
    return {
        "patients": all_patients,
        "total": len(all_patients),
        "page": page,
        "per_page": per_page,
    }


@app.get("/api/v1/patients/{patient_id}", tags=["patients"])
async def get_patient(patient_id: str):
    if patient_id in PATIENTS:
        return PATIENTS[patient_id]
    raise HTTPException(404, "Patient not found")


class PatientCreateRequest(BaseModel):
    abha_id: Optional[str] = None
    demographics: dict
    consent_given: bool = True
    consent_purpose: Optional[str] = None
    device_info: Optional[dict] = None


@app.post("/api/v1/patients", tags=["patients"], status_code=201)
async def create_patient(patient: PatientCreateRequest):
    pid = f"patient-{uuid4().hex[:8]}"
    record = {
        "id": pid,
        "abha_id": patient.abha_id,
        "created_at": "2026-05-14T12:00:00Z",
        "consent_given": patient.consent_given,
        "demographics": patient.demographics,
        "sessions_count": 0,
        "last_session_date": None,
    }
    PATIENTS[pid] = record
    return record


# ============================================================
# Diagnostics Endpoints
# ============================================================

@app.post("/api/v1/diagnostics/analyze", tags=["diagnostics"], status_code=202)
async def run_analysis(
    patient_id: str = Form(default="demo-patient-001"),
    session_type: str = Form(default="full"),
    patient_features: str = Form(default="{}"),
    audio_file: UploadFile = File(default=None),
    video_file: UploadFile = File(default=None),
):
    session_id = str(uuid4())
    
    # Parse features from frontend (or default to random if empty)
    try:
        features = json.loads(patient_features)
    except:
        features = {}
        
    if not features:
        # Generate completely random live features for real-time demonstration
        features = {
            "malnutrition": round(random.uniform(0.1, 0.9), 2), 
            "crowding_index": random.randint(1, 8), 
            "bmi": round(random.uniform(14.0, 30.0), 1), 
            "nutrition_score": random.randint(1, 10), 
            "smoking": random.choice([0, 1])
        }
        
    has_audio = audio_file is not None and audio_file.size > 0
    has_video = video_file is not None and video_file.size > 0
    
    # 1. Save uploaded files to temp paths for OpenCV / Librosa processing
    video_path = None
    audio_path = None
    
    if has_video:
        _, video_path = tempfile.mkstemp(suffix=".webm")
        with open(video_path, "wb") as f:
            f.write(await video_file.read())
            
    if has_audio:
        _, audio_path = tempfile.mkstemp(suffix=".webm")
        with open(audio_path, "wb") as f:
            f.write(await audio_file.read())
            
    # 2. Run Actual ML Models via PRISMSensePipeline
    sense_result = None
    if sense_pipeline and (video_path or audio_path):
        sense_result = sense_pipeline.run(video_path=video_path, audio_path=audio_path)
        
    # Cleanup temp files
    if video_path and os.path.exists(video_path):
        os.remove(video_path)
    if audio_path and os.path.exists(audio_path):
        os.remove(audio_path)
    
    SESSIONS[session_id] = {
        "status": "queued",
        "patient_id": patient_id,
        "created_at": time.time(),
        "result": build_dynamic_result(session_id, features, sense_result, has_audio, has_video)
    }
    
    # Update patient last scan date
    if patient_id in PATIENTS:
        PATIENTS[patient_id]['last_session_date'] = datetime.now(timezone.utc).isoformat() + "Z"
        PATIENTS[patient_id]['sessions_count'] += 1

    logger.info("Analysis started: session=%s patient=%s audio=%s video=%s", session_id, patient_id, has_audio, has_video)
    return {
        "session_id": session_id,
        "task_id": f"task-{uuid4().hex[:8]}",
        "status": "queued",
        "estimated_time_seconds": 8,
    }


@app.get("/api/v1/diagnostics/results/{session_id}", tags=["diagnostics"])
async def get_results(session_id: str):
    if session_id in SESSIONS and "result" in SESSIONS[session_id]:
        return SESSIONS[session_id]["result"]
    
    # Fallback to demo result for standard URL testing
    return build_dynamic_result(session_id, {"malnutrition": 0.8, "crowding_index": 5, "bmi": 17.5}, None, False, False)


@app.get("/api/v1/diagnostics/stream/{session_id}", tags=["diagnostics"])
async def stream_results(session_id: str):
    """SSE stream simulating pipeline progress through all 4 layers."""
    stages = [
        ("sensing", 0.25, "Layer 1 SENSE: Extracting rPPG, audio biomarkers, visual cues..."),
        ("reasoning", 0.50, "Layer 2 REASON: Building causal attribution graph..."),
        ("projecting", 0.75, "Layer 3 PROJECT: Simulating digital twin trajectory..."),
        ("optimizing", 0.90, "Layer 4 ACT: Ranking intervention options..."),
        ("complete", 1.0, "Analysis complete — all 4 layers integrated."),
    ]

    async def event_generator():
        for stage, progress, message in stages:
            event = json.dumps({
                "stage": stage,
                "progress": progress,
                "message": message,
                "session_id": session_id,
            })
            yield f"data: {event}\n\n"
            if stage != "complete":
                await asyncio.sleep(1.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


# ============================================================
# ABDM Endpoints
# ============================================================

@app.post("/api/v1/abdm/verify/{abha_id}", tags=["abdm"])
async def verify_abha(abha_id: str):
    return {
        "verified": True,
        "name": "Rajesh Kumar",
        "age": 42,
        "gender": "M",
        "abha_address": f"{abha_id}@abdm",
    }


@app.post("/api/v1/abdm/fetch-history", tags=["abdm"])
async def fetch_history(data: dict):
    return {
        "records": [
            {"type": "lab", "date": "2026-04-10", "parameter": "Hemoglobin", "value": 9.1, "unit": "g/dL", "codes": ["D50.9"]},
            {"type": "lab", "date": "2026-03-22", "parameter": "WBC Count", "value": 11200, "unit": "/μL", "codes": []},
            {"type": "diagnosis", "date": "2026-02-15", "findings": "Suspected pulmonary TB, sputum pending", "codes": ["A15.0"]},
        ]
    }


@app.post("/api/v1/abdm/push-report", tags=["abdm"])
async def push_report(data: dict):
    return {"status": "success", "fhir_id": f"fhir-{uuid4().hex[:8]}"}


# ============================================================
# Federated Learning Endpoints
# ============================================================

@app.get("/api/v1/federated/status", tags=["federated"])
async def fl_status():
    # Dynamic simulated FL status
    elapsed_minutes = (datetime.now(timezone.utc) - datetime(2026, 5, 14, 0, 0, 0, tzinfo=timezone.utc)).total_seconds() / 60
    current_round = int(elapsed_minutes / 10) + 14 # roughly 1 round per 10 mins
    
    return {
        "server_status": "running",
        "current_round": current_round,
        "total_nodes": 8,
        "active_nodes": random.randint(5, 8),
        "global_model_version": f"prism-causal-v1.0.{current_round}",
        "cumulative_dp_epsilon": 3.72 + (current_round * 0.01),
        "last_round_metrics": {
            "accuracy": min(0.98, 0.847 + (current_round * 0.001)),
            "auc_roc": min(0.99, 0.912 + (current_round * 0.001)),
            "loss": max(0.05, 0.231 - (current_round * 0.002)),
            "participants": random.randint(4, 7),
        },
    }


@app.get("/api/v1/federated/rounds", tags=["federated"])
async def fl_rounds(limit: int = 20):
    elapsed_minutes = (datetime.now(timezone.utc) - datetime(2026, 5, 14, 0, 0, 0, tzinfo=timezone.utc)).total_seconds() / 60
    current_round = int(elapsed_minutes / 10) + 14
    
    # Calculate how many sessions were rejected due to bad data quality
    bad_sessions_count = sum(1 for s in SESSIONS.values() if s.get('result', {}).get('data_quality_rejected', False))
    
    rounds = []
    base_acc = 0.847
    base_loss = 0.231
    for i in range(current_round, max(0, current_round - limit), -1):
        round_time = datetime.now(timezone.utc) - timedelta(minutes=(current_round - i) * 10)
        acc = min(0.98, base_acc - ((current_round - i) * 0.001) + random.uniform(-0.005, 0.005))
        loss = max(0.05, base_loss + ((current_round - i) * 0.002) + random.uniform(-0.005, 0.005))
        
        # Inject our actual rejected sessions into the latest round
        rejected = bad_sessions_count if i == current_round else random.randint(0, 2)
        
        rounds.append({
            "round_number": i,
            "participating_nodes": random.randint(4, 8),
            "rejected_nodes": rejected,
            "metrics": {"accuracy": acc, "loss": loss},
            "dp_epsilon_spent": 0.25 + random.uniform(-0.02, 0.02),
            "completed_at": round_time.isoformat() + "Z",
        })
    return rounds


# ============================================================
# Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print("  PRISM Platform - Standalone Integrated Server")
    print("  Layers: SENSE -> REASON -> PROJECT -> ACT")
    print("  API Docs: http://localhost:8000/docs")
    print("=" * 60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
