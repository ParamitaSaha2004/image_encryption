"""
Phase 12 - Comprehensive End-to-End Clinical Workflow Test Suite
Executes the full clinical demonstration across all 12 platform phases:
1. Ingestion & Validation (Phase 1)
2. Pre-cipher Chaotic Permutation (Phase 2)
3. Pre-cipher Cellular Automata Diffusion (Phase 3)
4. AES-256-GCM Authenticated Encryption (Phase 4)
5. NIST P-256 ECDH Key Agreement & HKDF (Phase 5)
6. Exact Lossless Inversion & Reconstruction (Phase 6)
7. REST API Integration (Phase 7)
8. Doctor-to-Doctor Secure Sharing & Granular Permissions (Phase 8)
9. Tamper-Evident SHA-256 Chained Audit Trail (Phase 9)
10. AI-Based Suspicious Activity Sentry (Phase 10)
11. Quantitative Cryptographic Benchmarks (Phase 11)
12. Final Validation & Chain-of-Custody Verification (Phase 12)
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import SessionLocal
from app.models.db_models import User
from app.security.token_util import create_access_token
from app.security.audit_ledger import AuditLedger

client = TestClient(app)

def test_full_clinical_workflow_lifecycle():
    db = SessionLocal()
    try:
        # Start with clean audit ledger for clinical lifecycle
        from app.models.db_models import AuditLog
        db.query(AuditLog).delete()
        db.commit()

        # Step 1: Clinician Authentication
        alice = db.query(User).filter(User.username == "dr_alice_radiology").first()
        bob = db.query(User).filter(User.username == "dr_bob_oncology").first()
        admin = db.query(User).filter(User.username == "sec_admin").first()

        alice_token = create_access_token({"sub": alice.user_id, "username": alice.username, "role": "USER"})
        bob_token = create_access_token({"sub": bob.user_id, "username": bob.username, "role": "USER"})
        admin_token = create_access_token({"sub": admin.user_id, "username": admin.username, "role": "ADMIN"})

        alice_headers = {"Authorization": f"Bearer {alice_token}"}
        bob_headers = {"Authorization": f"Bearer {bob_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Step 2: Dr. Alice ingests synthetic Chest X-Ray
        load_resp = client.post(
            "/api/v1/images/samples/load/synthetic_chest_xray.png",
            headers=alice_headers
        )
        assert load_resp.status_code == 200
        ingest_data = load_resp.json()
        image_id = ingest_data["image_id"]
        original_sha = ingest_data["original_sha256"]

        # Step 3: Dr. Alice executes Hybrid Encryption (Chaos + CA + AES-256-GCM)
        enc_resp = client.post(
            f"/api/v1/crypto/hybrid/encrypt/{image_id}",
            data={"master_key": "HICE_CLINICAL_MASTER_KEY_2026", "ca_rule": 30},
            headers=alice_headers
        )
        assert enc_resp.status_code == 200
        enc_data = enc_resp.json()
        assert enc_data["status"] == "SUCCESS"

        # Step 4: Run Cryptographic Benchmarks (Phase 11)
        bench_resp = client.post(
            f"/api/v1/evaluation/run/{image_id}",
            params={"master_key": "HICE_CLINICAL_MASTER_KEY_2026"},
            headers=alice_headers
        )
        assert bench_resp.status_code == 200
        benchmarks = bench_resp.json()["benchmark_data"]["comparative_benchmarks"]
        assert len(benchmarks) == 4
        hybrid_metric = next(b for b in benchmarks if "Full Hybrid" in b["configuration"])
        assert hybrid_metric["entropy"] >= 7.990
        assert hybrid_metric["npcr"] >= 99.0

        # Step 5: Secure Sharing with Granular Permission (Phase 8: VIEW permission)
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

        # Step 6: Dr. Bob decapsulates key and accesses scan
        bob_access_resp = client.post(f"/api/v1/shares/{share_id}/access", headers=bob_headers)
        assert bob_access_resp.status_code == 200
        bob_acc = bob_access_resp.json()
        assert bob_acc["is_bit_exact"] is True
        assert bob_acc["reconstructed_sha256"] == original_sha
        assert bob_acc["can_download"] is False

        # Step 7: Dr. Bob tries unauthorized download -> blocked
        blocked_down = client.get(f"/api/v1/shares/{share_id}/download", headers=bob_headers)
        assert blocked_down.status_code == 403

        # Step 8: Dr. Alice shares with DOWNLOAD permission
        share_down_resp = client.post(
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
        share_down_id = share_down_resp.json()["share_id"]

        # Bob downloads successfully
        bob_down = client.get(f"/api/v1/shares/{share_down_id}/download", headers=bob_headers)
        assert bob_down.status_code == 200
        assert bob_down.headers["content-type"] == "image/png"

        # Step 9: Alice instantly revokes the download share
        revoke_resp = client.delete(f"/api/v1/shares/{share_down_id}/revoke", headers=alice_headers)
        assert revoke_resp.status_code == 200

        # Subsequent download is rejected
        revoked_down = client.get(f"/api/v1/shares/{share_down_id}/download", headers=bob_headers)
        assert revoked_down.status_code == 403

        # Step 10: AI Security Sentry detects simulated threat (Phase 10)
        attack_resp = client.post(
            "/api/v1/monitoring/simulate-attack?attack_type=NOCTURNAL_BULK_DOWNLOAD",
            headers=admin_headers
        )
        assert attack_resp.status_code == 200
        assert attack_resp.json()["detection_result"]["is_anomaly"] is True

        # Step 11: Cryptographic Hash-Chained Audit Ledger Verification (Phase 9)
        verify_resp = client.get("/api/v1/audit/verify", headers=admin_headers)
        assert verify_resp.status_code == 200
        v_data = verify_resp.json()
        assert v_data["is_valid"] is True
        assert v_data["verified_count"] >= 5

    finally:
        db.close()
