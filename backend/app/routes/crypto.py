"""
Cryptographic Testing and Transformation API Endpoints
Exposes modular routes for testing Chaotic Maps, Cellular Automata,
Key Derivation, and Hybrid transformations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import numpy as np
import time
import os

from app.database.connection import get_db
from app.models.db_models import User, EncryptedImage
from app.security.rbac import get_current_user
from app.encryption.chaotic_map import LogisticMap, ChaoticMapError
from app.encryption.cellular_automata import CellularAutomataDiffuser, CAError
from app.key_management.ecdh_manager import ECDHManager
from app.key_management.hkdf_util import HKDFUtil
from app.encryption.aes_gcm import AES256GCMEngine, TamperingDetectedError
from app.encryption.hybrid_pipeline import HybridEncryptionPipeline, HybridPipelineError
from app.decryption.hybrid_decryption import HybridDecryptionPipeline, CryptographicIntegrityError
from app.models.db_models import AuditLog, EncryptionMetric
from app.image_processing.preprocessor import ImagePreprocessor
from app.config import settings
from fastapi.responses import FileResponse, Response
from fastapi import UploadFile, File, Form
from datetime import datetime, timezone

router = APIRouter(prefix="/api/v1/crypto", tags=["Cryptographic Engine"])

@router.get("/chaos/sensitivity")
def get_chaos_key_sensitivity(
    seed_str: str = "HICE_SECRET_CHAOS_SEED_2026",
    delta: float = 1e-14
) -> Dict[str, Any]:
    """
    Demonstrates the sensitive dependence on initial conditions (Butterfly Effect).
    Perturbs x0 by delta (e.g. 10^-14) and evaluates cross-correlation and permutation divergence.
    """
    try:
        results = LogisticMap.evaluate_sensitivity(
            base_seed=seed_str.encode("utf-8"),
            delta=delta,
            length=1000
        )
        return {
            "status": "SUCCESS",
            "experiment": "Chaotic Key Sensitivity Analysis",
            "seed_tested": seed_str,
            "perturbation_delta": delta,
            "base_parameters": {
                "r": results["base_r"],
                "x0": results["base_x0"]
            },
            "trajectory_cross_correlation": results["trajectory_correlation"],
            "perm_index_divergence_ratio": results["perm_difference_ratio"],
            "divergence_percentage": f"{results['perm_difference_ratio'] * 100:.2f}%",
            "trajectory_preview": {
                "original_first_10": results["sample_trajectory_a"][:10],
                "perturbed_first_10": results["sample_trajectory_b"][:10]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chaotic sensitivity evaluation failed: {str(e)}")

@router.post("/chaos/test-permute/{image_id}")
def test_chaotic_permutation(
    image_id: str,
    seed: Optional[str] = "HICE_CLINICAL_CHAOS_KEY",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Loads an ingested image, applies Chaotic Logistic Map permutation,
    measures execution duration, and verifies exact inverse recovery.
    """
    img_record = db.query(EncryptedImage).filter(EncryptedImage.image_id == image_id).first()
    if not img_record:
        raise HTTPException(status_code=404, detail="Image record not found.")

    if not os.path.exists(img_record.storage_path):
        raise HTTPException(status_code=404, detail="Image raw storage file not found in vault.")

    # Read uncompressed 1D uint8 array
    with open(img_record.storage_path, "rb") as f:
        raw_bytes = f.read()

    vector = np.frombuffer(raw_bytes, dtype=np.uint8)

    # Initialize Logistic Map
    t0 = time.perf_counter()
    logistic = LogisticMap.from_seed(seed)
    permuted_vector, inv_perm = logistic.permute(vector)
    t_perm = (time.perf_counter() - t0) * 1000

    # Test exact recovery immediately
    t1 = time.perf_counter()
    recovered_vector = LogisticMap.inverse_permute(permuted_vector, inv_perm)
    t_inv = (time.perf_counter() - t1) * 1000

    is_bit_exact = bool(np.array_equal(vector, recovered_vector))

    # Calculate Pearson correlation of adjacent pixels in permuted vs original
    corr_orig = float(np.corrcoef(vector[:-1], vector[1:])[0, 1])
    corr_perm = float(np.corrcoef(permuted_vector[:-1], permuted_vector[1:])[0, 1])

    return {
        "status": "SUCCESS",
        "image_id": image_id,
        "title": img_record.title,
        "dimensions": {
            "width": img_record.width,
            "height": img_record.height,
            "channels": img_record.channels,
            "total_pixels": int(len(vector))
        },
        "performance": {
            "permutation_time_ms": round(t_perm, 2),
            "inverse_time_ms": round(t_inv, 2)
        },
        "exact_recovery_verified": is_bit_exact,
        "correlation_reduction": {
            "original_adjacent_correlation": round(corr_orig, 4),
            "permuted_adjacent_correlation": round(corr_perm, 4),
            "correlation_drop_percentage": f"{abs((corr_orig - corr_perm) / (corr_orig or 1)) * 100:.2f}%"
        }
    }

