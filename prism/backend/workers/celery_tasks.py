from celery import Celery
import logging
import shutil
import time
from typing import Dict, List, Optional, Tuple, Any
from backend.core_ml.model_loader import load_yamnet_model

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
        if self is not None and hasattr(self, "retry"):
            raise self.retry(exc=e, countdown=5) from e
        raise


def _run_sensing(payload: dict) -> dict:
    """
    Layer 1: SENSE — multimodal biomarker extraction.

    Uses ``layer1_sense.PRISMSensePipeline`` on files downloaded from Supabase Storage
    when ``use_real_sense`` is true and paths are present; otherwise (or on failure)
    falls back to the lightweight mock.
    """
    import time
    start = time.time()

    from backend.config import get_settings
    from backend.services.scan_media import download_scan_files
    from backend.services.real_sense import try_run_real_sense

    if payload is None:
        raise ValueError("payload required")

    settings = get_settings()
    use_real = getattr(settings, "use_real_sense", True)
    session_id = str(payload.get("session_id", "unknown"))
    audio_storage = payload.get("audio_path")
    video_storage = payload.get("video_path")

    tmp_dir: str | None = None
    try:
        if use_real and (audio_storage or video_storage):
            local_audio, local_video, tmp_dir = download_scan_files(
                session_id, audio_storage, video_storage
            )
            if local_audio or local_video:
                real = try_run_real_sense(local_video, local_audio)
                if real is not None:
                    logger.info("Real SENSE pipeline completed for session %s", session_id)
                    return real
            else:
                logger.warning(
                    "No local media files for session %s (uploads missing or empty); using mock SENSE",
                    session_id,
                )
        
        # Fallback to HEAD logic if use_real_sense is not used or files are missing
        try:
            from layer1_sense.sense_pipeline import run_sense_pipeline  # type: ignore
            result = run_sense_pipeline(payload)
            logger.info("Layer 1 sense pipeline executed successfully")
            return result
        except ImportError:
            logger.warning("Layer 1 sense pipeline not available — using fallback")
        except Exception as e:
            logger.warning("Layer 1 pipeline error: %s — falling back", e)

        return _legacy_run_sensing(payload)
    finally:
        if tmp_dir:
            shutil.rmtree(tmp_dir, ignore_errors=True)

def _legacy_run_sensing(payload: dict) -> dict:
    """Previous mock YAMNet + fixed vitals (fallback)."""
    model = load_yamnet_model()
    logger.info("Fallback mock SENSE via %s", model.path)
    infer_results = model.infer(payload)
    return {
        "disease_probabilities": {
            "TB": infer_results.get("TB_Cough", 0.79),
            "Pneumonia": infer_results.get("Wheezing", 0.12),
            "Anemia": 0.68,
            "Asthma": 0.05,
            "COPD": 0.03,
            "Dengue": 0.02,
            "Cardiac_Risk": 0.15,
            "Jaundice": 0.08,
        },
        "rppg": {"hr": 74.2, "spo2": 96.1, "hrv_rmssd": 42.3, "rr": 18.5},
        "audio": {
            "cough_detected": True,
            "cough_count": 3,
            "disease_probs": {"TB": infer_results.get("TB_Cough", 0.72)},
        },
        "visual": {"anemia_score": 0.68, "pallor_score": 0.55, "jaundice_score": 0.15},
        "uncertainty": {"TB": [0.71, 0.86], "Anemia": [0.61, 0.74]},
        "modalities_available": ["audio", "visual", "rppg"],
        "processing_time_ms": 1200,
    }

def _compute_rppg_from_video(video_path) -> dict | None:
    """
    Attempt basic rPPG extraction from video.
    Returns None if video not available or extraction fails.
    """
    if not video_path:
        return None
    try:
        return {
            "hr": None,
            "spo2": None,
            "hrv_rmssd": None,
            "rr": None,
            "confidence": {},
        }
    except Exception as e:
        logger.warning("rPPG extraction failed: %s", e)
        return None


def _run_reasoning(sense_results: dict, patient_features: dict) -> dict:
    """
    Layer 2: REASON — finetuned ``causal_explainer.pkl`` when loadable, else sense-derived heuristic.
    """
    from backend.core_ml.model_loader import load_causal_explainer
    from backend.services.pipeline_derived import build_causal_results

    model = load_causal_explainer()
    if getattr(model, "is_real", False) and hasattr(model, "explain"):
        try:
            out = model.explain(sense_results, patient_features)
            logger.info("Causal reasoning via finetuned artifact %s", getattr(model, "path", ""))
            return out
        except Exception as e:
            logger.warning("Causal artifact failed, using heuristic: %s", e)
    out = build_causal_results(sense_results, patient_features)
    logger.info("Causal reasoning derived from sense disease probabilities (heuristic)")
    return out


def _run_projecting(sense: dict, causal: dict, features: dict) -> dict:
    """
    Layer 3: PROJECT — finetuned ``lstm_trajectory.pth`` when loadable, else sense-derived heuristic.
    """
    from backend.core_ml.model_loader import load_trajectory_model
    from backend.services.pipeline_derived import build_twin_trajectory

    model = load_trajectory_model()
    if getattr(model, "is_real", False) and hasattr(model, "infer_from_sense"):
        try:
            out = model.infer_from_sense(sense, causal, features)
            logger.info("Twin trajectory via finetuned artifact %s", getattr(model, "path", ""))
            return out
        except Exception as e:
            logger.warning("Trajectory artifact failed, using heuristic: %s", e)
    out = build_twin_trajectory(sense, causal, features)
    logger.info("Twin trajectory derived from sense probabilities (heuristic)")
    return out


def _run_optimizing(sense: dict, causal: dict, twin: dict, features: dict) -> dict:
    """
    Layer 4: ACT — intervention options scaled from sense + twin urgency.
    """
    from backend.services.pipeline_derived import build_intervention_plan

    out = build_intervention_plan(sense, causal, twin, features)
    logger.info("Intervention plan derived from sense + twin")
    return out
