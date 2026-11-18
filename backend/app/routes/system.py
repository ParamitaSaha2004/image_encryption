"""
System & Operational Health API Endpoints
Exposes environment status, database connection telemetry, and system-wide settings.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.connection import get_db, DB_TYPE
from app.models.db_models import SystemSetting, User, EncryptedImage
from app.config import settings

router = APIRouter(prefix="/api/v1/system", tags=["System"])

@router.get("/status")
def get_system_status(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_users = db.query(User).count()
    total_images = db.query(EncryptedImage).count()

    return {
        "status": "OPERATIONAL",
        "system_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database_backend": DB_TYPE,
        "vault_path": settings.VAULT_STORAGE_PATH,
        "total_registered_users": total_users,
        "total_encrypted_images": total_images,
        "security_features": {
            "symmetric_cipher": "AES-256-GCM",
            "key_agreement": "ECDH (NIST P-256)",
            "key_derivation": "HKDF-SHA256",
            "chaotic_permutation": "Logistic Map",
            "diffusion_transform": "Cellular Automata (Rule 30/90)",
            "ai_anomaly_detection": "Scikit-Learn Isolation Forest",
            "tamper_protection": "AEAD 128-bit Tag + Hash-Chained Audit Trail"
        }
    }

@router.get("/settings")
def get_system_settings(db: Session = Depends(get_db)):
    settings_records = db.query(SystemSetting).all()
    return {s.setting_key: s.setting_value for s in settings_records}
