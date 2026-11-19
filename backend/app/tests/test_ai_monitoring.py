"""
Unit & Integration Tests: Phase 10 - AI-Based Suspicious Activity Monitoring
Verifies:
- Scikit-learn Isolation Forest unsupervised baseline
- Deterministic heuristic rule triggers:
  * Nocturnal bulk image download exfiltration
  * Brute-force decryption / repeated key guessing
  * Credential stuffing / rapid login failures
- Alert lifecycle: Generation, risk scoring, and administrative resolution
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.db_models import User, SecurityAlert
from app.ai_monitoring.anomaly_detector import AISecuritySentry
from app.security.token_util import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "sec_admin").first()
    token = create_access_token({"sub": admin.user_id, "username": admin.username, "role": "ADMIN"})
    db.close()
    return {"Authorization": f"Bearer {token}"}

def test_isolation_forest_model_initialization():
    sentry = AISecuritySentry.get_instance()
    assert sentry._model is not None

    # Normal daytime clinical access
    normal_features = {
        "hour_of_day": 11.5,
        "is_nocturnal": False,
        "failed_logins_recent": 0,
        "failed_decryptions_recent": 0,
        "download_count_recent": 1,
        "request_rate_recent": 5,
        "privilege_level": 1
    }
    result = sentry.analyze_event(normal_features)
    assert result["is_anomaly"] is False
    assert result["risk_score"] < 50.0

def test_heuristic_nocturnal_bulk_download_detection():
    sentry = AISecuritySentry.get_instance()
    db = SessionLocal()
    try:
        nocturnal_features = {
            "hour_of_day": 3.0,
            "is_nocturnal": True,
            "failed_logins_recent": 0,
            "failed_decryptions_recent": 0,
            "download_count_recent": 5,
            "request_rate_recent": 12,
            "privilege_level": 1
        }
        res = sentry.analyze_event(nocturnal_features, user_id="clinician_99", db=db)
        assert res["is_anomaly"] is True
        assert res["severity"] == "CRITICAL"
        assert res["alert_type"] == "NOCTURNAL_BULK_DOWNLOAD"
        assert res["risk_score"] > 90.0

        # Check DB persistence
        alert = db.query(SecurityAlert).filter(SecurityAlert.alert_type == "NOCTURNAL_BULK_DOWNLOAD").first()
        assert alert is not None
        assert alert.severity == "CRITICAL"
        assert alert.is_resolved is False
    finally:
        db.close()

def test_heuristic_brute_force_decryption_detection():
    sentry = AISecuritySentry.get_instance()
    features = {
        "hour_of_day": 14.0,
        "failed_decryptions_recent": 4,
        "request_rate_recent": 20
    }
    res = sentry.analyze_event(features)
    assert res["is_anomaly"] is True
    assert res["severity"] == "HIGH"
    assert res["alert_type"] == "BRUTE_FORCE_DECRYPTION"

def test_heuristic_credential_stuffing_detection():
    sentry = AISecuritySentry.get_instance()
    features = {
        "hour_of_day": 18.0,
        "failed_logins_recent": 5,
        "request_rate_recent": 25
    }
    res = sentry.analyze_event(features)
    assert res["is_anomaly"] is True
    assert res["severity"] == "HIGH"
    assert res["alert_type"] == "CREDENTIAL_STUFFING"

def test_api_attack_simulation_and_resolution(auth_headers):
    # Simulate nocturnal attack
    sim_resp = client.post(
        "/api/v1/monitoring/simulate-attack?attack_type=NOCTURNAL_BULK_DOWNLOAD",
        headers=auth_headers
    )
    assert sim_resp.status_code == 200
    sim_data = sim_resp.json()
    assert sim_data["status"] == "SIMULATED"
    alert_id = sim_data["detection_result"].get("alert_id")

    # Fetch alerts
    alerts_resp = client.get("/api/v1/monitoring/alerts?resolved=false", headers=auth_headers)
    assert alerts_resp.status_code == 200
    assert alerts_resp.json()["total_alerts"] >= 1

    # Resolve alert
    if alert_id:
        resolve_resp = client.post(f"/api/v1/monitoring/resolve/{alert_id}", headers=auth_headers)
        assert resolve_resp.status_code == 200
        assert resolve_resp.json()["status"] == "SUCCESS"

    # Fetch statistics
    stats_resp = client.get("/api/v1/monitoring/stats", headers=auth_headers)
    assert stats_resp.status_code == 200
    assert "severity_breakdown" in stats_resp.json()
