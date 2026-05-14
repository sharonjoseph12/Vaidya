"""
PRISM Platform — Clinical Report Pydantic Schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ClinicalReportCreate(BaseModel):
    """Schema for generating a clinical report."""
    session_id: UUID


class ClinicalReportResponse(BaseModel):
    """Schema for clinical report API responses."""
    id: UUID
    session_id: UUID
    generated_at: datetime
    report_pdf_url: Optional[str] = None
    abdm_push_status: str = "not_requested"
    abdm_record_id: Optional[str] = None

    model_config = {"from_attributes": True}
