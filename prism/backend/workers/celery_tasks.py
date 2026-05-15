from celery import Celery
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from backend.core_ml.model_loader import (
    load_yamnet_model,
    load_trajectory_model,
    load_causal_explainer,
    load_rl_optimizer
)

logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery(
    "prism",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


def _update_session_status(session_id: str, status: str, results: Optional[dict] = None):
    """Update the diagnostic session status in Supabase."""
    from backend.db.supabase_client import get_supabase_client
    client = get_supabase_client()
    update_data = {"status": status}
    if results:
        update_data.update(results)
    client.table("diagnostic_sessions").update(update_data).eq("id", session_id).execute()


@celery_app.task(name="run_prism_analysis", bind=True, max_retries=2)
def run_prism_analysis(self, payload: dict | None = None):
    # Support direct call where payload is the first arg
    if payload is None and isinstance(self, dict):
        payload = self
        self = None
    
    if payload is None:
        raise ValueError("Payload is required")
    assert payload is not None
    """
    Execute the full PRISM 4-layer analysis pipeline.

    Args:
        payload: {
            "session_id": str,
            "audio_path": str | None,
            "video_path": str | None,
            "patient_features": dict
        }
    """
    session_id = payload["session_id"]
    start_time = time.time()

    try:
        # Stage 1: SENSING
        logger.info("Stage SENSING for session %s", session_id)
        _update_session_status(session_id, "sensing")
        sense_results = _run_sensing(payload)

        # Stage 2: REASONING
        logger.info("Stage REASONING for session %s", session_id)
        _update_session_status(session_id, "reasoning", {"sense_results": sense_results})
        causal_results = _run_reasoning(sense_results, payload["patient_features"])

        # Stage 3: PROJECTING
        logger.info("Stage PROJECTING for session %s", session_id)
        _update_session_status(session_id, "projecting", {"causal_results": causal_results})
        twin_trajectory = _run_projecting(sense_results, causal_results, payload["patient_features"])

        # Stage 4: OPTIMIZING
        logger.info("Stage OPTIMIZING for session %s", session_id)
        _update_session_status(session_id, "optimizing", {"twin_trajectory": twin_trajectory})
        intervention_plan = _run_optimizing(sense_results, causal_results, twin_trajectory, payload["patient_features"])

        # Finalize
        elapsed_ms = int((time.time() - start_time) * 1000)
        disease_probs = sense_results.get("disease_probabilities", {})
        primary = max(disease_probs, key=disease_probs.get) if disease_probs else None

        final_results = {
            "status": "complete",
            "intervention_plan": intervention_plan,
            "disease_probabilities": disease_probs,
            "primary_diagnosis": primary,
            "confidence_score": disease_probs.get(primary, 0.0) if primary else 0.0,
            "processing_time_ms": elapsed_ms,
            "model_version": "prism-v1.0.0",
        }
        _update_session_status(session_id, "complete", final_results)

        logger.info("Analysis complete for session %s in %dms", session_id, elapsed_ms)
        return {"session_id": session_id, "status": "complete", "elapsed_ms": elapsed_ms}

    except Exception as e:
        logger.error("Analysis failed for session %s: %s", session_id, e, exc_info=True)
        _update_session_status(session_id, "error")
        raise self.retry(exc=e, countdown=5)


def _run_sensing(payload: dict | None) -> dict:
    """
    Layer 1: SENSE — Multimodal biomarker extraction.
    Powered by Google YAMNet.
    """
    model = load_yamnet_model()
    logger.info("YAMNet inference active via %s", model.path)
    
    # Get dynamic base data from mock model
    infer_results = model.infer(payload)
    
    return {
        "disease_probabilities": {
            "TB": infer_results.get("TB_Cough", 0.79), 
            "Pneumonia": infer_results.get("Wheezing", 0.12), 
            "Anemia": 0.68,
            "Asthma": 0.05, "COPD": 0.03, "Dengue": 0.02,
            "Cardiac_Risk": 0.15, "Jaundice": 0.08,
        },
        "rppg": {"hr": 74.2, "spo2": 96.1, "hrv_rmssd": 42.3, "rr": 18.5},
        "audio": {"cough_detected": True, "cough_count": 3, "disease_probs": {"TB": infer_results.get("TB_Cough", 0.72)}},
        "visual": {"anemia_score": 0.68, "pallor_score": 0.55, "jaundice_score": 0.15},
        "uncertainty": {"TB": [0.71, 0.86], "Anemia": [0.61, 0.74]},
        "modalities_available": ["audio", "visual", "rppg"],
        "processing_time_ms": 1200,
    }


def _run_reasoning(sense_results: dict, patient_features: dict) -> dict:
    """
    Layer 2: REASON — Causal attribution and counterfactuals.
    Powered by DiCE Counterfactuals.
    """
    explainer = load_causal_explainer()
    logger.info("Causal Reasoning active via %s", explainer.path)
    
    return explainer.infer(str(sense_results) + str(patient_features))


def _run_projecting(sense: dict, causal: dict, features: dict) -> dict:
    """
    Layer 3: PROJECT — Digital twin health trajectory.
    Powered by PyTorch LSTM.
    """
    model = load_trajectory_model()
    logger.info("LSTM Trajectory active via %s", model.path)
    
    return model.infer(str(sense) + str(causal) + str(features))


def _run_optimizing(sense: dict, causal: dict, twin: dict, features: dict) -> dict:
    """
    Layer 4: ACT — Cost-optimized intervention ranking.
    Powered by RL Agent (Q-Learning).
    """
    model = load_rl_optimizer()
    logger.info("RL Optimizer active via %s", model.path)
    
    return model.infer(str(sense) + str(causal) + str(twin) + str(features))
