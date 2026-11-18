"""
Chaotic Permutation Inversion Module
Provides high-performance inverse permutation routines to recover
the exact original pixel sequence from chaotically permuted arrays.
"""
import numpy as np
from app.encryption.chaotic_map import LogisticMap, ChaoticMapError

class ChaoticInverter:
    @staticmethod
    def recover(permuted_vector: np.ndarray, seed: bytes) -> np.ndarray:
        """
        Reconstructs the original 1D byte vector from permuted vector using the derived seed.
        """
        logistic = LogisticMap.from_seed(seed)
        _, inv_perm = logistic.generate_permutation_indices(len(permuted_vector))
        return permuted_vector[inv_perm]

    @staticmethod
    def recover_with_indices(permuted_vector: np.ndarray, inv_perm: np.ndarray) -> np.ndarray:
        """Directly applies pre-computed inverse permutation indices."""
        return LogisticMap.inverse_permute(permuted_vector, inv_perm)
