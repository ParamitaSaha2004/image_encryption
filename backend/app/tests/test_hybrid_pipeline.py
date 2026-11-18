"""
Phase 7 Automated Verification Suite: Complete Hybrid Encryption and Decryption Pipeline
Tests end-to-end forward encryption, reverse decryption, lossless reconstruction,
cryptographic SHA-256 integrity, tamper detection, wrong-key rejection, and REST API routes.
"""
import pytest
import os
import io
import json
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.encryption.hybrid_pipeline import HybridEncryptionPipeline, HybridPipelineError
from app.decryption.hybrid_decryption import HybridDecryptionPipeline, CryptographicIntegrityError
from app.encryption.aes_gcm import TamperingDetectedError
from app.image_processing.preprocessor import ImagePreprocessor
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

def test_key_normalization():
    # String passphrase
    k1 = HybridEncryptionPipeline.normalize_master_key("clinical_secure_passphrase_2026")
    assert len(k1) == 32

    # 64-char hex string
    hex_str = "a" * 64
    k2 = HybridEncryptionPipeline.normalize_master_key(hex_str)
    assert len(k2) == 32
    assert k2 == bytes.fromhex(hex_str)

    # 32-byte raw bytes
    raw_32 = os.urandom(32)
    k3 = HybridEncryptionPipeline.normalize_master_key(raw_32)
    assert k3 == raw_32

def test_hice_package_serialization_deserialization():
    nonce = os.urandom(12)
    auth_tag = os.urandom(16)
    aad_dict = {"image_id": "TEST-123", "width": 256, "height": 256, "channels": 3}
    aad_bytes = json.dumps(aad_dict, sort_keys=True).encode("utf-8")
    ciphertext = os.urandom(1024)

    package_bytes = HybridEncryptionPipeline.serialize_hice_package(
        nonce, auth_tag, aad_bytes, ciphertext
    )
    assert len(package_bytes) == 12 + 16 + 4 + len(aad_bytes) + len(ciphertext)

    unpacked = HybridDecryptionPipeline.deserialize_hice_package(package_bytes)
    assert unpacked["nonce"] == nonce
    assert unpacked["auth_tag"] == auth_tag
    assert unpacked["aad_bytes"] == aad_bytes
    assert unpacked["aad_payload"]["image_id"] == "TEST-123"
    assert unpacked["ciphertext"] == ciphertext

def test_end_to_end_forward_and_reverse_pipeline_lossless():
    # Generate synthetic 64x64 RGB test image
    img_data = np.random.randint(0, 256, size=(64, 64, 3), dtype=np.uint8)
    flat_vector = img_data.flatten()
    import hashlib
    original_sha256 = hashlib.sha256(flat_vector.tobytes()).hexdigest()

    metadata = {
        "image_id": "TEST-SCAN-E2E",
        "title": "Synthetic Test Scan",
        "width": 64,
        "height": 64,
        "channels": 3,
        "original_sha256": original_sha256,
        "format": "PNG"
    }
    master_key = "RESEARCH_HICE_SECRET_KEY_98765"

    # Forward Encryption
    enc_res = HybridEncryptionPipeline.encrypt_vector(
        vector=flat_vector,
        metadata=metadata,
        master_key=master_key,
        ca_rule=30
    )
    assert enc_res["status"] == "SUCCESS"
    assert len(enc_res["package_bytes"]) > 0
    assert enc_res["performance"]["total_encryption_ms"] > 0

    # Reverse Decryption
    dec_res = HybridDecryptionPipeline.decrypt_package(
        package_bytes=enc_res["package_bytes"],
        master_key=master_key,
        verify_bit_exact=True
    )
    assert dec_res["status"] == "SUCCESS"
    assert dec_res["is_bit_exact"] is True
    assert dec_res["reconstructed_sha256"] == original_sha256
    assert dec_res["dimensions"]["width"] == 64
    assert dec_res["dimensions"]["height"] == 64
    assert dec_res["dimensions"]["channels"] == 3
    assert dec_res["data_uri"].startswith("data:image/png;base64,")

    # Verify bit-level raster reconstruction
    with Image.open(io.BytesIO(dec_res["image_bytes"])) as reconstructed_img:
        recon_array = np.array(reconstructed_img, dtype=np.uint8)
        assert np.array_equal(img_data, recon_array)

def test_rule_90_forward_and_reverse_pipeline():
    # Test with Rule 90 additive fractal lattice
    img_data = np.random.randint(0, 256, size=(32, 32, 1), dtype=np.uint8)
    flat_vector = img_data.flatten()
    import hashlib
    original_sha256 = hashlib.sha256(flat_vector.tobytes()).hexdigest()

    metadata = {
        "image_id": "TEST-RULE90",
        "title": "Rule 90 Scan",
        "width": 32,
        "height": 32,
        "channels": 1,
        "original_sha256": original_sha256,
        "format": "PNG"
    }
    master_key = "RULE90_SECRET_KEY"

    enc_res = HybridEncryptionPipeline.encrypt_vector(
        vector=flat_vector,
        metadata=metadata,
        master_key=master_key,
        ca_rule=90
    )
    dec_res = HybridDecryptionPipeline.decrypt_package(
        package_bytes=enc_res["package_bytes"],
        master_key=master_key,
        verify_bit_exact=True
    )
    assert dec_res["is_bit_exact"] is True
    assert dec_res["reconstructed_sha256"] == original_sha256

