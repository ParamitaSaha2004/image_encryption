"""
Cellular Automata Reversible Diffusion Engine
Implements 1D Elementary Cellular Automata (ECA) for Rule 30 and Rule 90.
Generates secret-derived deterministic diffusion masks and provides
guaranteed bit-exact reversible XOR-based pixel diffusion.
"""
import numpy as np
import hashlib
from typing import Tuple, Dict, Any, Union

class CAError(ValueError):
    """Exception raised for invalid Cellular Automata parameters."""
    pass

class CellularAutomataDiffuser:
    """
    Elementary Cellular Automata (ECA) Diffusion Engine supporting Rule 30 and Rule 90.
    """
    SUPPORTED_RULES = (30, 90)

    def __init__(self, rule: int = 30):
        if rule not in self.SUPPORTED_RULES:
            raise CAError(f"Unsupported rule: {rule}. Supported rules are {self.SUPPORTED_RULES}.")
        self.rule = rule

    @staticmethod
    def _apply_rule_30(left: np.ndarray, center: np.ndarray, right: np.ndarray) -> np.ndarray:
        """
        Rule 30 transition: s_i^(t+1) = left ^ (center | right)
        Exhibits Class 3 chaotic, aperiodic, pseudo-random behavior.
        """
        return np.bitwise_xor(left, np.bitwise_or(center, right))

    @staticmethod
    def _apply_rule_90(left: np.ndarray, center: np.ndarray, right: np.ndarray) -> np.ndarray:
        """
        Rule 90 transition: s_i^(t+1) = left ^ right
        Exhibits Class 3 additive linear diffusion (Sierpinski fractal lattice).
        """
        return np.bitwise_xor(left, right)

    def evolve_step(self, lattice: np.ndarray) -> np.ndarray:
        """
        Evolves a 1D binary lattice (uint8 array containing 0s and 1s) by one time step
        using periodic (circular) boundary conditions.
        """
        # Periodic circular shifts: left neighbor is rolled right, right neighbor rolled left
        left = np.roll(lattice, 1)
        center = lattice
        right = np.roll(lattice, -1)

        if self.rule == 30:
            return self._apply_rule_30(left, center, right)
        elif self.rule == 90:
            return self._apply_rule_90(left, center, right)
        else:
            raise CAError(f"Unimplemented rule: {self.rule}")

    @classmethod
    def generate_keystream_mask(
        cls, 
        length: int, 
        seed: Union[bytes, str], 
        rule: int = 30, 
        warmup_steps: int = 128
    ) -> np.ndarray:
        """
        Generates a deterministic pseudo-random keystream mask M of specified length (in bytes).
        The seed initializes an initial binary lattice via SHA-512 hashing, which is evolved
        under the specified ECA rule. Bits are packed into uint8 bytes.
        """
        if length <= 0:
            raise CAError("Keystream mask length must be positive.")
        if rule not in cls.SUPPORTED_RULES:
            raise CAError(f"Unsupported rule: {rule}. Choose 30 or 90.")

        if isinstance(seed, str):
            seed = seed.encode("utf-8")

        # Lattice width: must be at least 512 bits to prevent short cycles
        lattice_bits = max(512, (length * 8) // 16)
        # Pad to multiple of 64 bits
        if lattice_bits % 64 != 0:
            lattice_bits += 64 - (lattice_bits % 64)

        # Expand seed into initial binary lattice using SHA-512 HKDF-style extraction
        hasher = hashlib.sha512()
        hasher.update(seed + b"_ca_init")
        digest = hasher.digest()
        
        # Tile digest to fill lattice width
        needed_bytes = lattice_bits // 8
        full_seed_bytes = (digest * ((needed_bytes // len(digest)) + 1))[:needed_bytes]
        
        # Unpack bytes into 1D binary array (0s and 1s)
        unpacked_bits = np.unpackbits(np.frombuffer(full_seed_bytes, dtype=np.uint8))
        lattice = unpacked_bits.copy()

        diffuser = cls(rule=rule)

        # Warm-up phase: evolve lattice to eliminate initial seeding bias
        for _ in range(warmup_steps):
            lattice = diffuser.evolve_step(lattice)

        # Generate bits until we have enough to pack into `length` bytes
        total_bits_needed = length * 8
        collected_bits = []
        bits_count = 0

        while bits_count < total_bits_needed:
            lattice = diffuser.evolve_step(lattice)
            collected_bits.append(lattice)
            bits_count += len(lattice)

        all_bits = np.concatenate(collected_bits)[:total_bits_needed]
        # Pack bits into contiguous uint8 byte array
        mask = np.packbits(all_bits)[:length]
        return mask

    def diffuse(
        self, 
        data: np.ndarray, 
        seed: Union[bytes, str]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Executes forward diffusion on a 1D uint8 array using reversible XOR operations.
        Returns (diffused_data, mask).
        """
        if data.ndim != 1 or data.dtype != np.uint8:
            raise CAError("Data must be a 1D uint8 NumPy array.")

        mask = self.generate_keystream_mask(len(data), seed, rule=self.rule)
        # Reversible bitwise XOR: V_diff = V_perm ^ M
        diffused_data = np.bitwise_xor(data, mask)
        return diffused_data, mask

    def invert_diffuse(
        self, 
        diffused_data: np.ndarray, 
        seed: Union[bytes, str]
    ) -> np.ndarray:
        """
        Reconstructs original data by applying identical keystream mask via XOR:
        (A ^ M) ^ M = A.
        """
        if diffused_data.ndim != 1 or diffused_data.dtype != np.uint8:
            raise CAError("Diffused data must be a 1D uint8 NumPy array.")

        mask = self.generate_keystream_mask(len(diffused_data), seed, rule=self.rule)
        # Reversible bitwise XOR
        recovered_data = np.bitwise_xor(diffused_data, mask)
        return recovered_data

    @classmethod
    def evaluate_avalanche_effect(
        cls, 
        length: int = 1000, 
        rule: int = 30
    ) -> Dict[str, Any]:
        """
        Measures the Avalanche Effect: When a single input bit is flipped in the seed,
        what percentage of bits flip in the resulting diffusion mask?
        Ideal cryptographic diffusion targets ~50% bit flip rate.
        """
        seed1 = b"HICE_SECURE_KEYSTREAM_SEED_ALPHA"
        # Flip 1 bit in seed (change last byte from 'A' to 'B')
        seed2 = b"HICE_SECURE_KEYSTREAM_SEED_ALPHB"

        mask1 = cls.generate_keystream_mask(length, seed1, rule=rule)
        mask2 = cls.generate_keystream_mask(length, seed2, rule=rule)

        bits1 = np.unpackbits(mask1)
        bits2 = np.unpackbits(mask2)

        flipped_bits = int(np.sum(bits1 != bits2))
        total_bits = len(bits1)
        avalanche_percentage = (flipped_bits / total_bits) * 100.0

        # Measure byte entropy of mask
        counts = np.bincount(mask1, minlength=256)
        probs = counts[counts > 0] / len(mask1)
        entropy = -np.sum(probs * np.log2(probs))

        return {
            "rule": rule,
            "mask_length_bytes": length,
            "total_bits_evaluated": total_bits,
            "bits_flipped": flipped_bits,
            "avalanche_percentage": round(avalanche_percentage, 2),
            "shannon_entropy": round(float(entropy), 4),
            "ideal_entropy": 8.0000,
            "ideal_avalanche": 50.00
        }