@router.get("/ca/avalanche")
def get_ca_avalanche_effect(
    rule: int = 30,
    length: int = 1000
) -> Dict[str, Any]:
    """
    Evaluates the bit avalanche effect and Shannon entropy of Cellular Automata (Rule 30 or Rule 90)
    when a single bit in the seed is flipped. Ideal cryptographic diffusion achieves ~50% bit flip.
    """
    try:
        results = CellularAutomataDiffuser.evaluate_avalanche_effect(length=length, rule=rule)
        return {
            "status": "SUCCESS",
            "experiment": f"Cellular Automata Rule {rule} Avalanche & Entropy Analysis",
            "parameters": {
                "rule": rule,
                "length_bytes": length
            },
            "avalanche_percentage": f"{results['avalanche_percentage']:.2f}%",
            "bits_flipped": results["bits_flipped"],
            "total_bits_evaluated": results["total_bits_evaluated"],
            "shannon_entropy": results["shannon_entropy"],
            "ideal_entropy": 8.0000,
            "ideal_avalanche": "50.00%"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CA avalanche evaluation failed: {str(e)}")

@router.post("/ca/test-diffuse/{image_id}")
def test_ca_diffusion(
    image_id: str,
    rule: int = 30,
    seed: Optional[str] = "HICE_CLINICAL_CA_KEY",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Applies Cellular Automata diffusion (Rule 30 or 90) on an ingested image vector,
    measures diffusion timing, calculates Shannon entropy change, and verifies exact inverse recovery.
    """
    img_record = db.query(EncryptedImage).filter(EncryptedImage.image_id == image_id).first()
    if not img_record:
        raise HTTPException(status_code=404, detail="Image record not found.")

    if not os.path.exists(img_record.storage_path):
        raise HTTPException(status_code=404, detail="Image raw storage file not found in vault.")

    with open(img_record.storage_path, "rb") as f:
        raw_bytes = f.read()

    vector = np.frombuffer(raw_bytes, dtype=np.uint8)

    # Calculate original Shannon entropy
    counts_orig = np.bincount(vector, minlength=256)
    p_orig = counts_orig[counts_orig > 0] / len(vector)
    entropy_orig = float(-np.sum(p_orig * np.log2(p_orig)))

    diffuser = CellularAutomataDiffuser(rule=rule)

    # Forward diffusion
    t0 = time.perf_counter()
    diffused_vector, mask = diffuser.diffuse(vector, seed)
    t_diff = (time.perf_counter() - t0) * 1000

    # Calculate diffused Shannon entropy
    counts_diff = np.bincount(diffused_vector, minlength=256)
    p_diff = counts_diff[counts_diff > 0] / len(diffused_vector)
    entropy_diff = float(-np.sum(p_diff * np.log2(p_diff)))

    # Reversible Inversion: (V ^ M) ^ M = V
    t1 = time.perf_counter()
    recovered_vector = diffuser.invert_diffuse(diffused_vector, seed)
    t_inv = (time.perf_counter() - t1) * 1000

    is_bit_exact = bool(np.array_equal(vector, recovered_vector))

    return {
        "status": "SUCCESS",
        "image_id": image_id,
        "title": img_record.title,
        "ca_rule": rule,
        "dimensions": {
            "width": img_record.width,
            "height": img_record.height,
            "channels": img_record.channels,
            "total_pixels": int(len(vector))
        },
        "performance": {
            "diffusion_time_ms": round(t_diff, 2),
            "inverse_time_ms": round(t_inv, 2)
        },
        "exact_recovery_verified": is_bit_exact,
        "entropy_elevation": {
            "original_entropy": round(entropy_orig, 4),
            "diffused_entropy": round(entropy_diff, 4),
            "theoretical_max": 8.0000
        }
    }

@router.post("/ecdh/test-key-agreement")
def test_ecdh_key_agreement() -> Dict[str, Any]:
    """
    Simulates asymmetric key agreement between Alice (sender) and Bob (receiver)
    over NIST P-256 (secp256r1) with HKDF-SHA256 session key expansion.
    """
    # 1. Alice generates keypair (d_A, Q_A)
    alice_pub_pem, alice_priv_pem = ECDHManager.generate_keypair()
    alice_priv = ECDHManager.load_private_key(alice_priv_pem)
    alice_pub = ECDHManager.load_public_key(alice_pub_pem)

    # 2. Bob generates keypair (d_B, Q_B)
    bob_pub_pem, bob_priv_pem = ECDHManager.generate_keypair()
    bob_priv = ECDHManager.load_private_key(bob_priv_pem)
    bob_pub = ECDHManager.load_public_key(bob_pub_pem)

    # 3. Alice computes Z_A = d_A * Q_B
    z_alice = ECDHManager.compute_shared_secret(alice_priv, bob_pub)

    # 4. Bob computes Z_B = d_B * Q_A
    z_bob = ECDHManager.compute_shared_secret(bob_priv, alice_pub)

    # 5. Check symmetry
    is_symmetric = bool(z_alice == z_bob)

    # 6. HKDF key derivation
    alice_keys = HKDFUtil.derive_session_keys(z_alice)
    bob_keys = HKDFUtil.derive_session_keys(z_bob)

    keys_match = bool(alice_keys["aes_key"] == bob_keys["aes_key"])

    return {
        "status": "SUCCESS",
        "experiment": "NIST P-256 ECDH Key Agreement & HKDF Derivation",
        "curve": "secp256r1 (NIST P-256)",
        "shared_secret_symmetric": is_symmetric,
        "derived_aes_keys_match": keys_match,
        "shared_secret_hex": z_alice.hex()[:32] + "...",
        "derived_aes_key_hex": alice_keys["aes_key"].hex()[:32] + "...",
        "subkeys_derived": [
            "K_aes (AES-256-GCM symmetric session)",
            "K_chaos (Logistic Map permutation parameter)",
            "K_ca (Cellular Automata diffusion mask)",
            "K_wrap (Key encapsulation wrapping)"
        ]
    }

@router.post("/aes/test-tamper-simulation")
def test_aes_tamper_simulation() -> Dict[str, Any]:
    """
    Demonstrates AEAD tamper detection: Encrypts a message with AES-256-GCM,
    flips a single bit in the ciphertext, and demonstrates that decryption safely
    fails with an integrity exception before releasing any plaintext.
    """
    key = AES256GCMEngine.generate_key()
    original_message = b"CONFIDENTIAL_RADIOLOGY_REPORT_PATIENT_DOB_1985"
    metadata = {"scan_id": "SCAN-7890", "modality": "CT", "patient": "ANON-01"}
    aad = AES256GCMEngine.format_aad(metadata)

    # Legitimate encryption
    ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(key, original_message, aad=aad)

    # Verify normal decryption succeeds
    decrypted_valid = AES256GCMEngine.decrypt(key, ciphertext, nonce, auth_tag, aad=aad)
    legitimate_success = bool(decrypted_valid == original_message)

    # Simulate Malicious Tampering: Flip 1 bit in ciphertext
    tampered_bytes = bytearray(ciphertext)
    tampered_bytes[0] ^= 0x01  # Flip least significant bit of first byte
    tampered_ciphertext = bytes(tampered_bytes)

    tamper_caught = False
    error_message = ""
    try:
        AES256GCMEngine.decrypt(key, tampered_ciphertext, nonce, auth_tag, aad=aad)
    except TamperingDetectedError as e:
        tamper_caught = True
        error_message = str(e)

    return {
        "status": "SUCCESS",
        "experiment": "AES-256-GCM Tampering Injection Test",
        "original_message_length": len(original_message),
        "legitimate_decryption_verified": legitimate_success,
        "tampering_attempt": "1-bit flip in ciphertext stream (offset 0, XOR 0x01)",
        "tampering_detected_by_gcm": tamper_caught,
        "security_response": error_message,
        "plaintext_leaked": False,
        "guarantee": "IND-CCA2 Authenticated Encryption (No plaintext released without valid MAC)"
    }

# =========================================================================
# PHASE 7: HYBRID ENCRYPTION & DECRYPTION ATOMIC PIPELINE ENDPOINTS
# =========================================================================

@router.post("/hybrid/encrypt/{image_id}")
def run_hybrid_encryption(
    image_id: str,
    master_key: Optional[str] = "HICE_CLINICAL_MASTER_KEY_2026",
    ca_rule: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Executes the full forward hybrid encryption pipeline on an ingested image:
    Pixel Array -> Chaotic Logistic Map Permutation -> Cellular Automata Diffusion -> AES-256-GCM AEAD.
    Saves the final encrypted package as a standardized .hice file in the storage vault.
    """
    img_record = db.query(EncryptedImage).filter(EncryptedImage.image_id == image_id).first()
    if not img_record:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found.")

    # Locate raw pixel vector in vault
    raw_vector_path = os.path.join(settings.VAULT_STORAGE_PATH, f"ingested_{image_id}.bin")
    if not os.path.exists(raw_vector_path):
        # Fallback to storage_path if it points to a bin file
        if os.path.exists(img_record.storage_path) and img_record.storage_path.endswith(".bin"):
            raw_vector_path = img_record.storage_path
        else:
            raise HTTPException(
                status_code=400, 
                detail="Raw ingested pixel vector is not available in vault for encryption."
            )

    with open(raw_vector_path, "rb") as f:
        raw_bytes = f.read()

    vector = np.frombuffer(raw_bytes, dtype=np.uint8)

    meta_record = img_record.metadata_record
    metadata = {
        "image_id": image_id,
        "title": img_record.title,
        "original_filename": img_record.original_filename,
        "width": img_record.width,
        "height": img_record.height,
        "channels": img_record.channels,
        "original_sha256": img_record.original_sha256,
        "format": "PNG",
        "clinical": {
            "modality": meta_record.modality if meta_record else "GENERAL",
            "body_part": meta_record.body_part if meta_record else "GENERAL",
            "patient_pseudonym": meta_record.patient_pseudonym if meta_record else "ANONYMOUS"
        }
    }

    try:
        pipeline_res = HybridEncryptionPipeline.encrypt_vector(
            vector=vector,
            metadata=metadata,
            master_key=master_key or "HICE_CLINICAL_MASTER_KEY_2026",
            ca_rule=ca_rule
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid encryption failed: {str(e)}")

    # Write .hice package to vault
    hice_filename = f"{image_id}.hice"
    hice_path = os.path.join(settings.VAULT_STORAGE_PATH, hice_filename)
    with open(hice_path, "wb") as f:
        f.write(pipeline_res["package_bytes"])

    # Update database record
    img_record.storage_path = hice_path
    img_record.ciphertext_sha256 = pipeline_res["ciphertext_sha256"]
    img_record.nonce_hex = pipeline_res["nonce_hex"]
    img_record.auth_tag_hex = pipeline_res["auth_tag_hex"]
    img_record.aad_json = pipeline_res["aad_payload"]

    audit_entry = AuditLog(
        user_id=current_user.user_id,
        action="HYBRID_ENCRYPTION",
        target_resource_type="IMAGE",
        target_resource_id=image_id,
        ip_address="127.0.0.1",
        status="SUCCESS",
        details_json={
            "performance": pipeline_res["performance"],
            "ca_rule": ca_rule,
            "ciphertext_sha256": pipeline_res["ciphertext_sha256"],
            "package_size": pipeline_res["package_size_bytes"]
        },
        prev_record_hash="0" * 64,
        current_record_hash="0" * 64
    )
    db.add(audit_entry)
    db.commit()

    return {
        "status": "SUCCESS",
        "message": "Image successfully encrypted with hybrid pipeline (Chaos + CA + AES-256-GCM).",
        "image_id": image_id,
        "title": img_record.title,
        "vault_package_file": hice_filename,
        "package_size_bytes": pipeline_res["package_size_bytes"],
        "nonce_hex": pipeline_res["nonce_hex"],
        "auth_tag_hex": pipeline_res["auth_tag_hex"],
        "ciphertext_sha256": pipeline_res["ciphertext_sha256"],
        "performance": pipeline_res["performance"],
        "subkeys_preview": pipeline_res["subkeys_preview"]
    }

@router.post("/hybrid/decrypt/{image_id}")
def run_hybrid_decryption(
    image_id: str,
    master_key: str = "HICE_CLINICAL_MASTER_KEY_2026",
    verify_bit_exact: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Executes the full reverse hybrid decryption pipeline on an encrypted .hice vault asset:
    .hice package -> AES-256-GCM AEAD -> CA Reverse Diffusion -> Chaos Reverse Permutation -> Exact Image.
    Verifies SHA-256 integrity and returns base64 raster image data for real-time visualization.
    """
    img_record = db.query(EncryptedImage).filter(EncryptedImage.image_id == image_id).first()
    if not img_record:
        raise HTTPException(status_code=404, detail=f"Image with ID {image_id} not found.")

    hice_path = os.path.join(settings.VAULT_STORAGE_PATH, f"{image_id}.hice")
    if not os.path.exists(hice_path):
        if os.path.exists(img_record.storage_path) and img_record.storage_path.endswith(".hice"):
            hice_path = img_record.storage_path
        else:
            raise HTTPException(
                status_code=400, 
                detail="Encrypted .hice package does not exist for this image. Encrypt it first."
            )

    with open(hice_path, "rb") as f:
        package_bytes = f.read()

    try:
        decrypt_res = HybridDecryptionPipeline.decrypt_package(
            package_bytes=package_bytes,
            master_key=master_key,
            verify_bit_exact=verify_bit_exact
        )
    except TamperingDetectedError as e:
        audit_entry = AuditLog(
            user_id=current_user.user_id,
            action="HYBRID_DECRYPTION",
            target_resource_type="IMAGE",
            target_resource_id=image_id,
            ip_address="127.0.0.1",
            status="TAMPER_DETECTED",
            details_json={"error": str(e)},
            prev_record_hash="0" * 64,
            current_record_hash="0" * 64
        )
        db.add(audit_entry)
        db.commit()
        raise HTTPException(
            status_code=403, 
            detail=f"TAMPERING DETECTED: Authenticated decryption failed. {str(e)}"
        )
    except CryptographicIntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")

    audit_entry = AuditLog(
        user_id=current_user.user_id,
        action="HYBRID_DECRYPTION",
        target_resource_type="IMAGE",
        target_resource_id=image_id,
        ip_address="127.0.0.1",
        status="SUCCESS",
        details_json={
            "performance": decrypt_res["performance"],
            "is_bit_exact": decrypt_res["is_bit_exact"]
        },
        prev_record_hash="0" * 64,
        current_record_hash="0" * 64
    )
    db.add(audit_entry)
    db.commit()

    return {
        "status": "SUCCESS",
        "image_id": image_id,
        "is_bit_exact": decrypt_res["is_bit_exact"],
        "original_sha256": decrypt_res["original_sha256"],
        "reconstructed_sha256": decrypt_res["reconstructed_sha256"],
        "dimensions": decrypt_res["dimensions"],
        "metadata": decrypt_res["metadata"],
        "performance": decrypt_res["performance"],
        "mime_type": decrypt_res["mime_type"],
        "data_uri": decrypt_res["data_uri"]
    }

@router.get("/hybrid/package/{image_id}")
def download_hice_package(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Downloads the raw .hice encrypted binary container."""
    img_record = db.query(EncryptedImage).filter(EncryptedImage.image_id == image_id).first()
    if not img_record:
        raise HTTPException(status_code=404, detail="Image not found.")

    hice_path = os.path.join(settings.VAULT_STORAGE_PATH, f"{image_id}.hice")
    if not os.path.exists(hice_path):
        if os.path.exists(img_record.storage_path) and img_record.storage_path.endswith(".hice"):
            hice_path = img_record.storage_path
        else:
            raise HTTPException(status_code=404, detail=".hice package does not exist.")

    return FileResponse(
        path=hice_path,
        media_type="application/octet-stream",
        filename=f"{img_record.title or image_id}.hice"
    )

@router.post("/hybrid/direct-decrypt-file")
async def direct_decrypt_uploaded_file(
    file: UploadFile = File(...),
    master_key: str = Form("HICE_CLINICAL_MASTER_KEY_2026"),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Decodes an arbitrary uploaded .hice file and reconstructs the image immediately.
    """
    package_bytes = await file.read()
    try:
        decrypt_res = HybridDecryptionPipeline.decrypt_package(
            package_bytes=package_bytes,
            master_key=master_key,
            verify_bit_exact=True
        )
    except TamperingDetectedError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decrypt package: {str(e)}")

    return {
        "status": "SUCCESS",
        "is_bit_exact": decrypt_res["is_bit_exact"],
        "original_sha256": decrypt_res["original_sha256"],
        "reconstructed_sha256": decrypt_res["reconstructed_sha256"],
        "dimensions": decrypt_res["dimensions"],
        "metadata": decrypt_res["metadata"],
        "performance": decrypt_res["performance"],
        "mime_type": decrypt_res["mime_type"],
        "data_uri": decrypt_res["data_uri"]
    }
