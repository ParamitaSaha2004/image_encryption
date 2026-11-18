"""
Image Validation Module
Enforces strict file type, magic byte signatures, file size bounds,
and detects corrupted or maliciously disguised image payloads.
"""
from typing import Tuple, Dict, Any
import io
from PIL import Image

# Supported magic byte signatures
MAGIC_SIGNATURES: Dict[str, bytes] = {
    "PNG": b"\x89PNG\r\n\x1a\n",
    "JPEG": b"\xff\xd8\xff",
    "BMP": b"BM"
}

ALLOWED_MIME_TYPES = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/bmp": "BMP",
    "image/x-ms-bmp": "BMP"
}

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MIN_FILE_SIZE = 64  # Bytes

class ImageValidationError(Exception):
    """Custom exception raised when image validation fails."""
    pass

def detect_image_format_from_bytes(file_bytes: bytes) -> str:
    """
    Validates magic byte signatures at the head of the file buffer
    to prevent extension spoofing (e.g., executable disguised as .png).
    """
    if len(file_bytes) < 8:
        raise ImageValidationError("Payload is too small to be a valid image file.")

    if file_bytes.startswith(MAGIC_SIGNATURES["PNG"]):
        return "PNG"
    elif file_bytes.startswith(MAGIC_SIGNATURES["JPEG"]):
        return "JPEG"
    elif file_bytes.startswith(MAGIC_SIGNATURES["BMP"]):
        return "BMP"
    else:
        raise ImageValidationError(
            "Unsupported or unrecognized file header. Only authentic PNG, JPEG, and BMP files are accepted."
        )

def validate_image_payload(file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
    """
    Comprehensive validation:
    1. Size threshold check
    2. Magic bytes signature check
    3. Pillow integrity decode check (detects truncated or corrupt streams)
    4. Dimension sanity checks
    """
    size = len(file_bytes)
    if size < MIN_FILE_SIZE:
        raise ImageValidationError(f"File size ({size} bytes) is below minimum threshold.")
    if size > MAX_FILE_SIZE:
        raise ImageValidationError(f"File size ({size / (1024*1024):.2f} MB) exceeds maximum limit of 50 MB.")

    detected_format = detect_image_format_from_bytes(file_bytes)

    # Attempt decoding with Pillow to ensure data integrity
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()  # Verifies image structure without loading entire pixel matrix
            
            # Re-open because verify() closes the stream
            with Image.open(io.BytesIO(file_bytes)) as loaded_img:
                width, height = loaded_img.size
                format_name = loaded_img.format
                mode = loaded_img.mode

                if width <= 0 or height <= 0:
                    raise ImageValidationError("Invalid image dimensions.")
                if width > 16384 or height > 16384:
                    raise ImageValidationError(f"Image dimensions ({width}x{height}) exceed maximum allowed bound of 16384x16384.")

                # Determine channel count
                channels = 1 if mode in ("L", "1") else 4 if mode in ("RGBA", "CMYK") else 3

                return {
                    "valid": True,
                    "format": detected_format,
                    "width": width,
                    "height": height,
                    "channels": channels,
                    "mode": mode,
                    "size_bytes": size,
                    "filename": original_filename
                }
    except Exception as e:
        if isinstance(e, ImageValidationError):
            raise e
        raise ImageValidationError(f"Corrupted image data or failed decoding: {str(e)}")
