# HICE – Hybrid Intelligent Image Encryption and Secure Sharing System

[![Research Prototype](https://img.shields.io/badge/Security-AES--256--GCM%20%7C%20ECDH%20%7C%20Chaos%20%7C%20CA-blue.svg)](#)
[![Python](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.10+-brightgreen.svg)](#)
[![React](https://img.shields.io/badge/Frontend-React%2018%20%7C%20TailwindCSS%20%7C%20Vite-61dafb.svg)](#)
[![Database](https://img.shields.io/badge/Database-MySQL%208.0-orange.svg)](#)

## Overview
**HICE** (*Hybrid Intelligent Image Encryption and Secure Sharing System*) is a research-oriented, high-assurance digital image security platform specifically engineered for healthcare diagnostics (medical DICOM, X-rays, MRI, CT scans), biometric records, and sensitive visual assets.

It fuses mathematical pre-cipher transformations (**Chaotic Logistic Maps** for permutation and **Elementary Cellular Automata** for diffusion) with standard **AES-256-GCM** authenticated encryption, **NIST P-256 ECDH** key exchange, **Scikit-learn Isolation Forest** anomaly detection, and **tamper-evident hash-chained audit logging**.

---

## Key Features

1. **Hybrid Cryptographic Engine:**
   - **Chaotic Permutation:** 1D Logistic Map dynamically permutes pixel coordinates, destroying spatial correlation.
   - **Cellular Automata Diffusion:** Reversible Elementary Cellular Automata (Rule 30 & Rule 90) diffuses pixel values across neighbor lattices.
   - **Authenticated Encryption:** AES-256-GCM with unique 96-bit CSPRNG nonces and 128-bit authentication tags to guarantee confidentiality and ciphertext integrity.
   - **Exact Lossless Recovery:** Guaranteed bit-exact reconstruction of diagnostic scans upon authorized decryption.

2. **Secure Asymmetric Key Management:**
   - NIST P-256 Elliptic Curve Diffie-Hellman (ECDH) for authorized sender-receiver key agreement.
   - HKDF-SHA256 for key derivation and session key wrapping.
   - Zero hardcoded keys or unprotected private keys.

3. **Intelligent Security Monitoring:**
   - Hybrid detection engine: Deterministic rule thresholds + unsupervised **Isolation Forest** machine learning.
   - Real-time scoring of anomalous access times, decryption failures, and bulk download bursts.

4. **Security Evaluation & Analytics:**
   - Real-time calculation and visualization of Shannon Entropy, NPCR, UACI, and Horizontal/Vertical/Diagonal correlation.
   - Side-by-side performance comparison across 4 configurations:
     1. AES-256-GCM only
     2. Chaotic Map + AES-256-GCM
     3. Cellular Automata + AES-256-GCM
     4. Full Hybrid (Chaos + CA + AES-256-GCM)

5. **Role-Based Access & Granular Sharing:**
   - Granular permissions: `VIEW`, `DECRYPT`, `DOWNLOAD`.
   - Time-bound expirations and cryptographic revocation.
   - Hash-chained audit logs for indisputable chain-of-custody tracking.

---

## Architecture & Directory Layout

```text
HICE/
  frontend/          # React 18 + Vite + Tailwind CSS + Recharts
  backend/           # FastAPI + PyCryptodome/Cryptography + Scikit-Learn
    app/
      routes/        # REST API endpoints
      encryption/    # Chaotic map, Cellular Automata, AES-GCM
      decryption/    # Inverse diffusion, inverse permutation
      image_processing/ # Ingestion, validation, tensor conversion
      key_management/# ECDH P-256, HKDF, key wrapping
      security/      # RBAC, tampering detection, JWT auth
      ai_monitoring/ # Isolation Forest anomaly detection
      evaluation/    # Entropy, NPCR, UACI, correlation
      database/      # MySQL connection pooling & migrations
      models/        # Pydantic schemas & SQLAlchemy ORM
  database/          # schema.sql and seed.sql
  docs/              # Architecture, API docs, security design, research methodology
```

---

## Quick Start Guide

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Configure your MySQL credentials in .env
python run.py
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 3. Open in VS Code
```bash
code C:\Users\Paramita\.gemini\antigravity\scratch\HICE
```
