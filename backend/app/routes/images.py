"""
Image Ingestion and Management API Endpoints
Handles image upload, format validation, pixel normalization,
metadata sanitization, and demonstration sample ingestion.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.database.connection import get_db
from app.models.db_models import User, EncryptedImage, ImageMetadata, AuditLog
from app.models.schemas import EncryptedImageResponse
from app.security.rbac import get_current_user
from app.image_processing.preprocessor import ImagePreprocessor
from app.image_processing.validator import ImageValidationError
from app.image_processing.metadata_extractor import MetadataSanitizer
from app.security.audit_ledger import AuditLedger
from app.config import settings

router = APIRouter(prefix="/api/v1/images", tags=["Image Ingestion"])

SAMPLES_DIR = Path(settings.SAMPLES_STORAGE_PATH)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_image(
    file: UploadFile = File(...),
    title: str = Form(...),
    modality: str = Form("GENERAL"),
    body_part: Optional[str] = Form(None),
    patient_pseudonym: Optional[str] = Form(None),
    clinical_notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingests an image, enforces magic-byte security checks, extracts dimensions,
    normalizes the pixel tensor, isolates clinical metadata, and logs an audit record.
    """
    file_bytes = await file.read()
    filename = file.filename or "unknown.png"

    try:
        processed = ImagePreprocessor.process(file_bytes, filename)
    except ImageValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image preprocessing failed: {str(e)}")

    image_id = str(uuid.uuid4())
    ingested_filename = f"ingested_{image_id}.bin"
    storage_path = os.path.join(settings.VAULT_STORAGE_PATH, ingested_filename)

    # Save normalized byte vector to secure storage vault
    with open(storage_path, "wb") as f:
        f.write(processed["vector"].tobytes())

    # Sanitize clinical metadata
    clinical_input = {
        "modality": modality,
        "body_part": body_part,
        "patient_pseudonym": patient_pseudonym,
        "clinical_notes": clinical_notes
    }
    sanitized_meta = MetadataSanitizer.extract_and_sanitize(file_bytes, clinical_input)

    # Create EncryptedImage record
    new_image = EncryptedImage(
        image_id=image_id,
        title=title,
        original_filename=filename,
        mime_type=file.content_type or f"image/{processed['format'].lower()}",
        file_size_bytes=len(file_bytes),
        width=processed["width"],
        height=processed["height"],
        channels=processed["channels"],
        storage_path=storage_path,
        original_sha256=processed["original_sha256"],
        ciphertext_sha256="PENDING_ENCRYPTION",
        nonce_hex="0" * 24,
        auth_tag_hex="0" * 32,
        aad_json={
            "image_id": image_id,
            "uploader_id": current_user.user_id,
            "dimensions": [processed["height"], processed["width"], processed["channels"]],
            "original_sha256": processed["original_sha256"]
        },
        uploader_id=current_user.user_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_image)
    db.commit()

    # Create ImageMetadata record
    meta_record = ImageMetadata(
        metadata_id=str(uuid.uuid4()),
        image_id=image_id,
        modality=sanitized_meta["modality"],
        body_part=sanitized_meta["body_part"],
        patient_pseudonym=sanitized_meta["patient_pseudonym"],
        clinical_notes=sanitized_meta["clinical_notes"]
    )
    db.add(meta_record)

    # Cryptographic Hash-Chained Audit Log
    AuditLedger.record_event(
        db=db,
        action="IMAGE_INGESTION",
        user_id=current_user.user_id,
        target_resource_type="IMAGE",
        target_resource_id=image_id,
        ip_address="127.0.0.1",
        status="SUCCESS",
        details_json={
            "filename": filename,
            "dimensions": f"{processed['width']}x{processed['height']}x{processed['channels']}",
            "sha256": processed["original_sha256"]
        }
    )

    return {
        "status": "SUCCESS",
        "message": "Image validated, normalized, and ingested successfully.",
        "image_id": image_id,
        "title": title,
        "original_filename": filename,
        "format": processed["format"],
        "dimensions": {
            "width": processed["width"],
            "height": processed["height"],
            "channels": processed["channels"]
        },
        "file_size_bytes": len(file_bytes),
        "original_sha256": processed["original_sha256"],
        "modality": sanitized_meta["modality"],
        "patient_pseudonym": sanitized_meta["patient_pseudonym"]
    }

