"""
PRISM Platform — ABDM Service
ABDM gateway client for ABHA verification, consent, health record fetch/push.
"""
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional
from backend.models.abdm import ABHAProfile, HealthRecord

logger = logging.getLogger(__name__)


class ABDMService:
    """Client for India's ABDM (Ayushman Bharat Digital Mission) gateway."""

    def __init__(self):
        from backend.config import get_settings
        s = get_settings()
        self.client_id = s.abdm_client_id
        self.client_secret = s.abdm_client_secret
        self.base_url = s.abdm_base_url
        self.access_token: Optional[str] = None
        self.token_expiry: Optional[datetime] = None

    async def _ensure_authenticated(self):
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/v0.5/sessions",
                json={"clientId": self.client_id, "clientSecret": self.client_secret},
            )
            if resp.status_code == 200:
                data = resp.json()
                self.access_token = data.get("accessToken")
                self.token_expiry = datetime.now() + timedelta(seconds=data.get("expiresIn", 1800))
            else:
                raise Exception(f"ABDM auth failed: {resp.status_code}")

    def _headers(self):
        return {"Authorization": f"Bearer {self.access_token}", "X-CM-ID": "sbx"}

    async def verify_abha(self, abha_id: str) -> ABHAProfile:
        await self._ensure_authenticated()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/v0.5/patients/profile",
                headers=self._headers(),
                params={"healthId": abha_id},
            )
            if resp.status_code == 200:
                d = resp.json()
                return ABHAProfile(verified=True, name=d.get("name",""), age=d.get("yearOfBirth",0), gender=d.get("gender",""))
            return ABHAProfile(verified=False)

    async def request_health_records(self, abha_id: str, date_from: str, date_to: str) -> list[HealthRecord]:
        await self._ensure_authenticated()
        # Simplified: In production, this involves consent flow
        logger.info("Fetching health records for %s from %s to %s", abha_id, date_from, date_to)
        # Return empty for sandbox — actual records come via consent flow
        return []

    async def push_diagnostic_report(self, abha_id: str, prism_report: dict) -> str:
        await self._ensure_authenticated()
        # Build FHIR DiagnosticReport
        fhir_report = self._build_fhir_report(prism_report)
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/v0.5/health-information/notify",
                json=fhir_report,
                headers=self._headers(),
            )
            if resp.status_code in (200, 201):
                return resp.json().get("id", "mock-abdm-record-id")
            raise Exception(f"ABDM push failed: {resp.status_code}")

    def _build_fhir_report(self, report: dict) -> dict:
        """Convert PRISM results to FHIR R4 DiagnosticReport."""
        observations = []
        for disease, prob in report.get("disease_probabilities", {}).items():
            observations.append({
                "resourceType": "Observation",
                "status": "final",
                "code": {"coding": [{"display": f"PRISM {disease} probability"}]},
                "valueQuantity": {"value": prob, "unit": "probability"},
            })
        return {
            "resourceType": "DiagnosticReport",
            "status": "final",
            "code": {"coding": [{"display": "PRISM Multimodal Diagnostic Report"}]},
            "conclusion": report.get("primary_diagnosis", ""),
        }