def test_wrong_key_rejection():
    img_data = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8).flatten()
    import hashlib
    original_sha256 = hashlib.sha256(img_data.tobytes()).hexdigest()

    metadata = {"width": 32, "height": 32, "channels": 3, "original_sha256": original_sha256}
    enc_res = HybridEncryptionPipeline.encrypt_vector(img_data, metadata, "CORRECT_KEY", ca_rule=30)

    # Attempt decryption with wrong key
    with pytest.raises(TamperingDetectedError):
        HybridDecryptionPipeline.decrypt_package(enc_res["package_bytes"], "WRONG_KEY")

def test_tampered_ciphertext_rejection():
    img_data = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8).flatten()
    import hashlib
    original_sha256 = hashlib.sha256(img_data.tobytes()).hexdigest()

    metadata = {"width": 32, "height": 32, "channels": 3, "original_sha256": original_sha256}
    enc_res = HybridEncryptionPipeline.encrypt_vector(img_data, metadata, "TAMPER_KEY", ca_rule=30)
    package = bytearray(enc_res["package_bytes"])

    # Tamper with the last byte in ciphertext
    package[-1] ^= 0x01

    with pytest.raises(TamperingDetectedError):
        HybridDecryptionPipeline.decrypt_package(bytes(package), "TAMPER_KEY")

def test_tampered_aad_metadata_rejection():
    img_data = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8).flatten()
    import hashlib
    original_sha256 = hashlib.sha256(img_data.tobytes()).hexdigest()

    metadata = {"width": 32, "height": 32, "channels": 3, "original_sha256": original_sha256}
    enc_res = HybridEncryptionPipeline.encrypt_vector(img_data, metadata, "AAD_TAMPER_KEY", ca_rule=30)
    package = bytearray(enc_res["package_bytes"])

    # Tamper with a byte inside the AAD metadata segment (offset 35)
    package[35] ^= 0x01

    with pytest.raises(TamperingDetectedError):
        HybridDecryptionPipeline.decrypt_package(bytes(package), "AAD_TAMPER_KEY")

def test_tampered_auth_tag_rejection():
    img_data = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8).flatten()
    import hashlib
    original_sha256 = hashlib.sha256(img_data.tobytes()).hexdigest()

    metadata = {"width": 32, "height": 32, "channels": 3, "original_sha256": original_sha256}
    enc_res = HybridEncryptionPipeline.encrypt_vector(img_data, metadata, "TAG_TAMPER_KEY", ca_rule=30)
    package = bytearray(enc_res["package_bytes"])

    # Auth tag is located at offset 12:28
    package[15] ^= 0xFF

    with pytest.raises(TamperingDetectedError):
        HybridDecryptionPipeline.decrypt_package(bytes(package), "TAG_TAMPER_KEY")

def test_corrupted_truncated_package_rejection():
    with pytest.raises(HybridPipelineError):
        HybridDecryptionPipeline.decrypt_package(b"TOO_SHORT", "KEY")

def test_api_hybrid_encrypt_and_decrypt_endpoints(auth_headers):
    # 1. Ingest synthetic PA Chest X-Ray
    load_resp = client.post(
        "/api/v1/images/samples/load/synthetic_chest_xray.png",
        headers=auth_headers
    )
    assert load_resp.status_code == 200
    img_data = load_resp.json()
    image_id = img_data["image_id"]
    original_sha256 = img_data["original_sha256"]

    # 2. Call Hybrid Encrypt API
    encrypt_resp = client.post(
        f"/api/v1/crypto/hybrid/encrypt/{image_id}?master_key=HICE_CLINICAL_DEMO_KEY&ca_rule=30",
        headers=auth_headers
    )
    assert encrypt_resp.status_code == 200
    enc_json = encrypt_resp.json()
    assert enc_json["status"] == "SUCCESS"
    assert "package_size_bytes" in enc_json
    assert enc_json["vault_package_file"] == f"{image_id}.hice"

    # 3. Call Hybrid Decrypt API
    decrypt_resp = client.post(
        f"/api/v1/crypto/hybrid/decrypt/{image_id}?master_key=HICE_CLINICAL_DEMO_KEY",
        headers=auth_headers
    )
    assert decrypt_resp.status_code == 200
    dec_json = decrypt_resp.json()
    assert dec_json["status"] == "SUCCESS"
    assert dec_json["is_bit_exact"] is True
    assert dec_json["original_sha256"] == original_sha256
    assert dec_json["reconstructed_sha256"] == original_sha256
    assert "data_uri" in dec_json
    assert dec_json["data_uri"].startswith("data:image/png;base64,")

    # 4. Download raw .hice package
    download_resp = client.get(
        f"/api/v1/crypto/hybrid/package/{image_id}",
        headers=auth_headers
    )
    assert download_resp.status_code == 200
    assert len(download_resp.content) == enc_json["package_size_bytes"]

def test_api_direct_decrypt_file_endpoint(auth_headers):
    # Generate encrypted package
    img_data = np.random.randint(0, 256, size=(32, 32, 3), dtype=np.uint8).flatten()
    import hashlib
    original_sha256 = hashlib.sha256(img_data.tobytes()).hexdigest()

    metadata = {"width": 32, "height": 32, "channels": 3, "original_sha256": original_sha256}
    enc_res = HybridEncryptionPipeline.encrypt_vector(img_data, metadata, "DIRECT_TEST_KEY", ca_rule=30)

    # Post file directly to direct-decrypt-file endpoint
    files = {"file": ("test.hice", enc_res["package_bytes"], "application/octet-stream")}
    data = {"master_key": "DIRECT_TEST_KEY"}
    response = client.post("/api/v1/crypto/hybrid/direct-decrypt-file", files=files, data=data, headers=auth_headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["is_bit_exact"] is True
    assert res_data["original_sha256"] == original_sha256
