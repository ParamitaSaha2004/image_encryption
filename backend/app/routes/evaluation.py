"""
Security Evaluation & Cryptographic Benchmarks API Endpoints (Phase 11)
Provides comparative security analytics: Entropy, NPCR, UACI, and Pearson Correlation.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import numpy as np

from app.database.connection import get_db
from app.models.db_models import User, EncryptedImage, EncryptionMetric
from app.security.rbac import get_current_user
from app.evaluation.benchmark_engine import SecurityEvaluationEngine
from app.encryption.hybrid_pipeline import HybridEncryptionPipeline
from app.config import settings

router = APIRouter(prefix="/api/v1/evaluation", tags=["Security Evaluation & Benchmarks"])

@router.post("/run/{image_id}")
def run_evaluation_benchmark(
    image_id: str,
    master_key: str = Query("HICE_CLINICAL_MASTER_KEY_2026"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Executes a complete 4-way cryptographic benchmark on a vault image:
    1. Loads raw pixel bytes from vault.
    2. Runs AES Only, Chaos+AES, CA+AES, and Full Hybrid.
    3. Computes Shannon Entropy (H ≈ 7.999), NPCR (>99.6%), UACI (>33.4%), and Pearson correlation.
    4. Persists records to database and returns comparative payload.
    """
    img = db.query(EncryptedImage).filter(EncryptedImage.image_id == image_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found in vault.")

    # Find the ingested raw pixel tensor or raw bin
    raw_path = os.path.join(settings.VAULT_STORAGE_PATH, f"ingested_{image_id}.bin")
    if not os.path.exists(raw_path):
        # Check storage path
        if os.path.exists(img.storage_path) and not img.storage_path.endswith(".hice"):
            raw_path = img.storage_path
        else:
            raise HTTPException(status_code=400, detail="Raw ingested image bytes not found for benchmarking.")

    with open(raw_path, "rb") as f:
        pixel_bytes = f.read()

    pixel_vector = np.frombuffer(pixel_bytes, dtype=np.uint8)
    master_key_bytes = HybridEncryptionPipeline.normalize_master_key(master_key)

    benchmark_data = SecurityEvaluationEngine.run_4way_comparative_benchmark(
        image_id=image_id,
        pixel_vector=pixel_vector,
        height=img.height,
        width=img.width,
        channels=img.channels,
        master_key_bytes=master_key_bytes,
        db=db
    )

    return {
        "status": "SUCCESS",
        "image_title": img.title,
        "dimensions": f"{img.width}x{img.height}x{img.channels}",
        "benchmark_data": benchmark_data
    }

@router.get("/comparative/{image_id}")
def get_comparative_metrics(
    image_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Retrieves stored 4-way comparative metrics for a specified image.
    """
    metrics = db.query(EncryptionMetric).filter(EncryptionMetric.image_id == image_id).all()
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail="No evaluation metrics found for this scan. Run /api/v1/evaluation/run/{image_id} first."
        )

    return {
        "image_id": image_id,
        "metrics": [
            {
                "configuration": m.configuration,
                "entropy": float(m.entropy),
                "npcr": float(m.npcr),
                "uaci": float(m.uaci),
                "h_corr": float(m.h_corr),
                "v_corr": float(m.v_corr),
                "d_corr": float(m.d_corr),
                "encryption_time_ms": float(m.encryption_time_ms),
                "decryption_time_ms": float(m.decryption_time_ms),
                "exact_recovery": m.exact_recovery,
                "evaluated_at": m.evaluated_at.isoformat() if m.evaluated_at else None
            }
            for m in metrics
        ]
    }
