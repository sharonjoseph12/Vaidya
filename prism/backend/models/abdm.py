"""
PRISM Platform — ABDM/ABHA Pydantic Schemas
Data models for India's Ayushman Bharat Digital Mission integration.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ABHAProfile(BaseModel):
    """Patient profile from ABDM."""
    verified: bool = False
    name: str = ""
    age: int = 0
    gender: str = ""
    abha_address: Optional[str] = None


class ConsentRequest(BaseModel):
    """Consent request for fetching health records."""
    abha_id: str
    date_from: str = Field(..., description="ISO date string YYYY-MM-DD")
    date_to: str = Field(..., description="ISO date string YYYY-MM-DD")
    hi_types: list[str] = Field(
        default=["DiagnosticReport", "Prescription", "OPConsultation"],
        description="Health Information types to fetch"
    )
    purpose: str = Field(default="CAREMGT", description="Purpose code")


class HealthRecord(BaseModel):
    """Parsed health record from ABDM FHIR bundle."""
    type: str = Field(..., description="diagnostic, observation, prescription")
    date: str
    findings: Optional[str] = None
    parameter: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    codes: list[str] = Field(default_factory=list)


class ABDMFetchRequest(BaseModel):
    """Request to fetch patient health records from ABDM."""
    abha_id: str
    date_from: str
    date_to: str
    hi_types: list[str] = Field(
        default=["DiagnosticReport", "Prescription", "OPConsultation"]
    )


class ABDMPushRequest(BaseModel):
    """Request to push diagnostic report to ABDM."""
    session_id: str
    abha_id: str


class ABDMFetchResponse(BaseModel):
    """Response from ABDM health records fetch."""
    consent_status: str
    records_count: int
    records: list[HealthRecord] = Field(default_factory=list)
    twin_enrichment: Optional[dict] = None


class ABDMPushResponse(BaseModel):
    """Response from ABDM report push."""
    status: str
    abdm_record_id: Optional[str] = None
    fhir_resource_type: str = "DiagnosticReport"
