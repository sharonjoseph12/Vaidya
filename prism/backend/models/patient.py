"""
PRISM Platform — Patient Pydantic Schemas
Defines request/response models for Patient CRUD operations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from uuid import UUID
import re


class DemographicsSchema(BaseModel):
    """Patient demographics (encrypted at rest in DB)."""
    name: str = Field(..., min_length=1, max_length=200)
    age: int = Field(..., ge=0, le=150)
    sex: str = Field(..., pattern=r"^(M|F|O)$")
    location: str = Field(default="", max_length=500)
    socioeconomic_tier: Optional[str] = Field(
        default=None,
        description="e.g., BPL, APL, or income bracket"
    )


class PatientCreate(BaseModel):
    """Schema for creating a new patient."""
    abha_id: Optional[str] = Field(
        default=None,
        description="ABHA ID in format XX-XXXX-XXXX-XXXX"
    )
    demographics: DemographicsSchema
    consent_given: bool = Field(
        ...,
        description="Patient must consent before any data collection"
    )
    consent_purpose: Optional[str] = Field(
        default="CAREMGT",
        description="Purpose: CAREMGT, RESEARCH, etc."
    )
    device_info: Optional[dict] = None

    @field_validator("abha_id")
    @classmethod
    def validate_abha_format(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^\d{2}-\d{4}-\d{4}-\d{4}$", v):
            raise ValueError("ABHA ID must be in format XX-XXXX-XXXX-XXXX")
        return v

    @field_validator("consent_given")
    @classmethod
    def consent_must_be_true(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Patient consent is required before data collection")
        return v


class PatientResponse(BaseModel):
    """Schema for patient API responses."""
    id: UUID
    abha_id: Optional[str] = None
    created_at: datetime
    consent_given: bool
    demographics: Optional[DemographicsSchema] = None
    sessions_count: int = 0
    last_session_date: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PatientUpdate(BaseModel):
    """Schema for updating patient info."""
    abha_id: Optional[str] = None
    demographics: Optional[DemographicsSchema] = None
    device_info: Optional[dict] = None

    @field_validator("abha_id")
    @classmethod
    def validate_abha_format(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^\d{2}-\d{4}-\d{4}-\d{4}$", v):
            raise ValueError("ABHA ID must be in format XX-XXXX-XXXX-XXXX")
        return v


class PatientListResponse(BaseModel):
    """Paginated patient list response."""
    patients: list[PatientResponse]
    total: int
    page: int
    per_page: int
