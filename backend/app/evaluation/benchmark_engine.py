"""
Security Evaluation & Cryptographic Benchmarking Engine (Phase 11)
Calculates quantitative security and statistical metrics:
- Shannon Information Entropy (H ≈ 7.999)
- Number of Pixels Change Rate (NPCR > 99.6%)
- Unified Average Changing Intensity (UACI > 33.4%)
- Pearson Adjacent Pixel Correlation Coefficients (Horizontal, Vertical, Diagonal)
- 4-Way Comparative Benchmarks (AES Only, Chaos+AES, CA+AES, Full Hybrid)
- Scatter plot and histogram distribution data for frontend rendering
"""
import math
import time
import os
import uuid
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from sqlalchemy.orm import Session

from app.key_management.hkdf_util import HKDFUtil
from app.encryption.chaotic_map import LogisticMap
from app.encryption.cellular_automata import CellularAutomataDiffuser
from app.decryption.ca_inversion import CADecryptor
from app.decryption.chaotic_inversion import ChaoticInverter
from app.encryption.aes_gcm import AES256GCMEngine
from app.encryption.hybrid_pipeline import HybridEncryptionPipeline
from app.decryption.hybrid_decryption import HybridDecryptionPipeline
from app.models.db_models import EncryptionMetric

class SecurityEvaluationEngine:
    @staticmethod
    def calculate_entropy(data_bytes: bytes) -> float:
        """
        Calculates Shannon Information Entropy:
        H = - sum( P(x_i) * log2(P(x_i)) )
        Ideal theoretical value for 8-bit uniform ciphertext is 8.000 bits.
        """
        if not data_bytes:
            return 0.0

        arr = np.frombuffer(data_bytes, dtype=np.uint8)
        total_len = len(arr)
        counts = np.bincount(arr, minlength=256)
        probs = counts / total_len
        
        # Filter non-zero probabilities
        non_zero = probs[probs > 0]
        entropy = -np.sum(non_zero * np.log2(non_zero))
        return float(round(entropy, 6))

    @staticmethod
    def calculate_npcr_uaci(c1_bytes: bytes, c2_bytes: bytes) -> Tuple[float, float]:
        """
        Computes NPCR (Number of Pixels Change Rate) and UACI (Unified Average Changing Intensity)
        between two ciphertexts whose plaintexts differed by 1 bit.
        """
        min_len = min(len(c1_bytes), len(c2_bytes))
        arr1 = np.frombuffer(c1_bytes[:min_len], dtype=np.uint8)
        arr2 = np.frombuffer(c2_bytes[:min_len], dtype=np.uint8)

        # NPCR: Percentage of differing byte positions
        diff = arr1 != arr2
        npcr = (np.sum(diff) / min_len) * 100.0

        # UACI: Normalized absolute intensity divergence
        abs_diff = np.abs(arr1.astype(np.int32) - arr2.astype(np.int32))
        uaci = (np.sum(abs_diff) / (255.0 * min_len)) * 100.0

        return float(round(npcr, 4)), float(round(uaci, 4))

    @staticmethod
    def calculate_correlation(data_2d: np.ndarray, num_samples: int = 2000) -> Dict[str, float]:
        """
        Calculates Pearson correlation coefficients between adjacent pixels:
        Horizontal, Vertical, and Diagonal.
        """
        h, w = data_2d.shape[:2]
        # Flatten if multi-channel to single 2D intensity plane
        if data_2d.ndim == 3:
            grid = data_2d[:, :, 0].astype(np.float64)
        else:
            grid = data_2d.astype(np.float64)

        rng = np.random.default_rng(42)
        samples = min(num_samples, (h - 1) * (w - 1))

        # Horizontal adjacent: (r, c) and (r, c+1)
        r_h = rng.integers(0, h, size=samples)
        c_h = rng.integers(0, w - 1, size=samples)
        x_h = grid[r_h, c_h]
        y_h = grid[r_h, c_h + 1]

        # Vertical adjacent: (r, c) and (r+1, c)
        r_v = rng.integers(0, h - 1, size=samples)
        c_v = rng.integers(0, w, size=samples)
        x_v = grid[r_v, c_v]
        y_v = grid[r_v + 1, c_v]

        # Diagonal adjacent: (r, c) and (r+1, c+1)
        r_d = rng.integers(0, h - 1, size=samples)
        c_d = rng.integers(0, w - 1, size=samples)
        x_d = grid[r_d, c_d]
        y_d = grid[r_d + 1, c_d + 1]

        def pearson(x: np.ndarray, y: np.ndarray) -> float:
            std_x = np.std(x)
            std_y = np.std(y)
            if std_x < 1e-9 or std_y < 1e-9:
                return 0.0
            cov = np.mean((x - np.mean(x)) * (y - np.mean(y)))
            r = cov / (std_x * std_y)
            return float(round(r, 6))

        return {
            "horizontal": pearson(x_h, y_h),
            "vertical": pearson(x_v, y_v),
            "diagonal": pearson(x_d, y_d)
        }

    @classmethod
    def extract_scatter_and_histograms(
        cls,
        original_bytes: bytes,
        cipher_bytes: bytes,
        height: int,
        width: int,
        channels: int,
        num_points: int = 150
    ) -> Dict[str, Any]:
        """
        Generates downsampled scatter plot coordinates and 256-bin histograms
        for high-performance React visualization.
        """
        orig_arr = np.frombuffer(original_bytes, dtype=np.uint8)
        cipher_arr = np.frombuffer(cipher_bytes[:len(orig_arr)], dtype=np.uint8)

        # Reshape to 2D for spatial correlation pairs
        orig_2d = orig_arr[:height*width].reshape(height, width).astype(np.float64)
        ciph_2d = cipher_arr[:height*width].reshape(height, width).astype(np.float64)

        rng = np.random.default_rng(101)
        pts = min(num_points, (height - 1) * (width - 1))

        # Sample horizontal pairs
        rh = rng.integers(0, height, size=pts)
        ch = rng.integers(0, width - 1, size=pts)
        orig_h_pts = [{"x": int(orig_2d[rh[i], ch[i]]), "y": int(orig_2d[rh[i], ch[i]+1])} for i in range(pts)]
        ciph_h_pts = [{"x": int(ciph_2d[rh[i], ch[i]]), "y": int(ciph_2d[rh[i], ch[i]+1])} for i in range(pts)]

        # Sample vertical pairs
        rv = rng.integers(0, height - 1, size=pts)
        cv = rng.integers(0, width, size=pts)
        orig_v_pts = [{"x": int(orig_2d[rv[i], cv[i]]), "y": int(orig_2d[rv[i]+1, cv[i]])} for i in range(pts)]
        ciph_v_pts = [{"x": int(ciph_2d[rv[i], cv[i]]), "y": int(ciph_2d[rv[i]+1, cv[i]])} for i in range(pts)]

        # Histograms (256 bins)
        orig_counts = np.bincount(orig_arr, minlength=256)
        ciph_counts = np.bincount(cipher_arr, minlength=256)

        # Downsample to 32 grouped buckets for compact chart payload
        bucket_size = 8
        buckets = []
        for b in range(32):
            start = b * bucket_size
            end = start + bucket_size
            buckets.append({
                "range": f"{start}-{end-1}",
                "original": int(np.sum(orig_counts[start:end])),
                "ciphertext": int(np.sum(ciph_counts[start:end]))
            })

        return {
            "scatter": {
                "horizontal_original": orig_h_pts,
                "horizontal_cipher": ciph_h_pts,
                "vertical_original": orig_v_pts,
                "vertical_cipher": ciph_v_pts
            },
            "histogram_buckets": buckets
        }

    @classmethod
    def run_4way_comparative_benchmark(
        cls,
        image_id: str,
        pixel_vector: np.ndarray,
        height: int,
        width: int,
        channels: int,
        master_key_bytes: bytes,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        Executes benchmarks across all 4 operational configurations:
        1. AES-256-GCM Only
        2. Chaotic Map + AES-256-GCM
        3. Cellular Automata + AES-256-GCM
        4. Full Hybrid (Chaos + CA + AES-256-GCM)
        """
        subkeys = HKDFUtil.derive_session_keys(master_key_bytes)
        k_chaos = subkeys["chaos_seed"]
        k_ca = subkeys["ca_seed"]
        k_aes = subkeys["aes_key"]

        plain_bytes = pixel_vector.tobytes()
        orig_entropy = cls.calculate_entropy(plain_bytes)
        orig_2d = pixel_vector.reshape(height, width, channels) if pixel_vector.ndim == 1 and channels > 1 else (pixel_vector.reshape(height, width) if pixel_vector.ndim == 1 else pixel_vector)
        orig_corr = cls.calculate_correlation(orig_2d)

        # Key Sensitivity differential testing (1 bit modified in master key)
        key_mod = bytearray(master_key_bytes)
        key_mod[-1] ^= 0x01
        subkeys_mod = HKDFUtil.derive_session_keys(bytes(key_mod))
        k_chaos_mod = subkeys_mod["chaos_seed"]
        k_ca_mod = subkeys_mod["ca_seed"]
        k_aes_mod = subkeys_mod["aes_key"]

        configs = [
            ("AES-256-GCM Only", False, False),
            ("Chaotic Map + AES-256-GCM", True, False),
            ("Cellular Automata + AES-256-GCM", False, True),
            ("Full Hybrid (Chaos + CA + AES-GCM)", True, True)
        ]

        results = []

        for config_name, use_chaos, use_ca in configs:
            # Benchmark Encryption
            t0 = time.perf_counter()
            data_arr = np.frombuffer(plain_bytes, dtype=np.uint8)

            # 1. Chaos Permutation (if enabled)
            inv_perm = None
            if use_chaos:
                logistic = LogisticMap.from_seed(k_chaos)
                data_arr, inv_perm = logistic.permute(data_arr)

            # 2. CA Diffusion (if enabled)
            if use_ca:
                diffuser = CellularAutomataDiffuser(rule=30)
                data_arr, _ = diffuser.diffuse(data_arr, seed=k_ca)

            # 3. AES-256-GCM
            fixed_nonce = b"\x00" * 12  # Fixed nonce for deterministic differential testing
            c1, nonce, tag = AES256GCMEngine.encrypt(k_aes, data_arr.tobytes(), aad=b"hice_benchmark", nonce=fixed_nonce)
            enc_time_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            # Differential Encryption under 1-bit perturbed key (Key Sensitivity / NPCR / UACI)
            data_mod_arr = np.frombuffer(plain_bytes, dtype=np.uint8)
            if use_chaos:
                logistic_mod = LogisticMap.from_seed(k_chaos_mod)
                data_mod_arr, _ = logistic_mod.permute(data_mod_arr)
            if use_ca:
                diffuser_mod = CellularAutomataDiffuser(rule=30)
                data_mod_arr, _ = diffuser_mod.diffuse(data_mod_arr, seed=k_ca_mod)
            c2, _, _ = AES256GCMEngine.encrypt(k_aes_mod, data_mod_arr.tobytes(), aad=b"hice_benchmark", nonce=fixed_nonce)

            # Benchmark Decryption
            t1 = time.perf_counter()
            dec_bytes = AES256GCMEngine.decrypt(k_aes, c1, nonce, tag, aad=b"hice_benchmark")
            dec_arr = np.frombuffer(dec_bytes, dtype=np.uint8)

            if use_ca:
                dec_arr = CADecryptor.invert(dec_arr, seed=k_ca, rule=30)
            if use_chaos:
                dec_arr = ChaoticInverter.recover(dec_arr, seed=k_chaos)
            dec_time_ms = round((time.perf_counter() - t1) * 1000.0, 2)

            exact_recovery = bool(dec_arr.tobytes() == plain_bytes)

            # Statistical Evaluation
            entropy = cls.calculate_entropy(c1)
            npcr, uaci = cls.calculate_npcr_uaci(c1, c2)
            c1_arr = np.frombuffer(c1[:height*width*channels], dtype=np.uint8)
            c1_2d = c1_arr.reshape(height, width, channels) if channels > 1 else c1_arr.reshape(height, width)
            corr = cls.calculate_correlation(c1_2d)

            metric_entry = {
                "configuration": config_name,
                "entropy": entropy,
                "npcr": npcr,
                "uaci": uaci,
                "h_corr": corr["horizontal"],
                "v_corr": corr["vertical"],
                "d_corr": corr["diagonal"],
                "encryption_time_ms": enc_time_ms,
                "decryption_time_ms": dec_time_ms,
                "original_size_bytes": len(plain_bytes),
                "encrypted_size_bytes": len(c1),
                "exact_recovery": exact_recovery
            }
            results.append(metric_entry)

            # Persist to database if Session provided
            if db is not None:
                db_metric = EncryptionMetric(
                    metric_id=str(uuid.uuid4()),
                    image_id=image_id,
                    configuration=config_name,
                    entropy=entropy,
                    npcr=npcr,
                    uaci=uaci,
                    h_corr=corr["horizontal"],
                    v_corr=corr["vertical"],
                    d_corr=corr["diagonal"],
                    encryption_time_ms=enc_time_ms,
                    decryption_time_ms=dec_time_ms,
                    original_size_bytes=len(plain_bytes),
                    encrypted_size_bytes=len(c1),
                    exact_recovery=exact_recovery
                )
                db.add(db_metric)

        if db is not None:
            db.commit()

        # Re-derive sample ciphertext for visual scatter using Full Hybrid configuration
        logistic = LogisticMap.from_seed(k_chaos)
        d_perm, _ = logistic.permute(np.frombuffer(plain_bytes, dtype=np.uint8))
        diffuser = CellularAutomataDiffuser(rule=30)
        d_diff, _ = diffuser.diffuse(d_perm, seed=k_ca)
        ciph_bytes, _, _ = AES256GCMEngine.encrypt(k_aes, d_diff.tobytes(), aad=b"hice")

        visuals = cls.extract_scatter_and_histograms(
            original_bytes=plain_bytes,
            cipher_bytes=ciph_bytes,
            height=height,
            width=width,
            channels=channels
        )

        return {
            "image_id": image_id,
            "original_metrics": {
                "entropy": orig_entropy,
                "h_corr": orig_corr["horizontal"],
                "v_corr": orig_corr["vertical"],
                "d_corr": orig_corr["diagonal"],
            },
            "comparative_benchmarks": results,
            "visualizations": visuals
        }
