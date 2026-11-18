"""
Pydantic Validation Schemas for HICE REST APIs
Defines request payloads, response bodies, and serialization schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

# ==================== Auth Schemas ====================
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=150)
    password: str = Field(..., min_length=8)
    role_name: Optional[str] = "USER"

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str

class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str
    role_name: str
    public_key_pem: Optional[str] = None
    created_at: datetime

# ==================== Image & Metadata Schemas ====================
class ImageMetadataCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    modality: str = Field("GENERAL", description="X-RAY, MRI, CT, GENERAL")
    body_part: Optional[str] = None
    patient_pseudonym: Optional[str] = None
    clinical_notes: Optional[str] = None

class EncryptedImageResponse(BaseModel):
    image_id: str
    title: str
    original_filename: str
    mime_type: str
    file_size_bytes: int
    width: int
    height: int
    channels: int
    original_sha256: str
    ciphertext_sha256: str
    created_at: datetime
    uploader_id: str

# ==================== Encryption / Decryption Schemas ====================
class EncryptionRequest(BaseModel):
    image_id: str
    configuration: str = Field("HYBRID_ALL", description="AES_ONLY, CHAOS_AES, CA_AES, HYBRID_ALL")
    ca_rule: int = Field(30, description="30 or 90")

class DecryptionRequest(BaseModel):
    image_id: str
    target_format: Optional[str] = "PNG"

# ==================== Sharing Schemas ====================
class ShareCreate(BaseModel):
    image_id: str
    receiver_username: str
    permission_type: str = Field("VIEW", description="VIEW, DECRYPT, DOWNLOAD")
    expires_in_hours: Optional[int] = Field(24, ge=1, le=720)

class ShareResponse(BaseModel):
    share_id: str
    image_id: str
    sender_username: str
    receiver_username: str
    permission_type: str
    expires_at: Optional[datetime]
    is_revoked: bool
    created_at: datetime

# ==================== Security & Audit Schemas ====================
class AuditLogResponse(BaseModel):
    log_id: int
    username: Optional[str]
    action: str
    target_resource_type: Optional[str]
    target_resource_id: Optional[str]
    ip_address: Optional[str]
    status: str
    details: Optional[Dict[str, Any]]
    current_record_hash: str
    timestamp: datetime

class SecurityAlertResponse(BaseModel):
    alert_id: str
    username: Optional[str]
    alert_type: str
    severity: str
    risk_score: float
    detection_source: str
    reason: str
    is_resolved: bool
    created_at: datetime

# ==================== Evaluation Metrics Schemas ====================
class MetricResponse(BaseModel):
    metric_id: str
    image_id: str
    configuration: str
    entropy: float
    npcr: float
    uaci: float
    h_corr: float
    v_corr: float
    d_corr: float
    encryption_time_ms: float
    decryption_time_ms: float
    original_size_bytes: int
    encrypted_size_bytes: int
    exact_recovery: bool
    evaluated_at: datetime
