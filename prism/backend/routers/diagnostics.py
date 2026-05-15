"""
PRISM Platform — Diagnostics Endpoints
Handles scan analysis submission, results retrieval, and SSE streaming.
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from uuid import uuid4
import asyncio
import json
import logging

from backend.utils.auth import get_current_user
from backend.db.supabase_client import get_supabase_client, log_audit
from backend.models.diagnostic_result import (
    AnalysisStartResponse,
    FullDiagnosticResult,
    AnalysisProgressEvent,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisStartResponse, status_code=202)
async def run_full_analysis(
    patient_id: str = Form(...),
    session_type: str = Form(default="full"),
    patient_features: str = Form(default="{}"),
    audio_file: UploadFile = File(default=None),
    video_file: UploadFile = File(default=None),
    current_user: dict = Depends(get_current_user),
):
    """
    Start a full PRISM analysis pipeline.
    Accepts multipart form data with optional audio and video files.
    Returns immediately with a session ID for polling/streaming results.
    """
    client = get_supabase_client()

    # Validate patient exists
    patient = client.table("patients").select("id").eq("id", patient_id).execute()
    if not patient.data:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Parse patient features JSON
    try:
        features = json.loads(patient_features)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid patient_features JSON")

    # Create diagnostic session
    session_id = str(uuid4())
    session_data = {
        "id": session_id,
        "patient_id": patient_id,
        "session_type": session_type,
        "status": "queued",
    }
    client.table("diagnostic_sessions").insert(session_data).execute()

    # Save uploaded files to Supabase Storage (if provided)
    audio_path = None
    video_path = None

    if audio_file and audio_file.filename:
        audio_bytes = await audio_file.read()
        storage_path = f"scans/{session_id}/audio_{audio_file.filename}"
        try:
            client.storage.from_("scan-media").upload(storage_path, audio_bytes)
            audio_path = storage_path
        except Exception as e:
            logger.warning("Failed to upload audio to storage: %s", e)

    if video_file and video_file.filename:
        video_bytes = await video_file.read()
        storage_path = f"scans/{session_id}/video_{video_file.filename}"
        try:
            client.storage.from_("scan-media").upload(storage_path, video_bytes)
            video_path = storage_path
        except Exception as e:
            logger.warning("Failed to upload video to storage: %s", e)

    # Run task directly for demo/dev (bypass Celery)
    from backend.workers.celery_tasks import run_prism_analysis as run_task
    # Use a thread or background task if we want it to be async, but for demo sync is fine
    # or use asyncio.create_task if it's an async function (but it's a celery task which is sync)
    class MockTask:
        def __init__(self): self.id = str(uuid4())
    task = MockTask()
    
    # Run in background so we can return the session ID immediately
    import threading
    thread = threading.Thread(target=run_task, args=( {
        "session_id": session_id,
        "audio_path": audio_path,
        "video_path": video_path,
        "patient_features": features,
    },))
    thread.start()

    # Audit log
    await log_audit(
        user_id=current_user["user_id"],
        action="create",
        resource_type="diagnostic_session",
        resource_id=session_id,
    )

    return AnalysisStartResponse(
        session_id=session_id,
        task_id=task.id,
        status="queued",
        estimated_time_seconds=10,
    )


@router.get("/results/{session_id}")
async def get_results(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get analysis results for a completed session."""
    client = get_supabase_client()

    result = client.table("diagnostic_sessions").select("*").eq("id", session_id).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = result.data[0]

    # If still processing, return 202 with current status
    if session["status"] not in ("complete", "error"):
        return {
            "session_id": session_id,
            "status": session["status"],
            "message": f"Analysis in progress: {session['status']}",
        }

    return FullDiagnosticResult(
        session_id=session["id"],
        status=session["status"],
        primary_diagnosis=session.get("primary_diagnosis"),
        confidence_score=session.get("confidence_score"),
        disease_probabilities=session.get("disease_probabilities", {}),
        sense_results=session.get("sense_results"),
        causal_results=session.get("causal_results"),
        twin_trajectory=session.get("twin_trajectory"),
        intervention_plan=session.get("intervention_plan"),
        uncertainty_bounds=session.get("uncertainty_bounds", {}),
        processing_time_ms=session.get("processing_time_ms", 0),
        model_version=session.get("model_version"),
    )


@router.get("/stream/{session_id}")
async def stream_results(session_id: str):
    """
    Server-Sent Events stream for real-time pipeline progress.
    Client receives events as the pipeline transitions through stages.
    """
    client = get_supabase_client()

    # Verify session exists
    result = client.table("diagnostic_sessions").select("id").eq("id", session_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Session not found")

    stage_progress = {
        "queued": 0.0,
        "sensing": 0.25,
        "reasoning": 0.50,
        "projecting": 0.75,
        "optimizing": 0.90,
        "complete": 1.0,
        "error": 1.0,
    }

    stage_messages = {
        "queued": "Waiting in queue...",
        "sensing": "Analyzing biomarkers from audio, video, and rPPG...",
        "reasoning": "Building causal attribution graph...",
        "projecting": "Simulating health trajectory with digital twin...",
        "optimizing": "Ranking intervention options...",
        "complete": "Analysis complete!",
        "error": "Analysis encountered an error.",
    }

    async def event_generator():
        last_status = None
        max_polls = 120  # 2 minutes max

        for _ in range(max_polls):
            result = client.table("diagnostic_sessions").select("status").eq(
                "id", session_id
            ).execute()

            if not result.data:
                break

            current_status = result.data[0]["status"]

            if current_status != last_status:
                event = AnalysisProgressEvent(
                    stage=current_status,
                    progress=stage_progress.get(current_status, 0.0),
                    message=stage_messages.get(current_status, "Processing..."),
                    session_id=session_id,
                )
                yield f"data: {event.model_dump_json()}\n\n"
                last_status = current_status
            else:
                # Send heartbeat to keep connection alive
                yield ": heartbeat\n\n"

            if current_status in ("complete", "error"):
                await asyncio.sleep(0.5)  # Give browser time to process
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/report/{session_id}/pdf")
async def generate_pdf_report(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Generate and return a clinical PDF report for a completed session."""
    client = get_supabase_client()

    session = client.table("diagnostic_sessions").select("*").eq("id", session_id).execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.data[0]["status"] != "complete":
        raise HTTPException(status_code=400, detail="Analysis not yet complete")

    # Generate PDF using report service
    from backend.services.report_service import generate_pdf_report as gen_pdf
    pdf_bytes = gen_pdf(session.data[0])

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=prism_report_{session_id[:8]}.pdf"},
    )
