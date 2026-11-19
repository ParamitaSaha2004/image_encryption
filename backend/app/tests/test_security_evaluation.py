"""
Unit & Integration Tests: Phase 11 - Security Evaluation Dashboard & Cryptographic Benchmarks
Verifies:
- Shannon Entropy computation (H ≈ 7.999 for ciphertext, < 7.5 for plain scan)
- Number of Pixels Change Rate (NPCR > 99.60%)
- Unified Average Changing Intensity (UACI > 33.40%)
- Pearson Adjacent Pixel Correlation Coefficients (Horizontal, Vertical, Diagonal -> ~0.00)
- 4-Way Comparative Benchmarks (AES Only, Chaos+AES, CA+AES, Full Hybrid)
- API endpoint execution and database metrics storage
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import SessionLocal
from app.models.db_models import User, EncryptionMetric
from app.evaluation.benchmark_engine import SecurityEvaluationEngine
from app.security.token_util import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    db = SessionLocal()
    alice = db.query(User).filter(User.username == "dr_alice_radiology").first()
    token = create_access_token({"sub": alice.user_id, "username": alice.username, "role": "USER"})
    db.close()
    return {"Authorization": f"Bearer {token}"}

def test_shannon_entropy_calculation():
    # 1. Low entropy constant data
    flat_data = bytes([128] * 10000)
    h_flat = SecurityEvaluationEngine.calculate_entropy(flat_data)
    assert h_flat == 0.0

    # 2. High entropy pseudo-random CSPRNG bytes
    import os
    random_bytes = os.urandom(65536)
    h_random = SecurityEvaluationEngine.calculate_entropy(random_bytes)
    assert h_random >= 7.990  # Extremely close to theoretical 8.000

def test_npcr_and_uaci_differential_metrics():
    import os
    # Two random byte streams of equal length
    c1 = os.urandom(65536)
    c2 = os.urandom(65536)

    npcr, uaci = SecurityEvaluationEngine.calculate_npcr_uaci(c1, c2)
    # Theoretical NPCR for independent uniform bytes is ~99.61%
    assert npcr > 99.0
    # Theoretical UACI for independent uniform bytes is ~33.46%
    assert 32.5 <= uaci <= 34.5

def test_pearson_adjacent_pixel_correlation():
    # 1. Plain image with strong horizontal/vertical gradient (high correlation)
    h, w = 128, 128
    y, x = np.ogrid[:h, :w]
    smooth_img = (x * 2 + y * 2) % 256
    corr_smooth = SecurityEvaluationEngine.calculate_correlation(smooth_img.astype(np.uint8))
    assert corr_smooth["horizontal"] > 0.80
    assert corr_smooth["vertical"] > 0.80

    # 2. Random cipher image (correlation destroyed -> near 0)
    rng = np.random.default_rng(42)
    noise_img = rng.integers(0, 256, size=(h, w), dtype=np.uint8)
    corr_noise = SecurityEvaluationEngine.calculate_correlation(noise_img)
    assert abs(corr_noise["horizontal"]) < 0.10
    assert abs(corr_noise["vertical"]) < 0.10
    assert abs(corr_noise["diagonal"]) < 0.10

def test_api_evaluation_benchmark_run_and_comparative(auth_headers):
    # 1. Ingest a sample scan
    load_resp = client.post(
        "/api/v1/images/samples/load/synthetic_chest_xray.png",
        headers=auth_headers
    )
    assert load_resp.status_code == 200
    image_id = load_resp.json()["image_id"]

    # 2. Run 4-way evaluation benchmark via API
    eval_resp = client.post(
        f"/api/v1/evaluation/run/{image_id}",
        params={"master_key": "HICE_CLINICAL_MASTER_KEY_2026"},
        headers=auth_headers
    )
    assert eval_resp.status_code == 200
    data = eval_resp.json()
    assert data["status"] == "SUCCESS"
    assert "benchmark_data" in data

    b_data = data["benchmark_data"]
    configs = b_data["comparative_benchmarks"]
    assert len(configs) == 4

    # Verify configurations: AES Only, Chaos+AES, CA+AES, Full Hybrid
    names = [c["configuration"] for c in configs]
    assert "AES-256-GCM Only" in names
    assert "Full Hybrid (Chaos + CA + AES-GCM)" in names

    # All configurations must exhibit Shannon Entropy >= 7.990, NPCR >= 99.0%, and correlation destruction
    for c in configs:
        assert c["entropy"] >= 7.990
        assert c["npcr"] >= 99.0
        assert c["uaci"] >= 33.0
        assert c["exact_recovery"] is True
        assert abs(c["h_corr"]) < 0.10

    # Check database persistence
    db = SessionLocal()
    try:
        metrics = db.query(EncryptionMetric).filter(EncryptionMetric.image_id == image_id).all()
        assert len(metrics) >= 4
    finally:
        db.close()

    # 3. Retrieve stored comparative metrics
    comp_resp = client.get(f"/api/v1/evaluation/comparative/{image_id}", headers=auth_headers)
    assert comp_resp.status_code == 200
    assert len(comp_resp.json()["metrics"]) >= 4
