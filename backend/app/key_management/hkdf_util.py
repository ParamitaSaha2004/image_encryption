"""
HMAC-based Extract-and-Expand Key Derivation Function (HKDF) Module
Derives cryptographically strong, independent subkeys from an ECDH shared secret
or master session key in accordance with RFC 5869 / NIST SP 800-56C.
"""
from typing import Dict, Optional, Union
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

class HKDFUtil:
    DEFAULT_SALT = b"HICE_STATIC_SALT_NIST_P256_2026"

    @classmethod
    def derive_key(
        cls, 
        input_key_material: bytes, 
        info: bytes, 
        length: int = 32, 
        salt: Optional[bytes] = None
    ) -> bytes:
        """
        Derives a subkey of specified length using HKDF-SHA256.
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=length,
            salt=salt or cls.DEFAULT_SALT,
            info=info
        )
        return hkdf.derive(input_key_material)

    @classmethod
    def derive_session_keys(
        cls, 
        shared_secret: bytes, 
        salt: Optional[bytes] = None
    ) -> Dict[str, bytes]:
        """
        Expands the ECDH shared secret into four cryptographically separated 256-bit subkeys:
        1. K_aes: AES-256-GCM symmetric cipher key
        2. K_chaos: Chaotic Logistic Map parameter seed
        3. K_ca: Cellular Automata diffusion keystream seed
        4. K_wrap: Key wrapping key for sharing permissions
        """
        k_aes = cls.derive_key(
            shared_secret, 
            info=b"hice_aes256_gcm_session_key", 
            length=32, 
            salt=salt
        )
        k_chaos = cls.derive_key(
            shared_secret, 
            info=b"hice_chaotic_logistic_map_seed", 
            length=32, 
            salt=salt
        )
        k_ca = cls.derive_key(
            shared_secret, 
            info=b"hice_cellular_automata_seed", 
            length=32, 
            salt=salt
        )
        k_wrap = cls.derive_key(
            shared_secret, 
            info=b"hice_key_encapsulation_wrap", 
            length=32, 
            salt=salt
        )

        return {
            "aes_key": k_aes,
            "chaos_seed": k_chaos,
            "ca_seed": k_ca,
            "wrap_key": k_wrap
        }
