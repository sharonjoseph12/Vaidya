"""
PRISM Platform — Patient CRUD Endpoints
Handles patient registration, retrieval, and management with encryption.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from uuid import UUID
import logging

from backend.utils.auth import get_current_user
from backend.utils.encryption import encrypt_demographics, decrypt_demographics
from backend.db.supabase_client import get_supabase_client, log_audit
from backend.models.patient import (
    PatientCreate,
    PatientResponse,
    PatientUpdate,
    PatientListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Register a new patient with encrypted demographics."""
    client = get_supabase_client()

    # Encrypt demographics before storage
    encrypted = encrypt_demographics(patient.demographics.model_dump())

    insert_data = {
        "encrypted_demographics": encrypted.hex(),  # Store as hex string for BYTEA
        "consent_given": patient.consent_given,
        "consent_timestamp": "now()",
        "consent_purpose": patient.consent_purpose,
        "device_info": patient.device_info,
    }

    if patient.abha_id:
        insert_data["abha_id"] = patient.abha_id

    try:
        result = client.table("patients").insert(insert_data).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() and "abha_id" in str(e).lower():
            raise HTTPException(status_code=409, detail="Patient with this ABHA ID already exists")
        raise HTTPException(status_code=500, detail="Failed to create patient")

    row = result.data[0]

    # Audit log
    await log_audit(
        user_id=current_user["user_id"],
        action="create",
        resource_type="patient",
        resource_id=row["id"],
        ip_address=request.client.host if request.client else None,
    )

    return PatientResponse(
        id=row["id"],
        abha_id=row.get("abha_id"),
        created_at=row["created_at"],
        consent_given=row["consent_given"],
        demographics=patient.demographics,
    )


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    """Retrieve a patient record with decrypted demographics."""
    client = get_supabase_client()

    result = client.table("patients").select("*").eq("id", str(patient_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Patient not found")

    row = result.data[0]

    # Decrypt demographics
    demographics = None
    if row.get("encrypted_demographics"):
        try:
            encrypted_bytes = bytes.fromhex(row["encrypted_demographics"])
            demographics = decrypt_demographics(encrypted_bytes)
        except Exception as e:
            logger.error("Failed to decrypt demographics for patient %s: %s", patient_id, e)

    # Count sessions
    sessions = client.table("diagnostic_sessions").select("id, created_at").eq(
        "patient_id", str(patient_id)
    ).order("created_at", desc=True).execute()

    # Audit log
    await log_audit(
        user_id=current_user["user_id"],
        action="read",
        resource_type="patient",
        resource_id=str(patient_id),
        ip_address=request.client.host if request.client else None,
    )

    return PatientResponse(
        id=row["id"],
        abha_id=row.get("abha_id"),
        created_at=row["created_at"],
        consent_given=row["consent_given"],
        demographics=demographics,
        sessions_count=len(sessions.data) if sessions.data else 0,
        last_session_date=sessions.data[0]["created_at"] if sessions.data else None,
    )


@router.get("", response_model=PatientListResponse)
async def list_patients(
    page: int = 1,
    per_page: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """List patients with pagination."""
    client = get_supabase_client()
    offset = (page - 1) * per_page

    result = client.table("patients").select(
        "id, abha_id, created_at, consent_given", count="exact"
    ).range(offset, offset + per_page - 1).order("created_at", desc=True).execute()

    patients = [
        PatientResponse(
            id=row.get("id"),
            abha_id=row.get("abha_id"),
            created_at=row.get("created_at"),
            consent_given=row.get("consent_given"),
        )
        for row in (result.data or [])
    ]

    return PatientListResponse(
        patients=patients,
        total=result.count or 0,
        page=page,
        per_page=per_page,
    )


@router.get("/{patient_id}/sessions")
async def get_patient_sessions(
    patient_id: UUID,
    current_user: dict = Depends(get_current_user),
):
    """Get all diagnostic sessions for a patient, sorted by date descending."""
    client = get_supabase_client()

    result = (
        client.table("diagnostic_sessions")
        .select("id, primary_diagnosis, confidence_score, disease_probabilities, sense_results, created_at, status")
        .eq("patient_id", str(patient_id))
        .eq("status", "complete")
        .order("created_at", desc=True)
        .execute()
    )

    return result.data or []