@router.get("", response_model=List[Dict[str, Any]])
def list_images(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Lists images uploaded by the authenticated clinician."""
    images = db.query(EncryptedImage).filter(EncryptedImage.uploader_id == current_user.user_id).order_by(EncryptedImage.created_at.desc()).all()
    
    result = []
    for img in images:
        meta = img.metadata_record
        result.append({
            "image_id": img.image_id,
            "title": img.title,
            "original_filename": img.original_filename,
            "mime_type": img.mime_type,
            "file_size_bytes": img.file_size_bytes,
            "width": img.width,
            "height": img.height,
            "channels": img.channels,
            "original_sha256": img.original_sha256,
            "is_encrypted": img.ciphertext_sha256 != "PENDING_ENCRYPTION",
            "modality": meta.modality if meta else "GENERAL",
            "patient_pseudonym": meta.patient_pseudonym if meta else "ANONYMOUS",
            "created_at": img.created_at
        })
    return result

@router.get("/samples/list")
def list_sample_scans():
    """Lists synthetic demonstration medical scans available in the vault."""
    samples = []
    for fname in ["synthetic_chest_xray.png", "synthetic_brain_mri.png", "sample_histology.bmp"]:
        fpath = SAMPLES_DIR / fname
        if fpath.exists():
            samples.append({
                "sample_id": fname,
                "name": fname.replace("_", " ").replace(".png", "").replace(".bmp", "").title(),
                "filename": fname,
                "size_bytes": fpath.stat().st_size
            })
    return samples

@router.post("/samples/load/{sample_name}")
async def load_sample_scan(
    sample_name: str, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Directly loads a synthetic medical scan into the active clinician's vault."""
    target_file = SAMPLES_DIR / sample_name
    if not target_file.exists():
        raise HTTPException(status_code=404, detail="Requested sample scan not found.")

    with open(target_file, "rb") as f:
        file_bytes = f.read()

    meta_presets = {
        "synthetic_chest_xray.png": ("Synthetic PA Chest X-Ray", "X-RAY", "CHEST", "PT-XRAY-7049"),
        "synthetic_brain_mri.png": ("Synthetic Axial T2 Brain MRI", "MRI", "BRAIN", "PT-MRI-9921"),
        "sample_histology.bmp": ("Histology Microscopy Cell Stain", "GENERAL", "CELL_TISSUE", "PT-HISTO-3012")
    }

    title, modality, body_part, pseudonym = meta_presets.get(
        sample_name, (sample_name, "GENERAL", "UNKNOWN", "PT-DEMO")
    )

    processed = ImagePreprocessor.process(file_bytes, sample_name)
    image_id = str(uuid.uuid4())
    storage_path = os.path.join(settings.VAULT_STORAGE_PATH, f"ingested_{image_id}.bin")

    with open(storage_path, "wb") as f:
        f.write(processed["vector"].tobytes())

    new_image = EncryptedImage(
        image_id=image_id,
        title=title,
        original_filename=sample_name,
        mime_type="image/png" if sample_name.endswith(".png") else "image/bmp",
        file_size_bytes=len(file_bytes),
        width=processed["width"],
        height=processed["height"],
        channels=processed["channels"],
        storage_path=storage_path,
        original_sha256=processed["original_sha256"],
        ciphertext_sha256="PENDING_ENCRYPTION",
        nonce_hex="0" * 24,
        auth_tag_hex="0" * 32,
        aad_json={
            "image_id": image_id,
            "uploader_id": current_user.user_id,
            "dimensions": [processed["height"], processed["width"], processed["channels"]],
            "original_sha256": processed["original_sha256"]
        },
        uploader_id=current_user.user_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(new_image)
    db.commit()

    meta_record = ImageMetadata(
        metadata_id=str(uuid.uuid4()),
        image_id=image_id,
        modality=modality,
        body_part=body_part,
        patient_pseudonym=pseudonym,
        clinical_notes=f"Synthetic research scan loaded for demonstration: {sample_name}"
    )
    db.add(meta_record)
    db.commit()

    return {
        "status": "SUCCESS",
        "message": f"Sample scan '{sample_name}' ingested successfully.",
        "image_id": image_id,
        "title": title,
        "dimensions": {
            "width": processed["width"],
            "height": processed["height"],
            "channels": processed["channels"]
        },
        "original_sha256": processed["original_sha256"]
    }
