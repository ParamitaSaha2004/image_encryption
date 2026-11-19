"""
Cryptographic Hash-Chained Audit Ledger Module (Phase 9)
Implements tamper-evident sequential audit logging:
Hash_n = SHA256(Hash_{n-1} || CanonicalEvent_n)
Guarantees immutability, retroactive alteration detection, and chronological chain-of-custody.
"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.db_models import AuditLog

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

class AuditLedger:
    @staticmethod
    def canonicalize_event(
        user_id: Optional[str],
        action: str,
        target_resource_type: Optional[str],
        target_resource_id: Optional[str],
        ip_address: Optional[str],
        status: str,
        details_json: Optional[Any],
        timestamp_str: str
    ) -> bytes:
        """
        Produces a deterministic, canonical byte representation of an operational event.
        Guarantees identical serialization across architectures and runs.
        """
        payload = {
            "user_id": user_id or "ANONYMOUS",
            "action": str(action),
            "target_resource_type": str(target_resource_type or "SYSTEM"),
            "target_resource_id": str(target_resource_id or "NONE"),
            "ip_address": str(ip_address or "127.0.0.1"),
            "status": str(status),
            "details": details_json if details_json is not None else {},
            "timestamp": timestamp_str
        }
        return json.dumps(payload, sort_keys=True, separators=(',', ':')).encode('utf-8')

    @staticmethod
    def compute_record_hash(prev_hash: str, canonical_bytes: bytes) -> str:
        """Computes Hash_n = SHA256(Hash_{n-1} || CanonicalBytes)."""
        hasher = hashlib.sha256()
        hasher.update(prev_hash.encode('utf-8'))
        hasher.update(b"//")
        hasher.update(canonical_bytes)
        return hasher.hexdigest()

    @classmethod
    def record_event(
        cls,
        db: Session,
        action: str,
        user_id: Optional[str] = None,
        target_resource_type: Optional[str] = None,
        target_resource_id: Optional[str] = None,
        ip_address: Optional[str] = "127.0.0.1",
        status: str = "SUCCESS",
        details_json: Optional[Dict[str, Any]] = None,
        commit: bool = True
    ) -> AuditLog:
        """
        Records a new audit entry cryptographically chained to the preceding head record.
        """
        last_log = db.query(AuditLog).order_by(AuditLog.log_id.desc()).first()
        prev_hash = last_log.current_record_hash if (last_log and last_log.current_record_hash) else GENESIS_HASH

        now_utc = datetime.now(timezone.utc)
        timestamp_str = now_utc.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Store details with the canonical timestamp string preserved in details for verification
        details_to_store = dict(details_json or {})
        details_to_store["_canonical_timestamp"] = timestamp_str

        canonical_bytes = cls.canonicalize_event(
            user_id=user_id,
            action=action,
            target_resource_type=target_resource_type,
            target_resource_id=target_resource_id,
            ip_address=ip_address,
            status=status,
            details_json=details_to_store,
            timestamp_str=timestamp_str
        )

        current_hash = cls.compute_record_hash(prev_hash, canonical_bytes)

        entry = AuditLog(
            user_id=user_id,
            action=action,
            target_resource_type=target_resource_type,
            target_resource_id=target_resource_id,
            ip_address=ip_address,
            status=status,
            details_json=details_to_store,
            prev_record_hash=prev_hash,
            current_record_hash=current_hash,
            timestamp=now_utc
        )
        db.add(entry)
        if commit:
            db.commit()
            db.refresh(entry)
        return entry

    @classmethod
    def verify_chain(cls, db: Session) -> Dict[str, Any]:
        """
        Verifies the cryptographic integrity of the entire audit log chain from genesis to head.
        Pinpoints the exact record ID and index if tampering, deletion, or retrofitting is detected.
        """
        logs = db.query(AuditLog).order_by(AuditLog.log_id.asc()).all()
        if not logs:
            return {
                "is_valid": True,
                "total_records": 0,
                "verified_count": 0,
                "genesis_hash": GENESIS_HASH,
                "head_hash": GENESIS_HASH,
                "status": "EMPTY_LEDGER",
                "message": "Audit ledger is currently empty."
            }

        prev_hash = GENESIS_HASH
        for idx, log in enumerate(logs):
            # Check 1: prev_record_hash continuity
            if log.prev_record_hash != prev_hash:
                return {
                    "is_valid": False,
                    "total_records": len(logs),
                    "verified_count": idx,
                    "broken_at_id": log.log_id,
                    "broken_at_index": idx,
                    "failure_type": "CHAIN_BROKEN_DISCONTINUITY",
                    "reason": f"Record #{log.log_id} prev_hash '{log.prev_record_hash[:16]}...' does not match preceding hash '{prev_hash[:16]}...'",
                    "tampered_record": {
                        "log_id": log.log_id,
                        "action": log.action,
                        "timestamp": str(log.timestamp)
                    }
                }

            # Check 2: recompute hash
            stored_details = log.details_json or {}
            canonical_ts = stored_details.get("_canonical_timestamp")
            if not canonical_ts:
                # If canonical timestamp was not stored (legacy record), use standard ISO format
                canonical_ts = log.timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ") if log.timestamp else ""

            # Check if record has valid format
            canonical_bytes = cls.canonicalize_event(
                user_id=log.user_id,
                action=log.action,
                target_resource_type=log.target_resource_type,
                target_resource_id=log.target_resource_id,
                ip_address=log.ip_address,
                status=log.status,
                details_json=stored_details,
                timestamp_str=canonical_ts
            )
            expected_hash = cls.compute_record_hash(prev_hash, canonical_bytes)

            if log.current_record_hash != expected_hash:
                return {
                    "is_valid": False,
                    "total_records": len(logs),
                    "verified_count": idx,
                    "broken_at_id": log.log_id,
                    "broken_at_index": idx,
                    "failure_type": "RECORD_CONTENT_MUTATED",
                    "reason": f"Record #{log.log_id} content was modified! Recomputed hash '{expected_hash[:16]}...' != stored hash '{log.current_record_hash[:16]}...'",
                    "tampered_record": {
                        "log_id": log.log_id,
                        "action": log.action,
                        "timestamp": str(log.timestamp)
                    }
                }

            prev_hash = log.current_record_hash

        return {
            "is_valid": True,
            "total_records": len(logs),
            "verified_count": len(logs),
            "genesis_hash": GENESIS_HASH,
            "head_hash": logs[-1].current_record_hash,
            "status": "SECURE_VERIFIED",
            "message": f"Cryptographic audit chain completely verified: all {len(logs)} records are intact and untampered."
        }

    @classmethod
    def simulate_tampering(cls, db: Session, log_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Simulates an unauthorized insider modification:
        Modifies a historical record's action or data WITHOUT re-chaining,
        demonstrating that verify_chain() immediately flags the corruption.
        """
        if log_id is not None:
            target_log = db.query(AuditLog).filter(AuditLog.log_id == log_id).first()
        else:
            # Pick the middle or first record
            target_log = db.query(AuditLog).order_by(AuditLog.log_id.asc()).first()

        if not target_log:
            return {"status": "ERROR", "message": "No audit records found to tamper with."}

        original_action = target_log.action
        # Maliciously alter action in database without updating cryptographic hash
        target_log.action = "MALICIOUS_UNAUTHORIZED_EXPORT_TAMPERED"
        db.commit()

        return {
            "status": "TAMPERED",
            "message": f"Simulated tampering applied to audit record #{target_log.log_id}.",
            "target_log_id": target_log.log_id,
            "original_action": original_action,
            "tampered_action": target_log.action
        }
