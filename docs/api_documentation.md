# HICE REST API Specification

All endpoints are prefixed with `/api/v1`. Interactive Swagger UI is available at `/docs`.

## 1. Authentication & Users
- `POST /api/v1/auth/register` - Register a new user account.
- `POST /api/v1/auth/login` - Authenticate and receive JWT access token.
- `GET  /api/v1/auth/profile` - Get authenticated user profile and public key.
- `GET  /api/v1/users` - List users (Admin/Clinician directory for sharing).

## 2. Image Management & Encryption
- `POST /api/v1/images/upload` - Upload and validate image (PNG, JPG, BMP).
- `POST /api/v1/crypto/encrypt` - Execute hybrid encryption (Chaos + CA + AES-GCM).
- `POST /api/v1/crypto/decrypt` - Authenticate, verify AEAD tag, and decrypt image.
- `GET  /api/v1/images/{image_id}` - Retrieve encrypted package details & metadata.

## 3. Secure Sharing
- `POST /api/v1/shares` - Create time-limited recipient share with wrapped ECDH key.
- `GET  /api/v1/shares/received` - List images shared with the authenticated user.
- `DELETE /api/v1/shares/{share_id}/revoke` - Revoke future decryption access.

## 4. Evaluation & Analytics
- `GET  /api/v1/evaluation/{image_id}/metrics` - Retrieve entropy, NPCR, UACI, and correlation.
- `POST /api/v1/evaluation/{image_id}/benchmark` - Run 4-way comparative performance benchmark.

## 5. Security & AI Monitoring
- `GET  /api/v1/ai-monitoring/alerts` - List active anomaly alerts and risk scores.
- `POST /api/v1/ai-monitoring/alerts/{alert_id}/resolve` - Mark alert as investigated.
- `GET  /api/v1/audit/logs` - Retrieve tamper-evident hash-chained audit logs.
