"""
Phase 5 Automated Verification Suite: Cellular Automata Reversible Diffusion
Tests Rule 30 and Rule 90 transitions, periodic boundary conditions,
deterministic mask derivation, exact lossless inverse recovery, and avalanche effects.
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.encryption.cellular_automata import CellularAutomataDiffuser, CAError
from app.decryption.ca_inversion import CADecryptor
from app.database.connection import SessionLocal
from app.database.init_db import init_database
from app.models.db_models import User
from app.security.token_util import create_access_token

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_database()

@pytest.fixture
def auth_headers():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "dr_alice_radiology").first()
        token = create_access_token({
            "sub": user.user_id,
            "username": user.username,
            "role": user.role.role_name if user.role else "USER"
        })
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()

def test_rule_30_transition_table():
    diffuser = CellularAutomataDiffuser(rule=30)
    # Test all 8 configurations: (left, center, right)
    configs = [
        (1, 1, 1, 0),
        (1, 1, 0, 0),
        (1, 0, 1, 0),
        (1, 0, 0, 1),
        (0, 1, 1, 1),
        (0, 1, 0, 1),
        (0, 0, 1, 1),
        (0, 0, 0, 0),
    ]
    for left, center, right, expected in configs:
        res = diffuser._apply_rule_30(
            np.array([left], dtype=np.uint8),
            np.array([center], dtype=np.uint8),
            np.array([right], dtype=np.uint8)
        )
        assert res[0] == expected, f"Rule 30 failed for ({left},{center},{right})"

def test_rule_90_transition_table():
    diffuser = CellularAutomataDiffuser(rule=90)
    configs = [
        (1, 1, 1, 0),
        (1, 1, 0, 1),
        (1, 0, 1, 0),
        (1, 0, 0, 1),
        (0, 1, 1, 1),
        (0, 1, 0, 0),
        (0, 0, 1, 1),
        (0, 0, 0, 0),
    ]
    for left, center, right, expected in configs:
        res = diffuser._apply_rule_90(
            np.array([left], dtype=np.uint8),
            np.array([center], dtype=np.uint8),
            np.array([right], dtype=np.uint8)
        )
        assert res[0] == expected, f"Rule 90 failed for ({left},{center},{right})"

def test_unsupported_rule_rejection():
    with pytest.raises(CAError):
        CellularAutomataDiffuser(rule=45)

def test_deterministic_keystream_mask():
    seed = b"NIST_P256_SHARED_KEY_CA_TEST"
    mask1 = CellularAutomataDiffuser.generate_keystream_mask(1024, seed, rule=30)
    mask2 = CellularAutomataDiffuser.generate_keystream_mask(1024, seed, rule=30)
    np.testing.assert_array_equal(mask1, mask2)

    # Different rule produces different mask
    mask_90 = CellularAutomataDiffuser.generate_keystream_mask(1024, seed, rule=90)
    assert not np.array_equal(mask1, mask_90)

def test_exact_lossless_diffusion_and_recovery():
    seed = b"CLINICAL_SESSION_CA_DIFFUSION"
    np.random.seed(42)
    # 65536 byte image vector
    original_vector = np.random.randint(0, 256, 65536, dtype=np.uint8)

    # Test Rule 30
    diffuser_30 = CellularAutomataDiffuser(rule=30)
    diffused_30, mask_30 = diffuser_30.diffuse(original_vector, seed)
    assert len(diffused_30) == len(original_vector)
    assert not np.array_equal(diffused_30, original_vector)

    # Invert via diffuser
    recovered_30 = diffuser_30.invert_diffuse(diffused_30, seed)
    np.testing.assert_array_equal(recovered_30, original_vector)

    # Invert via CADecryptor module
    recovered_from_decryptor = CADecryptor.invert(diffused_30, seed, rule=30)
    np.testing.assert_array_equal(recovered_from_decryptor, original_vector)

    # Test Rule 90
    diffuser_90 = CellularAutomataDiffuser(rule=90)
    diffused_90, _ = diffuser_90.diffuse(original_vector, seed)
    recovered_90 = diffuser_90.invert_diffuse(diffused_90, seed)
    np.testing.assert_array_equal(recovered_90, original_vector)

def test_avalanche_effect():
    results = CellularAutomataDiffuser.evaluate_avalanche_effect(length=2000, rule=30)
    # Avalanche flip rate should be close to 50% (> 45%)
    assert results["avalanche_percentage"] > 45.0
    # Shannon entropy of the ECA mask is typically ~7.81 (> 7.75) for Rule 30
    assert results["shannon_entropy"] > 7.75

    # Check larger 65,536-byte array maintains robust entropy and avalanche
    large_results = CellularAutomataDiffuser.evaluate_avalanche_effect(length=65536, rule=30)
    assert large_results["avalanche_percentage"] > 45.0
    assert large_results["shannon_entropy"] > 7.75

def test_api_ca_avalanche_endpoint():
    response = client.get("/api/v1/crypto/ca/avalanche?rule=30&length=1000")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "avalanche_percentage" in data
    assert "shannon_entropy" in data
    assert data["shannon_entropy"] > 7.75
