-- =====================================================================
-- HICE: Hybrid Intelligent Image Encryption and Secure Sharing System
-- Complete Relational Database Schema (MySQL 8.0+)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS hice_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE hice_db;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS encryption_metrics;
DROP TABLE IF EXISTS security_alerts;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS login_history;
DROP TABLE IF EXISTS access_permissions;
DROP TABLE IF EXISTS image_shares;
DROP TABLE IF EXISTS key_records;
DROP TABLE IF EXISTS image_metadata;
DROP TABLE IF EXISTS encrypted_images;
DROP TABLE IF EXISTS system_settings;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS roles;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Roles Table
CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Users Table
CREATE TABLE users (
    user_id CHAR(36) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    public_key_pem TEXT NULL,
    encrypted_private_key TEXT NULL,
    key_salt VARCHAR(64) NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_users_roles FOREIGN KEY (role_id) REFERENCES roles(role_id) ON DELETE RESTRICT,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Encrypted Images Table
CREATE TABLE encrypted_images (
    image_id CHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    width INT NOT NULL,
    height INT NOT NULL,
    channels INT NOT NULL,
    storage_path VARCHAR(500) NOT NULL UNIQUE,
    original_sha256 CHAR(64) NOT NULL,
    ciphertext_sha256 CHAR(64) NOT NULL,
    nonce_hex VARCHAR(32) NOT NULL,
    auth_tag_hex VARCHAR(32) NOT NULL,
    aad_json JSON NULL,
    uploader_id CHAR(36) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_images_uploader FOREIGN KEY (uploader_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_uploader (uploader_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Image Metadata Table
CREATE TABLE image_metadata (
    metadata_id CHAR(36) PRIMARY KEY,
    image_id CHAR(36) NOT NULL UNIQUE,
    modality VARCHAR(50) NOT NULL DEFAULT 'GENERAL',
    body_part VARCHAR(100) NULL,
    patient_pseudonym VARCHAR(100) NULL,
    acquisition_date DATETIME NULL,
    clinical_notes TEXT NULL,
    CONSTRAINT fk_metadata_image FOREIGN KEY (image_id) REFERENCES encrypted_images(image_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Key Records Table (Wrapped master keys per user)
CREATE TABLE key_records (
    key_record_id CHAR(36) PRIMARY KEY,
    image_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    encrypted_image_key TEXT NOT NULL,
    ephemeral_public_key TEXT NULL,
    key_wrap_nonce VARCHAR(32) NULL,
    key_wrap_tag VARCHAR(32) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_keys_image FOREIGN KEY (image_id) REFERENCES encrypted_images(image_id) ON DELETE CASCADE,
    CONSTRAINT fk_keys_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_image (user_id, image_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Image Shares Table
CREATE TABLE image_shares (
    share_id CHAR(36) PRIMARY KEY,
    image_id CHAR(36) NOT NULL,
    sender_id CHAR(36) NOT NULL,
    receiver_id CHAR(36) NOT NULL,
    encrypted_key_for_receiver TEXT NOT NULL,
    ephemeral_public_key TEXT NULL,
    permission_type VARCHAR(20) NOT NULL DEFAULT 'VIEW',
    expires_at DATETIME NULL,
    is_revoked BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_shares_image FOREIGN KEY (image_id) REFERENCES encrypted_images(image_id) ON DELETE CASCADE,
    CONSTRAINT fk_shares_sender FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_shares_receiver FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_receiver_access (receiver_id, is_revoked, expires_at),
    INDEX idx_sender (sender_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Access Permissions Table
CREATE TABLE access_permissions (
    permission_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NOT NULL UNIQUE,
    can_upload BOOLEAN NOT NULL DEFAULT TRUE,
    can_export_analytics BOOLEAN NOT NULL DEFAULT TRUE,
    max_shares_per_day INT NOT NULL DEFAULT 50,
    is_restricted BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_permissions_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. Login History Table
CREATE TABLE login_history (
    login_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NULL,
    ip_address VARCHAR(50) NULL,
    user_agent VARCHAR(255) NULL,
    status VARCHAR(20) NOT NULL,
    failure_reason VARCHAR(100) NULL,
    attempted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_login_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_user_attempts (user_id, attempted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Audit Logs Table (Hash-Chained)
CREATE TABLE audit_logs (
    log_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id CHAR(36) NULL,
    action VARCHAR(50) NOT NULL,
    target_resource_type VARCHAR(50) NULL,
    target_resource_id VARCHAR(100) NULL,
    ip_address VARCHAR(50) NULL,
    status VARCHAR(20) NOT NULL,
    details_json JSON NULL,
    prev_record_hash CHAR(64) NOT NULL,
    current_record_hash CHAR(64) NOT NULL,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_audit_timestamp (timestamp),
    INDEX idx_audit_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. Security Alerts Table
CREATE TABLE security_alerts (
    alert_id CHAR(36) PRIMARY KEY,
    user_id CHAR(36) NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'LOW',
    risk_score DECIMAL(5,2) NOT NULL,
    detection_source VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    is_resolved BOOLEAN NOT NULL DEFAULT FALSE,
    resolved_by CHAR(36) NULL,
    resolved_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_alerts_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    CONSTRAINT fk_alerts_resolver FOREIGN KEY (resolved_by) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_alerts_unresolved (is_resolved, severity),
    INDEX idx_alerts_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. Encryption Metrics Table
CREATE TABLE encryption_metrics (
    metric_id CHAR(36) PRIMARY KEY,
    image_id CHAR(36) NOT NULL,
    configuration VARCHAR(50) NOT NULL,
    entropy DECIMAL(8,6) NOT NULL,
    npcr DECIMAL(7,4) NOT NULL,
    uaci DECIMAL(7,4) NOT NULL,
    h_corr DECIMAL(8,6) NOT NULL,
    v_corr DECIMAL(8,6) NOT NULL,
    d_corr DECIMAL(8,6) NOT NULL,
    encryption_time_ms DECIMAL(10,2) NOT NULL,
    decryption_time_ms DECIMAL(10,2) NOT NULL,
    original_size_bytes BIGINT NOT NULL,
    encrypted_size_bytes BIGINT NOT NULL,
    exact_recovery BOOLEAN NOT NULL DEFAULT TRUE,
    evaluated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_metrics_image FOREIGN KEY (image_id) REFERENCES encrypted_images(image_id) ON DELETE CASCADE,
    INDEX idx_metrics_image_config (image_id, configuration)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. System Settings Table
CREATE TABLE system_settings (
    setting_key VARCHAR(100) PRIMARY KEY,
    setting_value TEXT NOT NULL,
    description VARCHAR(255) NULL,
    updated_by CHAR(36) NULL,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_settings_updater FOREIGN KEY (updated_by) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
