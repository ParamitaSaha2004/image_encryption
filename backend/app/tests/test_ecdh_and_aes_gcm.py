"""
Phase 6 Automated Verification Suite: ECDH Key Agreement & AES-256-GCM AEAD
Tests NIST P-256 key generation, ECDH mathematical symmetry, HKDF subkey separation,
AES-256-GCM authenticated encryption, nonce uniqueness, and tampering rejection.
"""
import pytest
import os
from fastapi.testclient import TestClient

from app.main import app
from app.key_management.ecdh_manager import ECDHManager, ECDHError
from app.key_management.hkdf_util import HKDFUtil
from app.encryption.aes_gcm import AES256GCMEngine, TamperingDetectedError, AESGCMError
from app.decryption.aes_gcm_decrypt import AESGCMDecryptor

client = TestClient(app)

def test_p256_keypair_generation_and_loading():
    pub_pem, priv_pem = ECDHManager.generate_keypair()
    assert "BEGIN PUBLIC KEY" in pub_pem
    assert "BEGIN PRIVATE KEY" in priv_pem

    priv_key = ECDHManager.load_private_key(priv_pem)
    pub_key = ECDHManager.load_public_key(pub_pem)
    assert priv_key is not None
    assert pub_key is not None

def test_ecdh_shared_secret_symmetry():
    # Alice keypair
    alice_pub_pem, alice_priv_pem = ECDHManager.generate_keypair()
    alice_priv = ECDHManager.load_private_key(alice_priv_pem)
    alice_pub = ECDHManager.load_public_key(alice_pub_pem)

    # Bob keypair
    bob_pub_pem, bob_priv_pem = ECDHManager.generate_keypair()
    bob_priv = ECDHManager.load_private_key(bob_priv_pem)
    bob_pub = ECDHManager.load_public_key(bob_pub_pem)

    # Compute shared secret
    z_alice = ECDHManager.compute_shared_secret(alice_priv, bob_pub)
    z_bob = ECDHManager.compute_shared_secret(bob_priv, alice_pub)

    assert len(z_alice) == 32
    assert z_alice == z_bob

    # Convenience method
    z_direct = ECDHManager.exchange_from_pems(alice_priv_pem, bob_pub_pem)
    assert z_direct == z_alice

def test_hkdf_subkey_separation():
    shared_secret = os.urandom(32)
    keys = HKDFUtil.derive_session_keys(shared_secret)

    assert "aes_key" in keys
    assert "chaos_seed" in keys
    assert "ca_seed" in keys
    assert "wrap_key" in keys

    # Verify all derived keys are 32 bytes (256 bits)
    for k_name, k_bytes in keys.items():
        assert len(k_bytes) == 32

    # Verify cryptographic separation: no two derived keys are identical
    subkeys = list(keys.values())
    for i in range(len(subkeys)):
        for j in range(i + 1, len(subkeys)):
            assert subkeys[i] != subkeys[j]

def test_aes_256_gcm_encryption_and_decryption():
    key = AES256GCMEngine.generate_key()
    plaintext = b"CONFIDENTIAL_MRI_DIAGNOSIS_DATA_SAMPLE" * 50
    metadata = {"patient_id": "PT-9988", "modality": "MRI", "dimensions": [512, 512, 1]}
    aad = AES256GCMEngine.format_aad(metadata)

    ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(key, plaintext, aad=aad)

    assert len(nonce) == 12
    assert len(auth_tag) == 16
    assert len(ciphertext) == len(plaintext)
    assert ciphertext != plaintext

    # Decrypt via engine
    decrypted = AES256GCMEngine.decrypt(key, ciphertext, nonce, auth_tag, aad=aad)
    assert decrypted == plaintext

    # Decrypt via Decryptor module
    decrypted_mod = AESGCMDecryptor.decrypt_and_verify(key, ciphertext, nonce, auth_tag, aad=aad)
    assert decrypted_mod == plaintext

def test_nonce_freshness_uniqueness():
    # Verify that consecutive nonces are never duplicated (prevents GCM nonce reuse catastrophe)
    nonces = {AES256GCMEngine.generate_nonce() for _ in range(1000)}
    assert len(nonces) == 1000

def test_tampering_rejection_ciphertext_bit_flip():
    key = AES256GCMEngine.generate_key()
    plaintext = b"CRITICAL_HEALTHCARE_SCAN_RECORD"
    aad = b"AUTHENTICATED_METADATA_HEADER"

    ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(key, plaintext, aad=aad)

    # Modify single bit in ciphertext
    tampered = bytearray(ciphertext)
    tampered[0] ^= 0x01

    with pytest.raises(TamperingDetectedError) as exc_info:
        AES256GCMEngine.decrypt(key, bytes(tampered), nonce, auth_tag, aad=aad)
    assert "INTEGRITY FAILURE" in str(exc_info.value)

def test_tampering_rejection_metadata_aad_modification():
    key = AES256GCMEngine.generate_key()
    plaintext = b"CONFIDENTIAL_RECORD"
    aad_legit = b"PATIENT_ID_4500"
    aad_tampered = b"PATIENT_ID_4501"  # Modifying 1 digit in metadata

    ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(key, plaintext, aad=aad_legit)

    with pytest.raises(TamperingDetectedError):
        AES256GCMEngine.decrypt(key, ciphertext, nonce, auth_tag, aad=aad_tampered)

def test_tampering_rejection_auth_tag_modification():
    key = AES256GCMEngine.generate_key()
    plaintext = b"CONFIDENTIAL_RECORD"
    ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(key, plaintext)

    tampered_tag = bytearray(auth_tag)
    tampered_tag[0] ^= 0x01

    with pytest.raises(TamperingDetectedError):
        AES256GCMEngine.decrypt(key, ciphertext, nonce, bytes(tampered_tag))

def test_wrong_key_rejection():
    key1 = AES256GCMEngine.generate_key()
    key2 = AES256GCMEngine.generate_key()
    plaintext = b"SAMPLE_PAYLOAD"

    ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(key1, plaintext)

    with pytest.raises(TamperingDetectedError):
        AES256GCMEngine.decrypt(key2, ciphertext, nonce, auth_tag)

def test_api_ecdh_key_agreement_endpoint():
    response = client.post("/api/v1/crypto/ecdh/test-key-agreement")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["shared_secret_symmetric"] is True
    assert data["derived_aes_keys_match"] is True

def test_api_aes_tamper_simulation_endpoint():
    response = client.post("/api/v1/crypto/aes/test-tamper-simulation")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["legitimate_decryption_verified"] is True
    assert data["tampering_detected_by_gcm"] is True
    assert data["plaintext_leaked"] is False
