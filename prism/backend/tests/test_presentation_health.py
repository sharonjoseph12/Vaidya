"""Smoke tests for evaluation / presentation health endpoints."""

from fastapi.testclient import TestClient


def test_health_ml_reports_real_artifacts_when_bootstrapped():
    from backend.main import app

    client = TestClient(app)
    r = client.get("/health/ml")
    assert r.status_code == 200
    data = r.json()
    assert "artifacts" in data
    art = data["artifacts"]
    for key in ("yamnet_audio", "lstm_trajectory", "causal_explainer"):
        assert key in art
        assert "is_real" in art[key]
        assert art[key]["is_real"] is True, f"Run: python scripts/bootstrap_presentation_artifacts.py ({key})"


def test_health_sense_returns_json():
    from backend.main import app

    client = TestClient(app)
    r = client.get("/health/sense")
    assert r.status_code == 200
    body = r.json()
    assert "python_version" in body
    assert "use_real_sense_config" in body
