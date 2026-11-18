"""
Hybrid Decryption Pipeline Module
Coordinates end-to-end authorized image decryption:
1. Deserializes .hice binary package (Nonce, Tag, AAD, Ciphertext)
2. AES-256-GCM authenticated decryption (verifies Tag and AAD integrity)
3. Cellular Automata inverse diffusion (CADecryptor)
4. Chaotic Logistic Map inverse permutation (ChaoticInverter)
5. Cryptographic SHA-256 pixel checksum verification
6. Exact lossless raster image reconstruction
"""
import time
import json
import base64
import hashlib
import numpy as np
from typing import Dict, Any, Union, Optional

from app.key_management.hkdf_util import HKDFUtil
from app.encryption.aes_gcm import AES256GCMEngine, TamperingDetectedError, AESGCMError
from app.decryption.ca_inversion import CADecryptor
from app.decryption.chaotic_inversion import ChaoticInverter
from app.image_processing.preprocessor import ImagePreprocessor
from app.encryption.hybrid_pipeline import HybridEncryptionPipeline, HybridPipelineError

class CryptographicIntegrityError(HybridPipelineError):
    """Exception raised when decrypted pixel digest does not match original SHA-256."""
    pass

class HybridDecryptionPipeline:
    """
    Executes reverse cryptographic decryption and bit-exact image recovery.
    """
    NONCE_LEN = 12
    TAG_LEN = 16

    @classmethod
    def deserialize_hice_package(cls, package_bytes: bytes) -> Dict[str, Any]:
        """
        Unpacks .hice binary payload into constituent cryptographic components:
        [12-byte Nonce | 16-byte GCM Tag | 4-byte big-endian AAD Length | UTF-8 JSON AAD | Ciphertext Stream]
        """
        min_header_len = cls.NONCE_LEN + cls.TAG_LEN + 4
        if len(package_bytes) < min_header_len:
            raise HybridPipelineError(
                f"Corrupted .hice package: file size ({len(package_bytes)} bytes) is smaller than minimum header ({min_header_len} bytes)."
            )

        offset = 0
        nonce = package_bytes[offset : offset + cls.NONCE_LEN]
        offset += cls.NONCE_LEN

        auth_tag = package_bytes[offset : offset + cls.TAG_LEN]
        offset += cls.TAG_LEN

        aad_len = int.from_bytes(package_bytes[offset : offset + 4], byteorder="big")
        offset += 4

        if len(package_bytes) < offset + aad_len:
            raise HybridPipelineError("Corrupted .hice package: truncated AAD metadata segment.")

        aad_bytes = package_bytes[offset : offset + aad_len]
        offset += aad_len

        ciphertext = package_bytes[offset:]
        if len(ciphertext) == 0:
            raise HybridPipelineError("Corrupted .hice package: missing ciphertext payload.")

        try:
            aad_payload = json.loads(aad_bytes.decode("utf-8"))
        except Exception as e:
            raise HybridPipelineError(f"Corrupted AAD metadata JSON: {str(e)}")

        return {
            "nonce": nonce,
            "auth_tag": auth_tag,
            "aad_bytes": aad_bytes,
            "aad_payload": aad_payload,
            "ciphertext": ciphertext
        }

    @classmethod
    def decrypt_package(
        cls,
        package_bytes: bytes,
        master_key: Union[bytes, str],
        verify_bit_exact: bool = True
    ) -> Dict[str, Any]:
        """
        Executes the atomic 3-stage reverse decryption pipeline:
        .hice package -> AES-256-GCM Auth Decryption -> CA Reverse Diffusion -> Chaos Reverse Permutation -> Exact Image
        """
        # 1. Unpack .hice binary container
        unpacked = cls.deserialize_hice_package(package_bytes)
        nonce = unpacked["nonce"]
        auth_tag = unpacked["auth_tag"]
        aad_bytes = unpacked["aad_bytes"]
        aad_payload = unpacked["aad_payload"]
        ciphertext = unpacked["ciphertext"]

        # 2. Derive cryptographically separated subkeys
        master_key_bytes = HybridEncryptionPipeline.normalize_master_key(master_key)
        subkeys = HKDFUtil.derive_session_keys(master_key_bytes)
        k_aes = subkeys["aes_key"]
        k_chaos = subkeys["chaos_seed"]
        k_ca = subkeys["ca_seed"]

        # 3. Stage 1 Reverse: AES-256-GCM Authenticated Decryption
        # Any alteration to ciphertext, tag, or AAD triggers TamperingDetectedError here
        t0 = time.perf_counter()
        diffused_bytes = AES256GCMEngine.decrypt(
            key=k_aes,
            ciphertext=ciphertext,
            nonce=nonce,
            auth_tag=auth_tag,
            aad=aad_bytes
        )
        t_aes_ms = (time.perf_counter() - t0) * 1000
        diffused_vector = np.frombuffer(diffused_bytes, dtype=np.uint8)

        # 4. Stage 2 Reverse: Cellular Automata Reverse Diffusion
        t1 = time.perf_counter()
        ca_rule = aad_payload.get("ca_rule", 30)
        permuted_vector = CADecryptor.invert(diffused_vector, seed=k_ca, rule=ca_rule)
        t_ca_ms = (time.perf_counter() - t1) * 1000

        # 5. Stage 3 Reverse: Chaotic Logistic Map Inverse Permutation
        t2 = time.perf_counter()
        reconstructed_vector = ChaoticInverter.recover(permuted_vector, seed=k_chaos)
        t_chaos_ms = (time.perf_counter() - t2) * 1000

        t_total_ms = t_aes_ms + t_ca_ms + t_chaos_ms
        total_bytes = int(reconstructed_vector.nbytes)
        total_time_s = max(t_total_ms / 1000.0, 1e-6)
        throughput_mbps = round((total_bytes / (1024.0 * 1024.0)) / total_time_s, 2)

        # 6. Cryptographic Integrity & Bit-Exact Verification
        hasher = hashlib.sha256()
        hasher.update(reconstructed_vector.tobytes())
        reconstructed_sha256 = hasher.hexdigest()
        expected_sha256 = aad_payload.get("original_sha256", "")

        is_bit_exact = (reconstructed_sha256.lower() == expected_sha256.lower())
        if verify_bit_exact and not is_bit_exact:
            raise CryptographicIntegrityError(
                f"INTEGRITY VERIFICATION FAILED: Reconstructed pixel digest ({reconstructed_sha256}) "
                f"does not match AAD digest ({expected_sha256})."
            )

        # 7. Lossless Raster Image Reconstruction
        height = aad_payload["height"]
        width = aad_payload["width"]
        channels = aad_payload["channels"]
        output_format = aad_payload.get("format", "PNG")

        image_bytes = ImagePreprocessor.reconstruct_image(
            vector=reconstructed_vector,
            height=height,
            width=width,
            channels=channels,
            output_format=output_format
        )

        mime_map = {
            "PNG": "image/png",
            "JPEG": "image/jpeg",
            "JPG": "image/jpeg",
            "BMP": "image/bmp"
        }
        mime_type = mime_map.get(output_format.upper(), "image/png")
        base64_encoded = base64.b64encode(image_bytes).decode("ascii")
        data_uri = f"data:{mime_type};base64,{base64_encoded}"

        return {
            "status": "SUCCESS",
            "is_bit_exact": is_bit_exact,
            "original_sha256": expected_sha256,
            "reconstructed_sha256": reconstructed_sha256,
            "dimensions": {
                "width": width,
                "height": height,
                "channels": channels,
                "total_pixels": total_bytes
            },
            "metadata": aad_payload,
            "performance": {
                "aes_gcm_ms": round(t_aes_ms, 2),
                "ca_inverse_ms": round(t_ca_ms, 2),
                "chaos_inverse_ms": round(t_chaos_ms, 2),
                "total_decryption_ms": round(t_total_ms, 2),
                "throughput_mbps": throughput_mbps
            },
            "image_bytes": image_bytes,
            "data_uri": data_uri,
            "mime_type": mime_type
        }
