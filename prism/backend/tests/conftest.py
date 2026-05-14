"""
PRISM Platform — Test Configuration and Fixtures
Provides mock Supabase clients, test patients, and shared fixtures.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def mock_supabase():
    """Mock Supabase client for unit testing."""
    client = MagicMock()
    client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[], count=0)
    client.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{
        "id": "test-uuid-1234",
        "created_at": "2026-05-14T00:00:00Z",
        "consent_given": True,
    }])
    return client


@pytest.fixture
def test_patient_features():
    """Standard test patient features."""
    return {
        "nutrition_score": 3.0,
        "bmi": 17.5,
        "age": 32,
        "crowding_index": 4.2,
        "smoking_status": 0,
        "activity_level": 2,
        "monthly_income": 8000,
    }


@pytest.fixture
def test_sense_results():
    """Mock Layer 1 SENSE results."""
    return {
        "disease_probabilities": {
            "TB": 0.79, "Pneumonia": 0.12, "Anemia": 0.68,
            "Asthma": 0.05, "COPD": 0.03, "Dengue": 0.02,
        },
        "rppg": {"hr": 74.2, "spo2": 96.1, "hrv_rmssd": 42.3, "rr": 18.5},
        "audio": {"cough_detected": True, "cough_count": 3},
        "visual": {"anemia_score": 0.68, "pallor_score": 0.55},
        "uncertainty": {"TB": [0.71, 0.86]},
        "modalities_available": ["audio", "visual", "rppg"],
        "processing_time_ms": 1200,
    }


@pytest.fixture
def test_session_data(test_sense_results):
    """Complete mock diagnostic session."""
    return {
        "id": "session-uuid-5678",
        "patient_id": "patient-uuid-1234",
        "status": "complete",
        "session_type": "full",
        "sense_results": test_sense_results,
        "disease_probabilities": test_sense_results["disease_probabilities"],
        "primary_diagnosis": "TB",
        "confidence_score": 0.79,
        "model_version": "prism-v1.0.0",
        "processing_time_ms": 2800,
    }
