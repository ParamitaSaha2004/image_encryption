"""
Cryptographic Audit Ledger API Endpoints (Phase 9)
Exposes verification and ledger inspection endpoints for tamper detection.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.database.connection import get_db
from app.models.db_models import User, AuditLog
from app.security.rbac import get_current_user, require_roles
from app.security.audit_ledger import AuditLedger

router = APIRouter(prefix="/api/v1/audit", tags=["Audit Ledger & Tamper Detection"])

@router.get("/logs")
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns cryptographically hash-chained audit logs with prev_record_hash and current_record_hash.
    """
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    
    total = query.count()
    records = query.order_by(AuditLog.log_id.desc()).offset(offset).limit(limit).all()

    return {
        "total_records": total,
        "returned_records": len(records),
        "offset": offset,
        "limit": limit,
        "logs": [
            {
                "log_id": r.log_id,
                "user_id": r.user_id,
                "action": r.action,
                "target_resource_type": r.target_resource_type,
                "target_resource_id": r.target_resource_id,
                "ip_address": r.ip_address,
                "status": r.status,
                "details": r.details_json,
                "prev_record_hash": r.prev_record_hash,
                "current_record_hash": r.current_record_hash,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None
            }
            for r in records
        ]
    }

@router.get("/verify")
def verify_audit_ledger_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Executes full cryptographic verification of the SHA-256 hash chain:
    Validates Hash_n = SHA256(Hash_{n-1} || Event) for every record from genesis to head.
    """
    return AuditLedger.verify_chain(db)

@router.post("/simulate-tamper")
def simulate_audit_tampering(
    log_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "SUPER_ADMIN"]))
) -> Dict[str, Any]:
    """
    Simulates unauthorized retroactive tampering with a historical audit log record
    without re-calculating the cryptographic hash chain.
    """
    return AuditLedger.simulate_tampering(db, log_id)

@router.post("/record-test-event")
def record_test_event(
    action: str = Query("SECURITY_DIAGNOSTIC_PING"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Appends a new test event into the hash chain.
    """
    entry = AuditLedger.record_event(
        db=db,
        action=action,
        user_id=current_user.user_id,
        target_resource_type="SYSTEM",
        status="SUCCESS",
        details_json={"initiated_by": current_user.username}
    )
    return {
        "status": "SUCCESS",
        "log_id": entry.log_id,
        "prev_record_hash": entry.prev_record_hash,
        "current_record_hash": entry.current_record_hash
    }
