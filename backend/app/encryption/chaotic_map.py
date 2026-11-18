"""
Chaotic Map Permutation Engine
Implements the 1D Logistic Dynamical System:
    x(n+1) = r * x(n) * (1 - x(n))
Provides deterministic secret-seeded permutation, exact mathematical inversion,
parameter validation, and key sensitivity evaluation.
"""
import numpy as np
import hashlib
from typing import Tuple, Dict, Any, Union

class ChaoticMapError(ValueError):
    """Exception raised for invalid chaotic map parameters or configurations."""
    pass

class LogisticMap:
    """
    High-precision Logistic Map permutation engine for spatial image scrambling.
    """
    MIN_R: float = 3.9000
    MAX_R: float = 4.0000
    TRANSIENT_DISCARD: int = 1000

    def __init__(self, r: float = 3.9999, x0: float = 0.54321):
        self.validate_parameters(r, x0)
        self.r = float(r)
        self.x0 = float(x0)

    @classmethod
    def validate_parameters(cls, r: float, x0: float) -> None:
        """Validates that r and x0 remain strictly within the chaotic regime."""
        if not (cls.MIN_R <= r <= cls.MAX_R):
            raise ChaoticMapError(
                f"Control parameter r={r} is outside the chaotic regime [{cls.MIN_R}, {cls.MAX_R}]."
            )
        if not (0.0 < x0 < 1.0):
            raise ChaoticMapError(
                f"Initial condition x0={x0} must be strictly within interval (0.0, 1.0)."
            )
        # Avoid non-chaotic fixed points
        if abs(x0 - 0.5) < 1e-12 or abs(x0 - (r - 1.0) / r) < 1e-12:
            raise ChaoticMapError(f"Initial condition x0={x0} is an unstable fixed point.")

    @classmethod
    def from_seed(cls, seed: Union[bytes, str]) -> "LogisticMap":
        """
        Deterministically derives high-entropy (r, x0) parameters from a cryptographic seed (e.g. HKDF key).
        Uses SHA-512 to generate 64-bit integers mapped to double-precision floats.
        """
        if isinstance(seed, str):
            seed = seed.encode("utf-8")

        digest = hashlib.sha512(seed).digest()
        
        # Extract 64-bit unsigned integers from digest
        int_x0 = int.from_bytes(digest[:8], byteorder="big")
        int_r = int.from_bytes(digest[8:16], byteorder="big")

        # Map int_x0 to (0.05, 0.95)
        x0 = 0.05 + (int_x0 / (2**64 - 1)) * 0.90

        # Map int_r to [3.9900, 3.9999] (deep within maximal Lyapunov chaos)
        r = 3.9900 + (int_r / (2**64 - 1)) * 0.0099

        return cls(r=r, x0=x0)

    def generate_sequence(self, length: int) -> np.ndarray:
        """
        Generates a sequence of chaotic real numbers of specified length,
        discarding transient states to eliminate boundary artifacts.
        """
        if length <= 0:
            raise ChaoticMapError("Sequence length must be positive.")

        total_iterations = self.TRANSIENT_DISCARD + length
        seq = np.empty(total_iterations, dtype=np.float64)
        
        curr_x = self.x0
        r = self.r

        # Iterative generation with high numerical precision
        for i in range(total_iterations):
            curr_x = r * curr_x * (1.0 - curr_x)
            seq[i] = curr_x

        # Discard initial transient values
        return seq[self.TRANSIENT_DISCARD:]

    def generate_permutation_indices(self, length: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generates forward permutation vector P and inverse permutation vector inv_P of length N.
        P[i] gives the index in the original array that maps to position i.
        inv_P[P[i]] = i for all i in [0, N-1].
        """
        chaotic_seq = self.generate_sequence(length)
        
        # Argsort sorts the chaotic sequence to generate a pseudo-random permutation
        perm_indices = np.argsort(chaotic_seq).astype(np.int64)

        # Invert permutation: inv_perm[perm_indices[i]] = i
        inv_perm = np.empty(length, dtype=np.int64)
        inv_perm[perm_indices] = np.arange(length, dtype=np.int64)

        return perm_indices, inv_perm

    def permute(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Permutes a 1D uint8 array using the chaotic sequence.
        Returns (permuted_array, inverse_permutation_indices).
        """
        if data.ndim != 1:
            raise ChaoticMapError("Data must be a 1D NumPy array.")
        
        length = len(data)
        perm_indices, inv_perm = self.generate_permutation_indices(length)
        
        permuted_data = data[perm_indices]
        return permuted_data, inv_perm

    @staticmethod
    def inverse_permute(permuted_data: np.ndarray, inv_perm: np.ndarray) -> np.ndarray:
        """
        Losslessly recovers the original 1D array using the inverse permutation vector.
        """
        if len(permuted_data) != len(inv_perm):
            raise ChaoticMapError("Permuted data and inverse indices must have identical lengths.")
        
        return permuted_data[inv_perm]

    @classmethod
    def evaluate_sensitivity(cls, base_seed: bytes, delta: float = 1e-14, length: int = 1000) -> Dict[str, Any]:
        """
        Quantifies the butterfly effect (sensitive dependence on initial conditions).
        Compares trajectory x_n against perturbed trajectory (x_n + delta).
        """
        base_map = cls.from_seed(base_seed)
        perturbed_map = cls(r=base_map.r, x0=base_map.x0 + delta)

        seq_a = base_map.generate_sequence(length)
        seq_b = perturbed_map.generate_sequence(length)

        # Pearson correlation between the two trajectories
        mean_a, mean_b = np.mean(seq_a), np.mean(seq_b)
        numerator = np.sum((seq_a - mean_a) * (seq_b - mean_b))
        denom = np.sqrt(np.sum((seq_a - mean_a)**2) * np.sum((seq_b - mean_b)**2))
        correlation = float(numerator / denom) if denom != 0 else 1.0

        # Permutation index discrepancy
        perm_a, _ = base_map.generate_permutation_indices(length)
        perm_b, _ = perturbed_map.generate_permutation_indices(length)
        different_indices_ratio = float(np.sum(perm_a != perm_b) / length)

        return {
            "initial_delta": delta,
            "base_r": base_map.r,
            "base_x0": base_map.x0,
            "trajectory_correlation": correlation,
            "perm_difference_ratio": different_indices_ratio,
            "sample_trajectory_a": seq_a[:20].tolist(),
            "sample_trajectory_b": seq_b[:20].tolist()
        }
