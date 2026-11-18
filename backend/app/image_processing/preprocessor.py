"""
Image Preprocessing and Tensor Normalization Module
Transforms image inputs into standardized NumPy 1D byte vectors,
calculates cryptographic SHA-256 digests, and guarantees bit-exact reconstruction.
"""
import io
import hashlib
import numpy as np
from PIL import Image
from typing import Dict, Any, Tuple
from app.image_processing.validator import validate_image_payload, ImageValidationError

class ImagePreprocessor:
    @staticmethod
    def process(file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Validates, normalizes, and serializes an image into an exact 1D uint8 array.
        Computes SHA-256 checksum of raw pixel data to serve as cryptographic proof of integrity.
        """
        val_info = validate_image_payload(file_bytes, original_filename)
        
        with Image.open(io.BytesIO(file_bytes)) as img:
            # Normalize image modes:
            # Grayscale ("L", "1") -> 1 channel
            # RGB ("RGB") -> 3 channels
            # RGBA ("RGBA") -> converted to 3-channel RGB with white background
            if img.mode in ("L", "1"):
                normalized_img = img.convert("L")
                channels = 1
            elif img.mode == "RGBA":
                # Create white background to avoid transparent pixel artifacts
                background = Image.new("RGB", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                normalized_img = background
                channels = 3
            else:
                normalized_img = img.convert("RGB")
                channels = 3

            width, height = normalized_img.size
            img_array = np.array(normalized_img, dtype=np.uint8)

            # Ensure 3D shape: (Height, Width, Channels)
            if channels == 1 and img_array.ndim == 2:
                img_array = np.expand_dims(img_array, axis=-1)

            # Flatten into a contiguous 1D byte vector
            flat_vector = img_array.flatten()
            total_bytes = flat_vector.nbytes

            # Calculate SHA-256 hash of the exact pixel array
            hasher = hashlib.sha256()
            hasher.update(flat_vector.tobytes())
            original_sha256 = hasher.hexdigest()

            return {
                "vector": flat_vector,
                "original_bytes": file_bytes,
                "height": height,
                "width": width,
                "channels": channels,
                "total_bytes": total_bytes,
                "original_sha256": original_sha256,
                "format": val_info["format"],
                "filename": original_filename,
                "shape": (height, width, channels)
            }

    @staticmethod
    def reconstruct_image(vector: np.ndarray, height: int, width: int, channels: int, output_format: str = "PNG") -> bytes:
        """
        Losslessly reconstructs an image byte stream from a 1D pixel vector and dimension parameters.
        Guarantees bit-exact pixel matching against original preprocessed array.
        """
        expected_size = height * width * channels
        if vector.size != expected_size:
            raise ImageValidationError(
                f"Vector size ({vector.size}) does not match expected dimensions ({height}x{width}x{channels} = {expected_size})"
            )

        if channels == 1:
            reshaped = vector.reshape((height, width)).astype(np.uint8)
            img = Image.fromarray(reshaped, mode="L")
        elif channels == 3:
            reshaped = vector.reshape((height, width, 3)).astype(np.uint8)
            img = Image.fromarray(reshaped, mode="RGB")
        elif channels == 4:
            reshaped = vector.reshape((height, width, 4)).astype(np.uint8)
            img = Image.fromarray(reshaped, mode="RGBA")
        else:
            raise ImageValidationError(f"Unsupported channel count: {channels}")

        out_buffer = io.BytesIO()
        img.save(out_buffer, format=output_format)
        return out_buffer.getvalue()
