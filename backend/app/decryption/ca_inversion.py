"""
Cellular Automata Diffusion Inversion Module
Provides exact lossless reverse diffusion routines for authorized decryption.
"""
import numpy as np
from typing import Union
from app.encryption.cellular_automata import CellularAutomataDiffuser

class CADecryptor:
    @staticmethod
    def invert(diffused_vector: np.ndarray, seed: Union[bytes, str], rule: int = 30) -> np.ndarray:
        """
        Reconstructs the pre-diffused pixel vector (V_perm) from diffused vector (V_diff)
        by applying the identical deterministic Cellular Automata keystream mask via XOR.
        """
        diffuser = CellularAutomataDiffuser(rule=rule)
        return diffuser.invert_diffuse(diffused_vector, seed)
