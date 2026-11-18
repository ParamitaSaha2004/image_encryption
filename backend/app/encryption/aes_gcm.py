"""
AES-256-GCM Authenticated Encryption Engine (AEAD)
Implements NIST SP 800-38D compliant Authenticated Encryption with Associated Data.
Guarantees confidentiality, ciphertext integrity, unique 96-bit CSPRNG nonces,
and metadata authentication via 128-bit GHASH authentication tags.
"""
import os
import json
from typing import Tuple, Dict, Any, Optional, Union
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

class AESGCMError(Exception):
    """Exception raised for AES-GCM encryption/decryption failures."""
    pass

class TamperingDetectedError(AESGCMError):
    """Exception raised when ciphertext or AAD authentication verification fails."""
    pass

class AES256GCMEngine:
    KEY_LENGTH_BYTES = 32  # 256 bits
    NONCE_LENGTH_BYTES = 12  # 96 bits (NIST recommendation)
    TAG_LENGTH_BYTES = 16   # 128 bits

    @classmethod
    def generate_key(cls) -> bytes:
        """Generates a cryptographically secure 256-bit symmetric key."""
        return AESGCM.generate_key(bit_length=256)

    @classmethod
    def generate_nonce(cls) -> bytes:
        """
        Generates a fresh, unique 96-bit cryptographically secure pseudorandom nonce (CSPRNG).
        Never reuse a nonce under the same key.
        """
        return os.urandom(cls.NONCE_LENGTH_BYTES)

    @classmethod
    def format_aad(cls, metadata_dict: Dict[str, Any]) -> bytes:
        """
        Serializes metadata into a canonical JSON byte string to serve as Authenticated Associated Data.
        Any modification to metadata will cause decryption authentication to fail.
        """
        # Canonical formatting with sorted keys
        canonical_json = json.dumps(metadata_dict, sort_keys=True, separators=(',', ':'))
        return canonical_json.encode('utf-8')

    @classmethod
    def encrypt(
        cls, 
        key: bytes, 
        plaintext: Union[bytes, bytearray], 
        aad: Optional[bytes] = None, 
        nonce: Optional[bytes] = None
    ) -> Tuple[bytes, bytes, bytes]:
        """
        Encrypts plaintext using AES-256-GCM.
        Returns:
            (ciphertext_bytes, nonce_bytes, auth_tag_bytes)
        """
        if len(key) != cls.KEY_LENGTH_BYTES:
            raise AESGCMError(f"AES-256 key must be exactly {cls.KEY_LENGTH_BYTES} bytes (256 bits).")

        if nonce is None:
            nonce = cls.generate_nonce()
        elif len(nonce) != cls.NONCE_LENGTH_BYTES:
            raise AESGCMError(f"GCM nonce must be exactly {cls.NONCE_LENGTH_BYTES} bytes (96 bits).")

        aesgcm = AESGCM(key)
        
        # PyCryptodome/Cryptography encrypts and appends the 16-byte tag to the ciphertext
        encrypted_with_tag = aesgcm.encrypt(nonce, bytes(plaintext), aad)
        
        ciphertext = encrypted_with_tag[:-cls.TAG_LENGTH_BYTES]
        auth_tag = encrypted_with_tag[-cls.TAG_LENGTH_BYTES:]

        return ciphertext, nonce, auth_tag

    @classmethod
    def decrypt(
        cls, 
        key: bytes, 
        ciphertext: bytes, 
        nonce: bytes, 
        auth_tag: bytes, 
        aad: Optional[bytes] = None
    ) -> bytes:
        """
        Authenticates and decrypts ciphertext using AES-256-GCM.
        If the ciphertext, tag, or AAD has been altered by even a single bit,
        raises TamperingDetectedError and NEVER returns partial plaintext.
        """
        if len(key) != cls.KEY_LENGTH_BYTES:
            raise AESGCMError(f"AES-256 key must be exactly {cls.KEY_LENGTH_BYTES} bytes.")
        if len(nonce) != cls.NONCE_LENGTH_BYTES:
            raise AESGCMError(f"GCM nonce must be exactly {cls.NONCE_LENGTH_BYTES} bytes.")
        if len(auth_tag) != cls.TAG_LENGTH_BYTES:
            raise AESGCMError(f"GCM authentication tag must be exactly {cls.TAG_LENGTH_BYTES} bytes.")

        aesgcm = AESGCM(key)
        # Recombine ciphertext and tag for decryption verification
        payload_with_tag = ciphertext + auth_tag

        try:
            plaintext = aesgcm.decrypt(nonce, payload_with_tag, aad)
            return plaintext
        except InvalidTag:
            raise TamperingDetectedError(
                "CRYPTOGRAPHIC INTEGRITY FAILURE: AES-GCM tag verification failed. "
                "The ciphertext, metadata (AAD), or authentication tag has been tampered with or corrupted. "
                "Plaintext release safely blocked."
            )
        except Exception as e:
            raise AESGCMError(f"Decryption error: {str(e)}")
