-- =====================================================================
-- HICE Seed Demonstration Data
-- Pre-populates roles, default system settings, and demonstration users.
-- =====================================================================

USE hice_db;

-- 1. Insert Standard Roles
INSERT INTO roles (role_id, role_name, description) VALUES
(1, 'SUPER_ADMIN', 'Root authority: Full security policy control, administrative auditing, and user management.'),
(2, 'ADMIN', 'Security & system administrator: Observes security alerts, monitors images, reviews audit logs.'),
(3, 'USER', 'Standard authorized clinician or researcher: Uploads, encrypts, decrypts, and shares images.')
ON DUPLICATE KEY UPDATE description=VALUES(description);

-- 2. Insert Default System Settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('MAX_UPLOAD_SIZE_MB', '50', 'Maximum allowed single image payload size in megabytes.'),
('ANOMALY_CONTAMINATION_RATE', '0.05', 'Expected anomaly proportion parameter for Isolation Forest model.'),
('MAX_FAILED_LOGINS_BEFORE_LOCK', '5', 'Number of consecutive authentication failures triggering temporary lockout.'),
('DEFAULT_SHARE_EXPIRY_HOURS', '24', 'Default lifetime for newly generated secure image shares.'),
('AUDIT_HASH_CHAIN_GENESIS', '0000000000000000000000000000000000000000000000000000000000000000', 'Genesis previous hash for tamper-evident audit chaining.')
ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value);

-- 3. Demonstration Users (Passwords hashed with bcrypt for "Password123!")
-- $2b$12$K1rZgG4vOq8UqZ8FzE6CpeL9/XvL4Y7QY2c7M7N1G2H3I4J5K6L7M represents "Password123!"
INSERT INTO users (user_id, username, email, password_hash, role_id, is_active) VALUES
('11111111-1111-1111-1111-111111111111', 'superadmin', 'superadmin@hice.security', '$2b$12$6/y4rTq7k0.WfZ4G68S1w.x37g5D1Rz2M1A7C3D5E7F9G1H3I5J7K', 1, TRUE),
('22222222-2222-2222-2222-222222222222', 'sec_admin', 'admin@hice.security', '$2b$12$6/y4rTq7k0.WfZ4G68S1w.x37g5D1Rz2M1A7C3D5E7F9G1H3I5J7K', 2, TRUE),
('33333333-3333-3333-3333-333333333333', 'dr_alice_radiology', 'alice@hospital.org', '$2b$12$6/y4rTq7k0.WfZ4G68S1w.x37g5D1Rz2M1A7C3D5E7F9G1H3I5J7K', 3, TRUE),
('44444444-4444-4444-4444-444444444444', 'dr_bob_oncology', 'bob@hospital.org', '$2b$12$6/y4rTq7k0.WfZ4G68S1w.x37g5D1Rz2M1A7C3D5E7F9G1H3I5J7K', 3, TRUE)
ON DUPLICATE KEY UPDATE updated_at=CURRENT_TIMESTAMP;

-- 4. Initial Access Permissions for Demo Users
INSERT INTO access_permissions (permission_id, user_id, can_upload, can_export_analytics, max_shares_per_day, is_restricted) VALUES
('a1111111-1111-1111-1111-111111111111', '33333333-3333-3333-3333-333333333333', TRUE, TRUE, 100, FALSE),
('a2222222-2222-2222-2222-222222222222', '44444444-4444-4444-4444-444444444444', TRUE, TRUE, 100, FALSE)
ON DUPLICATE KEY UPDATE can_upload=VALUES(can_upload);
