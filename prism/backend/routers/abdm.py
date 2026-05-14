"""
PRISM Platform — ABDM/ABHA Integration Endpoints
Handles ABHA verification, health record fetch/push via ABDM gateway.
"""

from fastapi import APIRouter, Depends, HTTPException
import logging

from backend.utils.auth import get_current_user
from backend.models.abdm import (
    ABHAProfile,
    ABDMFetchRequest,
    ABDMFetchResponse,
    ABDMPushRequest,
    ABDMPushResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/verify/{abha_id}", response_model=ABHAProfile)
async def verify_abha_patient(
    abha_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Verify an ABHA ID and retrieve basic profile from ABDM gateway."""
    from backend.services.abdm_service import ABDMService
    abdm = ABDMService()

    try:
        profile = await abdm.verify_abha(abha_id)
        return profile
    except Exception as e:
        logger.error("ABDM verification failed for %s: %s", abha_id, e)
        raise HTTPException(status_code=503, detail="ABDM gateway unavailable")


@router.post("/fetch-history", response_model=ABDMFetchResponse)
async def fetch_patient_history(
    request: ABDMFetchRequest,
    current_user: dict = Depends(get_current_user),
):
    """Fetch patient health records from ABDM (requires consent)."""
    from backend.services.abdm_service import ABDMService
    abdm = ABDMService()

    try:
        records = await abdm.request_health_records(
            abha_id=request.abha_id,
            date_from=request.date_from,
            date_to=request.date_to,
        )
        return ABDMFetchResponse(
            consent_status="approved",
            records_count=len(records),
            records=records,
        )
    except Exception as e:
        logger.error("ABDM fetch failed: %s", e)
        raise HTTPException(status_code=503, detail=f"Failed to fetch records: {e}")


@router.post("/push-report", response_model=ABDMPushResponse)
async def push_report_to_abdm(
    request: ABDMPushRequest,
    current_user: dict = Depends(get_current_user),
):
    """Push PRISM diagnostic report to patient's ABHA health locker."""
    from backend.services.abdm_service import ABDMService
    from backend.db.supabase_client import get_supabase_client

    client = get_supabase_client()

    # Get session results
    session = client.table("diagnostic_sessions").select("*").eq("id", request.session_id).execute()
    if not session.data:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.data[0]["status"] != "complete":
        raise HTTPException(status_code=400, detail="Analysis not complete")

    abdm = ABDMService()
    try:
        abdm_record_id = await abdm.push_diagnostic_report(
            abha_id=request.abha_id,
            prism_report=session.data[0],
        )

        # Update clinical report record
        client.table("clinical_reports").update({
            "abdm_push_status": "success",
            "abdm_record_id": abdm_record_id,
        }).eq("session_id", request.session_id).execute()

        return ABDMPushResponse(status="success", abdm_record_id=abdm_record_id)

    except Exception as e:
        logger.error("ABDM push failed: %s", e)
        client.table("clinical_reports").update({
            "abdm_push_status": "failed",
            "abdm_push_error": str(e),
        }).eq("session_id", request.session_id).execute()
        raise HTTPException(status_code=503, detail=f"ABDM push failed: {e}")
