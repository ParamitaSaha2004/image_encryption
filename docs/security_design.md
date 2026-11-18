# HICE Cryptographic & Security Design

## 1. Threat Model & Assumptions
HICE models an adversary capable of:
- Intercepting network traffic between client and server (Man-in-the-Middle).
- Gaining read-only access to disk storage or database backups.
- Attempting chosen-plaintext attacks (CPA) and chosen-ciphertext attacks (CCA).
- Modifying ciphertext bits in transit or storage (tampering).
- Attempting credential stuffing or unauthorized sharing access.

## 2. Cryptographic Guardrails
1. **Authenticated Encryption (AEAD):**
   - HICE enforces **AES-256-GCM**.
   - No ciphertext is ever decrypted or surfaced to the user if the 16-byte GHASH tag does not verify.
2. **Nonce Freshness Guarantee:**
   - Every encryption operation invokes `os.urandom(12)` to generate a 96-bit cryptographically secure pseudorandom nonce. Nonce reuse under the same key is mathematically prevented.
3. **Key Agreement via ECDH (NIST P-256):**
   - Public keys are stored in PEM format.
   - Senders and receivers derive shared secrets through scalar multiplication on curve `secp256r1`.
   - HKDF-SHA256 expands the shared secret into encryption and wrapping keys.
4. **Experimental vs. Established Security:**
   - Chaotic maps and Cellular Automata serve as **pre-cipher spatial and statistical scramblers**.
   - AES-GCM guarantees IND-CCA2 confidentiality and integrity.
5. **Tamper-Evident Hash-Chaining:**
   - Audit logs calculate:
     $$\text{Hash}_n = \text{SHA256}(\text{Hash}_{n-1} \parallel \text{LogData}_n)$$
   - Prevents retroactive modification or deletion of activity records by compromised administrators.
