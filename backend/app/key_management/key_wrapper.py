"""
NIST P-256 ECDH Key Encapsulation & Key Wrapping Module
Implements recipient-specific symmetric key wrapping:
Sender generates ephemeral ECDH keypair -> computes shared secret Z with Receiver public key ->
derives K_wrap via HKDF-SHA256 -> encrypts master image key K_master via AES-256-GCM AEAD.
Receiver decapsulates K_master using their private key and the ephemeral public key.
"""
import json
import base64
import os
from typing import Dict, Any, Tuple
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from app.key_management.ecdh_manager import ECDHManager, ECDHError
from app.key_management.hkdf_util import HKDFUtil
from app.encryption.aes_gcm import AES256GCMEngine, TamperingDetectedError, AESGCMError

class KeyWrapError(Exception):
    """Exception raised for key wrapping or decapsulation errors."""
    pass

class KeyWrapper:
    WRAP_INFO = b"hice_key_encapsulation_wrap"

    @classmethod
    def encapsulate_key(
        cls,
        recipient_public_key_pem: str,
        plaintext_key: bytes,
        aad_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Encapsulates a symmetric master key (K_master) for a specific recipient:
        1. Generates ephemeral keypair (d_eph, Q_eph).
        2. Computes shared secret Z = d_eph · Q_recipient.
        3. Derives K_wrap via HKDF-SHA256.
        4. Encrypts plaintext_key with AES-256-GCM bound to AAD metadata.
        Returns:
            ephemeral_public_key_pem, encrypted_bundle (JSON string with nonce, tag, ciphertext)
        """
        if not recipient_public_key_pem:
            raise KeyWrapError("Recipient public key PEM is required.")
        if len(plaintext_key) != 32:
            raise KeyWrapError("Plaintext key to wrap must be exactly 32 bytes (256 bits).")

        try:
            recipient_pub = ECDHManager.load_public_key(recipient_public_key_pem)
        except Exception as e:
            raise KeyWrapError(f"Invalid recipient public key: {str(e)}")

        # 1. Ephemeral keypair
        eph_pub_pem, eph_priv_pem = ECDHManager.generate_keypair()
        eph_priv = ECDHManager.load_private_key(eph_priv_pem)

        # 2. Shared secret Z
        shared_secret = ECDHManager.compute_shared_secret(eph_priv, recipient_pub)

        # 3. Derive K_wrap
        k_wrap = HKDFUtil.derive_key(
            input_key_material=shared_secret,
            info=cls.WRAP_INFO,
            length=32
        )

        # 4. Authenticated AES-256-GCM key wrapping
        aad_bytes = AES256GCMEngine.format_aad(aad_metadata)
        ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(
            key=k_wrap,
            plaintext=plaintext_key,
            aad=aad_bytes
        )

        bundle = {
            "ciphertext_hex": ciphertext.hex(),
            "nonce_hex": nonce.hex(),
            "auth_tag_hex": auth_tag.hex()
        }

        return {
            "ephemeral_public_key_pem": eph_pub_pem,
            "encrypted_key_bundle": json.dumps(bundle, separators=(',', ':')),
            "key_wrap_nonce_hex": nonce.hex(),
            "key_wrap_tag_hex": auth_tag.hex()
        }

    @classmethod
    def decapsulate_key(
        cls,
        recipient_private_key_pem: str,
        ephemeral_public_key_pem: str,
        encrypted_key_bundle_json: str,
        aad_metadata: Dict[str, Any]
    ) -> bytes:
        """
        Decapsulates the symmetric master key using recipient's private key:
        1. Computes shared secret Z = d_recipient · Q_eph.
        2. Derives K_wrap via HKDF-SHA256.
        3. Decrypts and authenticates wrapped key using AES-256-GCM.
        Returns:
            Unwrapped 32-byte master key.
        """
        try:
            recipient_priv = ECDHManager.load_private_key(recipient_private_key_pem)
            eph_pub = ECDHManager.load_public_key(ephemeral_public_key_pem)
        except Exception as e:
            raise KeyWrapError(f"Failed to load keys for decapsulation: {str(e)}")

        # 1. Reconstruct identical shared secret Z
        shared_secret = ECDHManager.compute_shared_secret(recipient_priv, eph_pub)

        # 2. Derive identical K_wrap
        k_wrap = HKDFUtil.derive_key(
            input_key_material=shared_secret,
            info=cls.WRAP_INFO,
            length=32
        )

        # 3. Parse encrypted bundle
        try:
            bundle = json.loads(encrypted_key_bundle_json)
            ciphertext = bytes.fromhex(bundle["ciphertext_hex"])
            nonce = bytes.fromhex(bundle["nonce_hex"])
            auth_tag = bytes.fromhex(bundle["auth_tag_hex"])
        except Exception as e:
            raise KeyWrapError(f"Malformed encrypted key bundle: {str(e)}")

        # 4. Authenticated AES-256-GCM Decryption
        aad_bytes = AES256GCMEngine.format_aad(aad_metadata)
        try:
            plaintext_key = AES256GCMEngine.decrypt(
                key=k_wrap,
                ciphertext=ciphertext,
                nonce=nonce,
                auth_tag=auth_tag,
                aad=aad_bytes
            )
            return plaintext_key
        except TamperingDetectedError as e:
            raise KeyWrapError(f"Key decapsulation authentication failed: {str(e)}")
        except Exception as e:
            raise KeyWrapError(f"Decapsulation failed: {str(e)}")
