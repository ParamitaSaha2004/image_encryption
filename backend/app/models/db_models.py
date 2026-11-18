"""
SQLAlchemy Database Models for HICE
Implements all normalized entities required for users, images, keys, shares, audit logs, and metrics.
"""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, 
    DateTime, ForeignKey, Numeric, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.database.connection import Base

def generate_uuid():
    return str(uuid.uuid4())

class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), unique=True, nullable=False)  # USER, ADMIN, SUPER_ADMIN
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"), nullable=False)
    public_key_pem = Column(Text, nullable=True)          # ECDH P-256 Public Key (PEM)
    encrypted_private_key = Column(Text, nullable=True)   # Encrypted with user-derived key
    key_salt = Column(String(64), nullable=True)          # Salt for PBKDF2/Argon2
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    role = relationship("Role", back_populates="users")
    uploaded_images = relationship("EncryptedImage", back_populates="uploader")
    sent_shares = relationship("ImageShare", foreign_keys="[ImageShare.sender_id]", back_populates="sender")
    received_shares = relationship("ImageShare", foreign_keys="[ImageShare.receiver_id]", back_populates="receiver")
    audit_logs = relationship("AuditLog", back_populates="user")
    alerts = relationship("SecurityAlert", foreign_keys="[SecurityAlert.user_id]", back_populates="user")

class EncryptedImage(Base):
    __tablename__ = "encrypted_images"

    image_id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    channels = Column(Integer, nullable=False)
    storage_path = Column(String(500), unique=True, nullable=False)
    original_sha256 = Column(String(64), nullable=False)
    ciphertext_sha256 = Column(String(64), nullable=False)
    nonce_hex = Column(String(32), nullable=False)          # 24 hex characters for 12-byte GCM nonce
    auth_tag_hex = Column(String(32), nullable=False)       # 32 hex characters for 16-byte GCM tag
    aad_json = Column(JSON, nullable=True)
    uploader_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    uploader = relationship("User", back_populates="uploaded_images")
    metadata_record = relationship("ImageMetadata", back_populates="image", uselist=False, cascade="all, delete-orphan")
    key_records = relationship("KeyRecord", back_populates="image", cascade="all, delete-orphan")
    shares = relationship("ImageShare", back_populates="image", cascade="all, delete-orphan")
    metrics = relationship("EncryptionMetric", back_populates="image", cascade="all, delete-orphan")

class ImageMetadata(Base):
    __tablename__ = "image_metadata"

    metadata_id = Column(String(36), primary_key=True, default=generate_uuid)
    image_id = Column(String(36), ForeignKey("encrypted_images.image_id", ondelete="CASCADE"), unique=True, nullable=False)
    modality = Column(String(50), default="GENERAL", nullable=False)  # X-RAY, MRI, CT, GENERAL
    body_part = Column(String(100), nullable=True)
    patient_pseudonym = Column(String(100), nullable=True)
    acquisition_date = Column(DateTime, nullable=True)
    clinical_notes = Column(Text, nullable=True)

    image = relationship("EncryptedImage", back_populates="metadata_record")

class KeyRecord(Base):
    __tablename__ = "key_records"

    key_record_id = Column(String(36), primary_key=True, default=generate_uuid)
    image_id = Column(String(36), ForeignKey("encrypted_images.image_id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    encrypted_image_key = Column(Text, nullable=False)      # Wrapped K_master
    ephemeral_public_key = Column(Text, nullable=True)     # ECDH Ephemeral PubKey
    key_wrap_nonce = Column(String(32), nullable=True)
    key_wrap_tag = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    image = relationship("EncryptedImage", back_populates="key_records")

class ImageShare(Base):
    __tablename__ = "image_shares"

    share_id = Column(String(36), primary_key=True, default=generate_uuid)
    image_id = Column(String(36), ForeignKey("encrypted_images.image_id", ondelete="CASCADE"), nullable=False, index=True)
    sender_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    receiver_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    encrypted_key_for_receiver = Column(Text, nullable=False) # Wrapped K_master for Receiver
    ephemeral_public_key = Column(Text, nullable=True)
    permission_type = Column(String(20), default="VIEW", nullable=False) # VIEW, DECRYPT, DOWNLOAD
    expires_at = Column(DateTime, nullable=True, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    image = relationship("EncryptedImage", back_populates="shares")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_shares")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_shares")

class AccessPermission(Base):
    __tablename__ = "access_permissions"

    permission_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    can_upload = Column(Boolean, default=True, nullable=False)
    can_export_analytics = Column(Boolean, default=True, nullable=False)
    max_shares_per_day = Column(Integer, default=50, nullable=False)
    is_restricted = Column(Boolean, default=False, nullable=False)

class LoginHistory(Base):
    __tablename__ = "login_history"

    login_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True, index=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILURE
    failure_reason = Column(String(100), nullable=True)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True, index=True)
    action = Column(String(50), nullable=False)  # UPLOAD, ENCRYPT, DECRYPT, SHARE, REVOKE
    target_resource_type = Column(String(50), nullable=True)
    target_resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    status = Column(String(20), nullable=False)  # SUCCESS, FAILURE, TAMPER_DETECTED
    details_json = Column(JSON, nullable=True)
    prev_record_hash = Column(String(64), nullable=False)
    current_record_hash = Column(String(64), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")

class SecurityAlert(Base):
    __tablename__ = "security_alerts"

    alert_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=True, index=True)
    alert_type = Column(String(50), nullable=False) # BRUTE_FORCE, ANOMALOUS_ACCESS, DECRYPTION_FAILURES, TAMPERING
    severity = Column(String(20), default="LOW", nullable=False) # LOW, MEDIUM, HIGH, CRITICAL
    risk_score = Column(Numeric(5, 2), nullable=False)           # 0.00 to 100.00
    detection_source = Column(String(50), nullable=False)        # RULE_BASED, ISOLATION_FOREST
    reason = Column(Text, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False, index=True)
    resolved_by = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="alerts")

class EncryptionMetric(Base):
    __tablename__ = "encryption_metrics"

    metric_id = Column(String(36), primary_key=True, default=generate_uuid)
    image_id = Column(String(36), ForeignKey("encrypted_images.image_id", ondelete="CASCADE"), nullable=False, index=True)
    configuration = Column(String(50), nullable=False) # AES_ONLY, CHAOS_AES, CA_AES, HYBRID_ALL
    entropy = Column(Numeric(8, 6), nullable=False)
    npcr = Column(Numeric(7, 4), nullable=False)
    uaci = Column(Numeric(7, 4), nullable=False)
    h_corr = Column(Numeric(8, 6), nullable=False)
    v_corr = Column(Numeric(8, 6), nullable=False)
    d_corr = Column(Numeric(8, 6), nullable=False)
    encryption_time_ms = Column(Numeric(10, 2), nullable=False)
    decryption_time_ms = Column(Numeric(10, 2), nullable=False)
    original_size_bytes = Column(BigInteger, nullable=False)
    encrypted_size_bytes = Column(BigInteger, nullable=False)
    exact_recovery = Column(Boolean, default=True, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    image = relationship("EncryptedImage", back_populates="metrics")

class SystemSetting(Base):
    __tablename__ = "system_settings"

    setting_key = Column(String(100), primary_key=True)
    setting_value = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    updated_by = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
