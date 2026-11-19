"""
Secure Image Sharing REST API Endpoints (Phase 8)
Implements doctor-to-doctor clinical image transfers:
- Recipient-specific key wrapping via NIST P-256 ECDH & HKDF-SHA256
- Granular permission enforcement (VIEW, DECRYPT, DOWNLOAD)
- Time-limited validity and automatic expiration checks
- Instant cryptographic access revocation
- Audit ledger hash-chaining integration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import os
import io
import uuid
import json
import numpy as np
from PIL import Image

from app.database.connection import get_db
from app.models.db_models import User, EncryptedImage, ImageShare, AuditLog
from app.security.rbac import get_current_user
from app.key_management.key_wrapper import KeyWrapper, KeyWrapError
from app.encryption.hybrid_pipeline import HybridEncryptionPipeline
from app.decryption.hybrid_decryption import HybridDecryptionPipeline
from app.security.audit_ledger import AuditLedger
from app.config import settings

router = APIRouter(prefix="/api/v1/shares", tags=["Secure Image Sharing"])

@router.get("/clinicians")
def list_available_clinicians(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """
    Returns authorized clinicians and doctors available for secure scan transfers.
    Excludes the calling user.
    """
    users = db.query(User).filter(
        User.user_id != current_user.user_id,
        User.is_active == True
    ).all()

    return [
        {
            "user_id": u.user_id,
            "username": u.username,
            "email": u.email,
            "role": u.role.role_name if u.role else "USER",
            "has_public_key": bool(u.public_key_pem)
        }
        for u in users
    ]

@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_image_share(
    image_id: str = Form(...),
    receiver_username: str = Form(...),
    permission_type: str = Form("VIEW"),
    expiry_hours: int = Form(24),
    master_key: str = Form("HICE_CLINICAL_MASTER_KEY_2026"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Creates an authorized share for a recipient doctor:
    1. Validates ownership and permissions.
    2. Encapsulates the image master key using recipient's ECDH public key.
    3. Persists the share with expiration and granular access flags.
    """
    image = db.query(EncryptedImage).filter(EncryptedImage.image_id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found in vault.")
    
    user_role = current_user.role.role_name if current_user.role else "USER"
    if image.uploader_id != current_user.user_id and user_role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="You do not have permission to share this scan.")

    receiver = db.query(User).filter(User.username == receiver_username).first()
    if not receiver:
        raise HTTPException(status_code=404, detail=f"Recipient doctor '{receiver_username}' not found.")
    if receiver.user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot create a share to yourself.")
    if not receiver.public_key_pem:
        raise HTTPException(status_code=400, detail="Recipient does not have a registered ECDH public key.")

    perm = permission_type.upper()
    if perm not in ["VIEW", "DECRYPT", "DOWNLOAD"]:
        raise HTTPException(status_code=400, detail="Permission must be one of: VIEW, DECRYPT, DOWNLOAD.")

    now = datetime.now(timezone.utc)
    expires_at = (now + timedelta(hours=max(1, expiry_hours))).replace(microsecond=0)
    expires_at_str = expires_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    share_id = str(uuid.uuid4())

    k_master = HybridEncryptionPipeline.normalize_master_key(master_key)
    aad_metadata = {
        "share_id": share_id,
        "image_id": image_id,
        "receiver_id": receiver.user_id,
        "permission_type": perm,
        "expires_at": expires_at_str
    }

    try:
        wrap_res = KeyWrapper.encapsulate_key(
            recipient_public_key_pem=receiver.public_key_pem,
            plaintext_key=k_master,
            aad_metadata=aad_metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key encapsulation failed: {str(e)}")

    share_record = ImageShare(
        share_id=share_id,
        image_id=image_id,
        sender_id=current_user.user_id,
        receiver_id=receiver.user_id,
        encrypted_key_for_receiver=wrap_res["encrypted_key_bundle"],
        ephemeral_public_key=wrap_res["ephemeral_public_key_pem"],
        permission_type=perm,
        expires_at=expires_at,
        is_revoked=False,
        created_at=now
    )
    db.add(share_record)
    db.commit()

    AuditLedger.record_event(
        db=db,
        action="SHARE_CREATION",
        user_id=current_user.user_id,
        target_resource_type="SHARE",
        target_resource_id=share_id,
        status="SUCCESS",
        details_json={
            "image_id": image_id,
            "receiver_username": receiver.username,
            "permission": perm,
            "expiry_hours": expiry_hours
        }
    )

    return {
        "status": "SUCCESS",
        "message": f"Scan securely encapsulated and shared with Dr. {receiver.username}.",
        "share_id": share_id,
        "image_id": image_id,
        "image_title": image.title,
        "receiver_username": receiver.username,
        "permission_type": perm,
        "expires_at": expires_at.isoformat(),
        "ephemeral_key_established": True
    }

@router.get("/sent")
def list_sent_shares(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Returns all shares initiated by the calling clinician."""
    shares = db.query(ImageShare).filter(
        ImageShare.sender_id == current_user.user_id
    ).order_by(ImageShare.created_at.desc()).all()

    now = datetime.now(timezone.utc)
    result = []
    for s in shares:
        receiver = s.receiver
        image = s.image
        is_expired = False
        if s.expires_at:
            exp = s.expires_at if s.expires_at.tzinfo else s.expires_at.replace(tzinfo=timezone.utc)
            is_expired = now > exp

        result.append({
            "share_id": s.share_id,
            "image_id": s.image_id,
            "image_title": image.title if image else "Unknown Scan",
            "modality": image.metadata_record.modality if image and image.metadata_record else "GENERAL",
            "receiver_id": s.receiver_id,
            "receiver_username": receiver.username if receiver else "Unknown",
            "receiver_email": receiver.email if receiver else "",
            "permission_type": s.permission_type,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "is_revoked": s.is_revoked,
            "is_expired": is_expired,
            "status": "REVOKED" if s.is_revoked else ("EXPIRED" if is_expired else "ACTIVE"),
            "created_at": s.created_at.isoformat() if s.created_at else None
        })
    return result

@router.get("/received")
def list_received_shares(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """Returns all medical scans shared with the calling clinician."""
    shares = db.query(ImageShare).filter(
        ImageShare.receiver_id == current_user.user_id
    ).order_by(ImageShare.created_at.desc()).all()

    now = datetime.now(timezone.utc)
    result = []
    for s in shares:
        sender = s.sender
        image = s.image
        is_expired = False
        if s.expires_at:
            exp = s.expires_at if s.expires_at.tzinfo else s.expires_at.replace(tzinfo=timezone.utc)
            is_expired = now > exp

        result.append({
            "share_id": s.share_id,
            "image_id": s.image_id,
            "image_title": image.title if image else "Unknown Scan",
            "modality": image.metadata_record.modality if image and image.metadata_record else "GENERAL",
            "patient_pseudonym": image.metadata_record.patient_pseudonym if image and image.metadata_record else "ANONYMOUS",
            "sender_id": s.sender_id,
            "sender_username": sender.username if sender else "Unknown",
            "sender_email": sender.email if sender else "",
            "permission_type": s.permission_type,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "is_revoked": s.is_revoked,
            "is_expired": is_expired,
            "can_access": not s.is_revoked and not is_expired,
            "status": "REVOKED" if s.is_revoked else ("EXPIRED" if is_expired else "ACTIVE"),
            "created_at": s.created_at.isoformat() if s.created_at else None
        })
    return result

@router.post("/{share_id}/access")
def access_shared_image(
    share_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Recipient doctor decapsulates the wrapped key and executes lossless decryption:
    1. Enforces active validity (not expired and not revoked).
    2. Recipient computes ECDH Z = d_receiver · Q_ephemeral.
    3. Derives K_wrap and unwraps the master key K_master via AES-256-GCM.
    4. Decrypts the vault .hice scan and applies granular permission constraints.
    """
    share = db.query(ImageShare).filter(ImageShare.share_id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Shared scan transfer not found.")

    user_role = current_user.role.role_name if current_user.role else "USER"
    if share.receiver_id != current_user.user_id and user_role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="Access denied: You are not the designated recipient doctor.")

    if share.is_revoked:
        raise HTTPException(status_code=403, detail="ACCESS REVOKED: This scan share was revoked by the sender doctor.")

    now = datetime.now(timezone.utc)
    if share.expires_at:
        exp = share.expires_at if share.expires_at.tzinfo else share.expires_at.replace(tzinfo=timezone.utc)
        if now > exp:
            raise HTTPException(status_code=403, detail="ACCESS EXPIRED: The time-limited validity window for this scan has lapsed.")

    if not current_user.encrypted_private_key:
        raise HTTPException(status_code=400, detail="Recipient private key not found on profile.")

    expires_at_str = share.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ") if share.expires_at else ""
    aad_metadata = {
        "share_id": share.share_id,
        "image_id": share.image_id,
        "receiver_id": share.receiver_id,
        "permission_type": share.permission_type,
        "expires_at": expires_at_str
    }

    try:
        k_master = KeyWrapper.decapsulate_key(
            recipient_private_key_pem=current_user.encrypted_private_key,
            ephemeral_public_key_pem=share.ephemeral_public_key,
            encrypted_key_bundle_json=share.encrypted_key_for_receiver,
            aad_metadata=aad_metadata
        )
    except KeyWrapError as e:
        raise HTTPException(status_code=403, detail=f"Cryptographic key decapsulation failed: {str(e)}")

    hice_path = os.path.join(settings.VAULT_STORAGE_PATH, f"{share.image_id}.hice")
    if not os.path.exists(hice_path):
        if share.image and os.path.exists(share.image.storage_path) and share.image.storage_path.endswith(".hice"):
            hice_path = share.image.storage_path
        else:
            raise HTTPException(status_code=404, detail="Encrypted scan package not found in vault.")

    with open(hice_path, "rb") as f:
        package_bytes = f.read()

    try:
        decrypt_res = HybridDecryptionPipeline.decrypt_package(
            package_bytes=package_bytes,
            master_key=k_master,
            verify_bit_exact=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption of shared scan failed: {str(e)}")

    AuditLedger.record_event(
        db=db,
        action="SHARE_ACCESS",
        user_id=current_user.user_id,
        target_resource_type="SHARE",
        target_resource_id=share_id,
        status="SUCCESS",
        details_json={
            "image_id": share.image_id,
            "permission": share.permission_type,
            "is_bit_exact": decrypt_res["is_bit_exact"]
        }
    )

    return {
        "status": "SUCCESS",
        "share_id": share_id,
        "permission_type": share.permission_type,
        "can_download": share.permission_type == "DOWNLOAD",
        "is_bit_exact": decrypt_res["is_bit_exact"],
        "original_sha256": decrypt_res["original_sha256"],
        "reconstructed_sha256": decrypt_res["reconstructed_sha256"],
        "dimensions": decrypt_res["dimensions"],
        "metadata": decrypt_res["metadata"],
        "performance": decrypt_res["performance"],
        "data_uri": decrypt_res["data_uri"]
    }

@router.get("/{share_id}/download")
def download_shared_image(
    share_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Downloads decrypted image file ONLY if granular permission is DOWNLOAD.
    If permission is VIEW or DECRYPT, strictly rejects with 403 Forbidden.
    """
    share = db.query(ImageShare).filter(ImageShare.share_id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Shared scan transfer not found.")

    user_role = current_user.role.role_name if current_user.role else "USER"
    if share.receiver_id != current_user.user_id and user_role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="Access denied: You are not the designated recipient doctor.")

    if share.is_revoked:
        raise HTTPException(status_code=403, detail="ACCESS REVOKED: This scan share was revoked by the sender doctor.")

    now = datetime.now(timezone.utc)
    if share.expires_at:
        exp = share.expires_at if share.expires_at.tzinfo else share.expires_at.replace(tzinfo=timezone.utc)
        if now > exp:
            raise HTTPException(status_code=403, detail="ACCESS EXPIRED: Time-limited validity has lapsed.")

    # GRANULAR PERMISSION ENFORCEMENT
    if share.permission_type != "DOWNLOAD":
        raise HTTPException(
            status_code=403,
            detail=f"DOWNLOAD PERMISSION DENIED: Your permission level is '{share.permission_type}'. Only recipients with 'DOWNLOAD' permission may export scan files."
        )

    # Reconstruct AAD
    expires_at_str = share.expires_at.strftime("%Y-%m-%dT%H:%M:%SZ") if share.expires_at else ""
    aad_metadata = {
        "share_id": share.share_id,
        "image_id": share.image_id,
        "receiver_id": share.receiver_id,
        "permission_type": share.permission_type,
        "expires_at": expires_at_str
    }

    try:
        k_master = KeyWrapper.decapsulate_key(
            recipient_private_key_pem=current_user.encrypted_private_key,
            ephemeral_public_key_pem=share.ephemeral_public_key,
            encrypted_key_bundle_json=share.encrypted_key_for_receiver,
            aad_metadata=aad_metadata
        )
    except Exception as e:
        raise HTTPException(status_code=403, detail=f"Key decapsulation failed: {str(e)}")

    hice_path = os.path.join(settings.VAULT_STORAGE_PATH, f"{share.image_id}.hice")
    if not os.path.exists(hice_path):
        if share.image and os.path.exists(share.image.storage_path) and share.image.storage_path.endswith(".hice"):
            hice_path = share.image.storage_path
        else:
            raise HTTPException(status_code=404, detail="Encrypted scan package not found in vault.")

    with open(hice_path, "rb") as f:
        package_bytes = f.read()

    decrypt_res = HybridDecryptionPipeline.decrypt_package(
        package_bytes=package_bytes,
        master_key=k_master,
        verify_bit_exact=True
    )

    png_bytes = decrypt_res["image_bytes"]

    AuditLedger.record_event(
        db=db,
        action="SHARE_DOWNLOAD",
        user_id=current_user.user_id,
        target_resource_type="SHARE",
        target_resource_id=share_id,
        status="SUCCESS",
        details_json={"image_id": share.image_id, "size_bytes": len(png_bytes)}
    )

    filename = f"decrypted_{share.image.original_filename if share.image else 'scan.png'}"
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

@router.delete("/{share_id}/revoke")
def revoke_image_share(
    share_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Instantly revokes an active share. Subsequent access requests by the recipient will be denied.
    """
    share = db.query(ImageShare).filter(ImageShare.share_id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share record not found.")

    user_role = current_user.role.role_name if current_user.role else "USER"
    if share.sender_id != current_user.user_id and user_role not in ["ADMIN", "SUPER_ADMIN"]:
        raise HTTPException(status_code=403, detail="You do not have permission to revoke this share.")

    if share.is_revoked:
        return {"status": "ALREADY_REVOKED", "message": "This share was already revoked."}

    now = datetime.now(timezone.utc)
    share.is_revoked = True
    share.revoked_at = now
    db.commit()

    AuditLedger.record_event(
        db=db,
        action="SHARE_REVOCATION",
        user_id=current_user.user_id,
        target_resource_type="SHARE",
        target_resource_id=share_id,
        status="SUCCESS",
        details_json={"image_id": share.image_id}
    )

    return {
        "status": "SUCCESS",
        "message": "Share access revoked immediately. Recipient cannot decrypt or view this scan.",
        "share_id": share_id,
        "revoked_at": now.isoformat()
    }
