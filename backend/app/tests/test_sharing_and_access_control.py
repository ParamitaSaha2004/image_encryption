"""
Comprehensive Unit & Integration Tests: Phase 8 - Secure Image Sharing & Granular Access Control
Verifies:
- NIST P-256 ECDH Key Encapsulation / Decapsulation
- Granular permissions: VIEW, DECRYPT, DOWNLOAD
- Expiration time window enforcement
- Instant cryptographic access revocation
- Recipient isolation and rejection of unauthorized decapsulators
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta
import json
import uuid

from app.main import app
from app.database.connection import SessionLocal
from app.models.db_models import User, EncryptedImage, ImageShare
from app.key_management.key_wrapper import KeyWrapper, KeyWrapError
from app.security.token_util import create_access_token

client = TestClient(app)

@pytest.fixture
def test_setup():
    db = SessionLocal()
    alice = db.query(User).filter(User.username == "dr_alice_radiology").first()
    bob = db.query(User).filter(User.username == "dr_bob_oncology").first()

    alice_token = create_access_token({"sub": alice.user_id, "username": alice.username, "role": "USER"})
    bob_token = create_access_token({"sub": bob.user_id, "username": bob.username, "role": "USER"})

    alice_headers = {"Authorization": f"Bearer {alice_token}"}
    bob_headers = {"Authorization": f"Bearer {bob_token}"}

    yield {
        "db": db,
        "alice": alice,
        "bob": bob,
        "alice_headers": alice_headers,
        "bob_headers": bob_headers
    }
    db.close()

def test_ecdh_key_encapsulation_and_decapsulation(test_setup):
    alice = test_setup["alice"]
    bob = test_setup["bob"]

    master_key = b"A" * 32
    aad = {"share_id": "test_share_123", "permission": "VIEW"}

    # Encapsulate under Bob's public key
    wrap_res = KeyWrapper.encapsulate_key(
        recipient_public_key_pem=bob.public_key_pem,
        plaintext_key=master_key,
        aad_metadata=aad
    )
    assert "ephemeral_public_key_pem" in wrap_res
    assert "encrypted_key_bundle" in wrap_res

    # Decapsulate using Bob's private key
    unwrapped = KeyWrapper.decapsulate_key(
        recipient_private_key_pem=bob.encrypted_private_key,
        ephemeral_public_key_pem=wrap_res["ephemeral_public_key_pem"],
        encrypted_key_bundle_json=wrap_res["encrypted_key_bundle"],
        aad_metadata=aad
    )
    assert unwrapped == master_key

    # Rejection: Alice's private key cannot decapsulate Bob's bundle
    with pytest.raises(KeyWrapError):
        KeyWrapper.decapsulate_key(
            recipient_private_key_pem=alice.encrypted_private_key,
            ephemeral_public_key_pem=wrap_res["ephemeral_public_key_pem"],
            encrypted_key_bundle_json=wrap_res["encrypted_key_bundle"],
            aad_metadata=aad
        )

def test_create_share_and_access_with_view_permission(test_setup):
    alice_headers = test_setup["alice_headers"]
    bob_headers = test_setup["bob_headers"]

    # 1. Load sample scan for Alice
    load_resp = client.post(
        "/api/v1/images/samples/load/synthetic_chest_xray.png",
        headers=alice_headers
    )
    assert load_resp.status_code == 200
    image_id = load_resp.json()["image_id"]

    # 2. Encrypt scan
    enc_resp = client.post(
        f"/api/v1/crypto/hybrid/encrypt/{image_id}",
        data={"master_key": "HICE_CLINICAL_MASTER_KEY_2026", "ca_rule": 30},
        headers=alice_headers
    )
    assert enc_resp.status_code == 200

    # 3. Share scan with Bob (permission: VIEW)
    share_resp = client.post(
        "/api/v1/shares/create",
        data={
            "image_id": image_id,
            "receiver_username": "dr_bob_oncology",
            "permission_type": "VIEW",
            "expiry_hours": 24,
            "master_key": "HICE_CLINICAL_MASTER_KEY_2026"
        },
        headers=alice_headers
    )
    assert share_resp.status_code == 201
    share_id = share_resp.json()["share_id"]

    # 4. Bob checks received shares
    rec_resp = client.get("/api/v1/shares/received", headers=bob_headers)
    assert rec_resp.status_code == 200
    shares = rec_resp.json()
    assert any(s["share_id"] == share_id for s in shares)

    # 5. Bob accesses scan (allowed)
    access_resp = client.post(f"/api/v1/shares/{share_id}/access", headers=bob_headers)
    assert access_resp.status_code == 200
    acc_data = access_resp.json()
    assert acc_data["status"] == "SUCCESS"
    assert acc_data["is_bit_exact"] is True
    assert acc_data["can_download"] is False

    # 6. Bob tries to download with VIEW permission (must be rejected with 403)
    down_resp = client.get(f"/api/v1/shares/{share_id}/download", headers=bob_headers)
    assert down_resp.status_code == 403
    assert "DOWNLOAD PERMISSION DENIED" in down_resp.json()["detail"]

def test_download_permission_allowed(test_setup):
    alice_headers = test_setup["alice_headers"]
    bob_headers = test_setup["bob_headers"]

    # Load and encrypt
    load_resp = client.post(
        "/api/v1/images/samples/load/synthetic_brain_mri.png",
        headers=alice_headers
    )
    image_id = load_resp.json()["image_id"]
    client.post(
        f"/api/v1/crypto/hybrid/encrypt/{image_id}",
        data={"master_key": "HICE_CLINICAL_MASTER_KEY_2026"},
        headers=alice_headers
    )

    # Share with DOWNLOAD permission
    share_resp = client.post(
        "/api/v1/shares/create",
        data={
            "image_id": image_id,
            "receiver_username": "dr_bob_oncology",
            "permission_type": "DOWNLOAD",
            "expiry_hours": 24,
            "master_key": "HICE_CLINICAL_MASTER_KEY_2026"
        },
        headers=alice_headers
    )
    share_id = share_resp.json()["share_id"]

    # Bob downloads decrypted file
    down_resp = client.get(f"/api/v1/shares/{share_id}/download", headers=bob_headers)
    assert down_resp.status_code == 200
    assert down_resp.headers["content-type"] == "image/png"
    assert len(down_resp.content) > 100

def test_instant_revocation_enforcement(test_setup):
    alice_headers = test_setup["alice_headers"]
    bob_headers = test_setup["bob_headers"]

    load_resp = client.post(
        "/api/v1/images/samples/load/sample_histology.bmp",
        headers=alice_headers
    )
    image_id = load_resp.json()["image_id"]
    client.post(
        f"/api/v1/crypto/hybrid/encrypt/{image_id}",
        data={"master_key": "HICE_CLINICAL_MASTER_KEY_2026"},
        headers=alice_headers
    )

    share_resp = client.post(
        "/api/v1/shares/create",
        data={
            "image_id": image_id,
            "receiver_username": "dr_bob_oncology",
            "permission_type": "VIEW",
            "expiry_hours": 12,
            "master_key": "HICE_CLINICAL_MASTER_KEY_2026"
        },
        headers=alice_headers
    )
    share_id = share_resp.json()["share_id"]

    # Alice revokes the share
    revoke_resp = client.delete(f"/api/v1/shares/{share_id}/revoke", headers=alice_headers)
    assert revoke_resp.status_code == 200
    assert revoke_resp.json()["status"] == "SUCCESS"

    # Bob's access is now rejected
    access_resp = client.post(f"/api/v1/shares/{share_id}/access", headers=bob_headers)
    assert access_resp.status_code == 403
    assert "ACCESS REVOKED" in access_resp.json()["detail"]

def test_expired_share_rejection(test_setup):
    db = test_setup["db"]
    alice_headers = test_setup["alice_headers"]
    bob_headers = test_setup["bob_headers"]

    load_resp = client.post(
        "/api/v1/images/samples/load/synthetic_chest_xray.png",
        headers=alice_headers
    )
    image_id = load_resp.json()["image_id"]
    client.post(
        f"/api/v1/crypto/hybrid/encrypt/{image_id}",
        data={"master_key": "HICE_CLINICAL_MASTER_KEY_2026"},
        headers=alice_headers
    )

    share_resp = client.post(
        "/api/v1/shares/create",
        data={
            "image_id": image_id,
            "receiver_username": "dr_bob_oncology",
            "permission_type": "VIEW",
            "expiry_hours": 1,
            "master_key": "HICE_CLINICAL_MASTER_KEY_2026"
        },
        headers=alice_headers
    )
    share_id = share_resp.json()["share_id"]

    # Manually expire the share in database
    share = db.query(ImageShare).filter(ImageShare.share_id == share_id).first()
    share.expires_at = datetime.now(timezone.utc) - timedelta(hours=2)
    db.commit()

    # Bob tries to access expired share
    access_resp = client.post(f"/api/v1/shares/{share_id}/access", headers=bob_headers)
    assert access_resp.status_code == 403
    assert "ACCESS EXPIRED" in access_resp.json()["detail"]
