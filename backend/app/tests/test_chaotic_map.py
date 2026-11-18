"""
Phase 4 Automated Verification Suite: Chaotic Map Permutation Engine
Tests Logistic Map dynamics, parameter constraints, deterministic seeding,
lossless inverse recovery, and key sensitivity experiments.
"""
import pytest
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.encryption.chaotic_map import LogisticMap, ChaoticMapError
from app.decryption.chaotic_inversion import ChaoticInverter
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

def test_parameter_validation():
    # Valid parameters
    l_valid = LogisticMap(r=3.999, x0=0.5123)
    assert l_valid.r == 3.999
    assert l_valid.x0 == 0.5123

    # Invalid r < 3.90 (non-chaotic regime)
    with pytest.raises(ChaoticMapError):
        LogisticMap(r=3.5, x0=0.5)

    # Invalid r > 4.00 (divergent)
    with pytest.raises(ChaoticMapError):
        LogisticMap(r=4.1, x0=0.5)

    # Invalid x0 bounds
    with pytest.raises(ChaoticMapError):
        LogisticMap(r=3.99, x0=0.0)
    with pytest.raises(ChaoticMapError):
        LogisticMap(r=3.99, x0=1.0)
    with pytest.raises(ChaoticMapError):
        LogisticMap(r=3.99, x0=-0.1)

def test_deterministic_seeding():
    seed = b"NIST_P256_SHARED_SECRET_KEY"
    map1 = LogisticMap.from_seed(seed)
    map2 = LogisticMap.from_seed(seed)
    
    assert map1.r == map2.r
    assert map1.x0 == map2.x0

    seq1 = map1.generate_sequence(500)
    seq2 = map2.generate_sequence(500)
    np.testing.assert_array_equal(seq1, seq2)

def test_lossless_permutation_and_inversion():
    seed = b"CLINICAL_TRIAL_PATIENT_SCAN"
    logistic = LogisticMap.from_seed(seed)

    # Simulated image pixel vector (e.g. 256x256 grayscale = 65,536 bytes)
    np.random.seed(1337)
    original_vector = np.random.randint(0, 256, 65536, dtype=np.uint8)

    # Forward permutation
    permuted, inv_perm = logistic.permute(original_vector)
    assert len(permuted) == len(original_vector)
    assert not np.array_equal(permuted, original_vector)

    # Multiset preservation: Sorted byte values must be identical
    np.testing.assert_array_equal(np.sort(permuted), np.sort(original_vector))

    # Inverse permutation recovery
    recovered = LogisticMap.inverse_permute(permuted, inv_perm)
    np.testing.assert_array_equal(recovered, original_vector)

    # Also test via ChaoticInverter helper
    recovered_from_seed = ChaoticInverter.recover(permuted, seed)
    np.testing.assert_array_equal(recovered_from_seed, original_vector)

def test_key_sensitivity_experiment():
    """
    Evaluates that a change in initial condition of only 10^-14
    causes trajectories to diverge and creates a completely different permutation.
    """
    seed = b"BASELINE_SECRET_KEY"
    delta = 1e-14
    results = LogisticMap.evaluate_sensitivity(seed, delta=delta, length=2000)

    # Divergence ratio should be > 95%
    assert results["perm_difference_ratio"] > 0.95
    # Trajectory cross-correlation should be low (< 0.20)
    assert abs(results["trajectory_correlation"]) < 0.20

def test_api_chaos_sensitivity_endpoint():
    response = client.get("/api/v1/crypto/chaos/sensitivity?delta=1e-14")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "trajectory_cross_correlation" in data
    assert "perm_index_divergence_ratio" in data
    assert data["perm_index_divergence_ratio"] > 0.90
