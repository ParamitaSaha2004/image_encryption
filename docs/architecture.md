# HICE System Architecture Specification

## 1. High-Level Architectural Pattern
HICE adheres to a layered **Defense-in-Depth** and **Decoupled Service-Oriented Architecture (SOA)**:

1. **Client / Presentation Layer:** React 18, Tailwind CSS, Recharts for scientific analytics, Framer Motion for responsive UI transitions.
2. **API & Orchestration Layer:** FastAPI application providing asynchronous REST endpoints, Pydantic data contract enforcement, and JWT authentication.
3. **Cryptographic Core (Stateless Engine):**
   - **Logistic Map Permutation:** 1D chaotic generator for spatial index shuffling.
   - **Cellular Automata Diffusion:** Rule 30 / Rule 90 lattice updates for pixel diffusion.
   - **AES-256-GCM:** Authenticated symmetric cipher with unique 96-bit nonces.
   - **NIST P-256 ECDH:** Asymmetric key agreement and HKDF session key derivation.
4. **Behavioral AI Sentry:** Unsupervised Scikit-learn Isolation Forest pipeline combined with deterministic rule evaluation.
5. **Persistence Layer:** MySQL 8.0 relational database with normalized relations, foreign keys, and hash-chained audit logs.
6. **Encrypted Vault:** Filesystem vault storing encrypted `.hice` binary packages with zero plaintext at rest.

## 2. Package Binary Format (.hice)
The encrypted file stored on disk follows this strict binary layout:
```text
+---------------------+-------------------+-------------------+-------------------+--------------------+
| 12-byte CSPRNG Nonce | 16-byte GHASH Tag | 4-byte AAD Length | UTF-8 JSON AAD    | Ciphertext Stream  |
+---------------------+-------------------+-------------------+-------------------+--------------------+
```
- Nonce (12 bytes): Unique per encryption.
- Tag (16 bytes): AES-GCM MAC tag.
- AAD: Contains image ID, uploader ID, dimensions $(H, W, C)$, and original SHA-256 checksum.
- Ciphertext: Permuted and diffused image bytes encrypted with AES-256-GCM.
