"""
AES-256-GCM Decryption and Authenticated Verification Module
Wraps authenticated verification and handles integrity breach isolation.
"""
from typing import Optional
from app.encryption.aes_gcm import AES256GCMEngine, TamperingDetectedError, AESGCMError

class AESGCMDecryptor:
    @staticmethod
    def decrypt_and_verify(
        key: bytes, 
        ciphertext: bytes, 
        nonce: bytes, 
        auth_tag: bytes, 
        aad: Optional[bytes] = None
    ) -> bytes:
        """
        Executes authenticated decryption with strict integrity enforcement.
        Aborts with TamperingDetectedError if verification fails.
        """
        return AES256GCMEngine.decrypt(
            key=key, 
            ciphertext=ciphertext, 
            nonce=nonce, 
            auth_tag=auth_tag, 
            aad=aad
        )
