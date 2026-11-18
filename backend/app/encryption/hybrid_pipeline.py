"""
Hybrid Encryption Pipeline Module
Coordinates end-to-end forward encryption:
1. Ingestion pixel vector (V)
2. Chaotic Logistic Map Permutation (V_perm)
3. Cellular Automata Diffusion (V_diff)
4. AES-256-GCM AEAD Authenticated Encryption (C, Nonce, Tag, AAD)
5. Packaging into standardized .hice binary format
"""
import time
import os
import json
import hashlib
import numpy as np
from typing import Dict, Any, Union, Tuple, Optional

from app.key_management.hkdf_util import HKDFUtil
from app.encryption.chaotic_map import LogisticMap, ChaoticMapError
from app.encryption.cellular_automata import CellularAutomataDiffuser, CAError
from app.encryption.aes_gcm import AES256GCMEngine, AESGCMError

class HybridPipelineError(Exception):
    """Exception raised for hybrid encryption pipeline errors."""
    pass

class HybridEncryptionPipeline:
    """
    Orchestrates the multi-layered HICE encryption workflow.
    """
    NONCE_LEN = 12
    TAG_LEN = 16

    @staticmethod
    def normalize_master_key(master_key: Union[bytes, str]) -> bytes:
        """
        Normalizes a string passphrase or byte sequence into a secure 256-bit (32-byte) key.
        """
        if isinstance(master_key, str):
            # If valid 64-char hex string, decode directly
            if len(master_key) == 64:
                try:
                    return bytes.fromhex(master_key)
                except ValueError:
                    pass
            return hashlib.sha256(master_key.encode("utf-8")).digest()
        elif isinstance(master_key, (bytes, bytearray)):
            if len(master_key) == 32:
                return bytes(master_key)
            return hashlib.sha256(master_key).digest()
        else:
            raise HybridPipelineError(f"Unsupported key format: {type(master_key)}. Must be str or bytes.")

    @classmethod
    def serialize_hice_package(
        cls, 
        nonce: bytes, 
        auth_tag: bytes, 
        aad_bytes: bytes, 
        ciphertext: bytes
    ) -> bytes:
        """
        Serializes encryption outputs into the standardized .hice binary package format:
        [12-byte Nonce | 16-byte GCM Tag | 4-byte big-endian AAD Length | UTF-8 JSON AAD | Ciphertext Stream]
        """
        if len(nonce) != cls.NONCE_LEN:
            raise HybridPipelineError(f"Nonce must be exactly {cls.NONCE_LEN} bytes.")
        if len(auth_tag) != cls.TAG_LEN:
            raise HybridPipelineError(f"Authentication tag must be exactly {cls.TAG_LEN} bytes.")

        aad_len = len(aad_bytes)
        aad_len_bytes = aad_len.to_bytes(4, byteorder="big")

        return nonce + auth_tag + aad_len_bytes + aad_bytes + ciphertext

    @classmethod
    def encrypt_vector(
        cls,
        vector: np.ndarray,
        metadata: Dict[str, Any],
        master_key: Union[bytes, str],
        ca_rule: int = 30
    ) -> Dict[str, Any]:
        """
        Executes the atomic 3-stage forward encryption pipeline:
        Pixel Vector -> Chaos Permutation -> CA Diffusion -> AES-256-GCM AEAD -> .hice package
        """
        if vector.ndim != 1 or vector.dtype != np.uint8:
            vector = np.ascontiguousarray(vector, dtype=np.uint8).flatten()

        total_bytes = int(vector.nbytes)
        if total_bytes == 0:
            raise HybridPipelineError("Cannot encrypt an empty vector.")

        # 1. Normalize master secret & derive cryptographic subkeys
        master_key_bytes = cls.normalize_master_key(master_key)
        subkeys = HKDFUtil.derive_session_keys(master_key_bytes)
        k_aes = subkeys["aes_key"]
        k_chaos = subkeys["chaos_seed"]
        k_ca = subkeys["ca_seed"]

        # 2. Stage 1: Chaotic Permutation (Logistic Map)
        t0 = time.perf_counter()
        logistic = LogisticMap.from_seed(k_chaos)
        permuted_vector, _ = logistic.permute(vector)
        t_chaos_ms = (time.perf_counter() - t0) * 1000

        # 3. Stage 2: Cellular Automata Diffusion (Rule 30 or 90)
        t1 = time.perf_counter()
        diffuser = CellularAutomataDiffuser(rule=ca_rule)
        diffused_vector, _ = diffuser.diffuse(permuted_vector, seed=k_ca)
        t_ca_ms = (time.perf_counter() - t1) * 1000

        # 4. Stage 3: AES-256-GCM AEAD Encryption
        # Prepare Associated Authenticated Data (AAD)
        aad_payload = {
            "image_id": metadata.get("image_id", "ANONYMOUS"),
            "title": metadata.get("title", "Untitled Scan"),
            "original_filename": metadata.get("original_filename", "scan.png"),
            "width": int(metadata.get("width", 0)),
            "height": int(metadata.get("height", 0)),
            "channels": int(metadata.get("channels", 1)),
            "total_pixels": total_bytes,
            "original_sha256": metadata.get("original_sha256", ""),
            "format": metadata.get("format", "PNG"),
            "ca_rule": ca_rule,
            "clinical": metadata.get("clinical", {}),
            "encryption_timestamp": metadata.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        aad_bytes = AES256GCMEngine.format_aad(aad_payload)

        t2 = time.perf_counter()
        ciphertext, nonce, auth_tag = AES256GCMEngine.encrypt(
            key=k_aes,
            plaintext=diffused_vector.tobytes(),
            aad=aad_bytes
        )
        t_aes_ms = (time.perf_counter() - t2) * 1000

        t_total_ms = t_chaos_ms + t_ca_ms + t_aes_ms
        total_time_s = max(t_total_ms / 1000.0, 1e-6)
        throughput_mbps = round((total_bytes / (1024.0 * 1024.0)) / total_time_s, 2)

        # 5. Serialize into .hice binary package
        package_bytes = cls.serialize_hice_package(nonce, auth_tag, aad_bytes, ciphertext)
        ciphertext_sha256 = hashlib.sha256(ciphertext).hexdigest()

        return {
            "status": "SUCCESS",
            "package_bytes": package_bytes,
            "ciphertext": ciphertext,
            "nonce": nonce,
            "nonce_hex": nonce.hex(),
            "auth_tag": auth_tag,
            "auth_tag_hex": auth_tag.hex(),
            "aad_payload": aad_payload,
            "aad_bytes": aad_bytes,
            "ciphertext_sha256": ciphertext_sha256,
            "package_size_bytes": len(package_bytes),
            "performance": {
                "chaos_permutation_ms": round(t_chaos_ms, 2),
                "ca_diffusion_ms": round(t_ca_ms, 2),
                "aes_gcm_ms": round(t_aes_ms, 2),
                "total_encryption_ms": round(t_total_ms, 2),
                "throughput_mbps": throughput_mbps
            },
            "subkeys_preview": {
                "aes_key_id": hashlib.sha256(k_aes).hexdigest()[:16],
                "chaos_seed_id": hashlib.sha256(k_chaos).hexdigest()[:16],
                "ca_seed_id": hashlib.sha256(k_ca).hexdigest()[:16]
            }
        }
