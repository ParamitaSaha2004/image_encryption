"""
Unit & Integration Tests: Phase 9 - Tamper Detection & Cryptographic Hash-Chained Audit Ledger
Verifies:
- Formula: Hash_n = SHA256(Hash_{n-1} || CanonicalEvent_n)
- Genesis block continuity
- Whole ledger chain validation
- Immediate detection and pinpointing of retroactive historical tampering
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.connection import SessionLocal
from app.models.db_models import User, AuditLog
from app.security.audit_ledger import AuditLedger, GENESIS_HASH
from app.security.token_util import create_access_token

client = TestClient(app)

@pytest.fixture
def auth_headers():
    db = SessionLocal()
    admin = db.query(User).filter(User.username == "sec_admin").first()
    token = create_access_token({"sub": admin.user_id, "username": admin.username, "role": "ADMIN"})
    db.close()
    return {"Authorization": f"Bearer {token}"}

def test_hash_chain_formula_and_sequential_integrity():
    db = SessionLocal()
    try:
        # Clear existing logs for a clean unit test
        db.query(AuditLog).delete()
        db.commit()

        # 1. Record first event -> prev_record_hash must be GENESIS_HASH
        log1 = AuditLedger.record_event(
            db=db,
            action="CLINICAL_SESSION_START",
            user_id="user_1",
            target_resource_type="SESSION",
            details_json={"ip": "192.168.1.10"}
        )
        assert log1.prev_record_hash == GENESIS_HASH
        assert len(log1.current_record_hash) == 64

        # 2. Record second event -> prev_record_hash must equal log1.current_record_hash
        log2 = AuditLedger.record_event(
            db=db,
            action="SCAN_UPLOAD",
            user_id="user_1",
            target_resource_type="IMAGE",
            target_resource_id="img_1001",
            details_json={"size": 102400}
        )
        assert log2.prev_record_hash == log1.current_record_hash

        # 3. Record third event
        log3 = AuditLedger.record_event(
            db=db,
            action="HYBRID_ENCRYPTION_COMPLETE",
            user_id="user_1",
            target_resource_type="IMAGE",
            target_resource_id="img_1001"
        )
        assert log3.prev_record_hash == log2.current_record_hash

        # 4. Verify chain integrity
        verif = AuditLedger.verify_chain(db)
        assert verif["is_valid"] is True
        assert verif["total_records"] == 3
        assert verif["verified_count"] == 3
        assert verif["head_hash"] == log3.current_record_hash

    finally:
        db.query(AuditLog).delete()
        db.commit()
        db.close()

def test_tampering_detection_pinpoints_corrupted_record():
    db = SessionLocal()
    try:
        db.query(AuditLog).delete()
        db.commit()

        # Insert 5 sequential chained events
        for i in range(5):
            AuditLedger.record_event(
                db=db,
                action=f"EVENT_{i}",
                user_id="user_1",
                details_json={"index": i}
            )

        # Baseline: verified
        v_clean = AuditLedger.verify_chain(db)
        assert v_clean["is_valid"] is True
        assert v_clean["total_records"] == 5

        # Malicious insider tampers with record #2 directly in database
        logs = db.query(AuditLog).order_by(AuditLog.log_id.asc()).all()
        target = logs[2]
        target.action = "TAMPERED_COVERUP_ACTION"
        db.commit()

        # Verification must now FAIL and pinpoint index 2
        v_tampered = AuditLedger.verify_chain(db)
        assert v_tampered["is_valid"] is False
        assert v_tampered["broken_at_index"] == 2
        assert v_tampered["broken_at_id"] == target.log_id
        assert v_tampered["failure_type"] == "RECORD_CONTENT_MUTATED"

    finally:
        db.query(AuditLog).delete()
        db.commit()
        db.close()

def test_audit_api_verification_endpoint(auth_headers):
    # Record a test event via API
    resp = client.post(
        "/api/v1/audit/record-test-event?action=SECURITY_AUDIT_PING",
        headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "SUCCESS"

    # Call verification endpoint
    v_resp = client.get("/api/v1/audit/verify", headers=auth_headers)
    assert v_resp.status_code == 200
    assert "is_valid" in v_resp.json()
