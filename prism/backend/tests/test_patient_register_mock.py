"""Patient registration + AES-GCM encryption with in-memory Supabase mock."""

import os
from io import BytesIO
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def _isolated_prism_mock_db_json(tmp_path, monkeypatch):
    """Avoid writing a shared ``.prism_mock_db.json`` in the repo during tests."""
    monkeypatch.setenv("PRISM_MOCK_DB_JSON", str(tmp_path / "prism_mock_db.json"))
    from backend.db import supabase_client as sc

    sc.get_supabase_client.cache_clear()
    yield
    sc.get_supabase_client.cache_clear()


def _dev_env():
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
    os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
    os.environ.setdefault(
        "ENCRYPTION_KEY",
        "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    )
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DEBUG", "true")


def test_encrypt_demographics_roundtrip():
    _dev_env()
    with patch("supabase.create_client", side_effect=RuntimeError("force mock")):
        from backend.db import supabase_client as sc

        sc.get_supabase_client.cache_clear()

        from backend.utils.encryption import encrypt_demographics, decrypt_demographics

        payload = {"name": "Ada", "age": 42, "sex": "F", "location": "Test"}
        blob = encrypt_demographics(payload)
        assert decrypt_demographics(blob) == payload


def test_post_patients_returns_201_with_id():
    _dev_env()
    with patch("supabase.create_client", side_effect=RuntimeError("force mock")):
        from backend.db import supabase_client as sc

        sc.get_supabase_client.cache_clear()

        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        body = {
            "consent_given": True,
            "consent_purpose": "diagnostic_screening",
            "demographics": {
                "name": "Test User",
                "age": 35,
                "sex": "M",
                "location": "Lab",
            },
        }
        r = client.post(
            "/api/v1/patients",
            json=body,
            headers={"Authorization": "Bearer DEMO_TOKEN"},
        )
        assert r.status_code == 201, r.text
        data = r.json()
        assert "id" in data
        assert data["demographics"]["name"] == "Test User"


def test_get_patient_decrypts_demographics():
    _dev_env()
    with patch("supabase.create_client", side_effect=RuntimeError("force mock")):
        from backend.db import supabase_client as sc

        sc.get_supabase_client.cache_clear()

        from fastapi.testclient import TestClient
        from backend.main import app

        c = TestClient(app)
        created = c.post(
            "/api/v1/patients",
            json={
                "consent_given": True,
                "demographics": {
                    "name": "Roundtrip",
                    "age": 50,
                    "sex": "O",
                    "location": "X",
                },
            },
            headers={"Authorization": "Bearer DEMO_TOKEN"},
        ).json()
        pid = created["id"]

        got = c.get(
            f"/api/v1/patients/{pid}",
            headers={"Authorization": "Bearer DEMO_TOKEN"},
        )
        assert got.status_code == 200, got.text
        assert got.json()["demographics"]["name"] == "Roundtrip"


def test_post_analyze_returns_202_when_patient_exists():
    _dev_env()
    with patch("supabase.create_client", side_effect=RuntimeError("force mock")):
        from backend.db import supabase_client as sc

        sc.get_supabase_client.cache_clear()

        from fastapi.testclient import TestClient
        from backend.main import app

        c = TestClient(app)
        created = c.post(
            "/api/v1/patients",
            json={
                "consent_given": True,
                "demographics": {
                    "name": "Scan User",
                    "age": 40,
                    "sex": "M",
                    "location": "Y",
                },
            },
            headers={"Authorization": "Bearer DEMO_TOKEN"},
        ).json()
        pid = created["id"]

        form = {
            "patient_id": pid,
            "patient_features": "{}",
        }
        files = {
            "video_file": ("scan.webm", BytesIO(b"fake-webm"), "video/webm"),
        }
        r = c.post(
            "/api/v1/diagnostics/analyze",
            data=form,
            files=files,
            headers={"Authorization": "Bearer DEMO_TOKEN"},
        )
        assert r.status_code == 202, r.text
        body = r.json()
        assert "session_id" in body


def test_encryption_key_validation_rejects_bad_length():
    _dev_env()
    bad = "cGxhY2Vob2xkZXIta2V5LTMyLWJ5dGVzLWxvbmc="
    from pydantic import ValidationError
    from backend.config import Settings

    with pytest.raises(ValidationError) as excinfo:
        Settings(
            supabase_url="https://test.supabase.co",
            supabase_anon_key="a",
            supabase_service_key="b",
            encryption_key=bad,
        )
    msgs = str(excinfo.value)
    assert "AES-GCM" in msgs or "16, 24, or 32" in msgs
