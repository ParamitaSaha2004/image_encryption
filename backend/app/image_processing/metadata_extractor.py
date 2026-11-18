"""
Image Metadata Extraction & Sanitization Module
Isolates clinical metadata (modality, body part, pseudonym) and sanitizes
raw EXIF headers to prevent out-of-band data leakage or privacy breaches.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from PIL import Image, ExifTags
import io

class MetadataSanitizer:
    @staticmethod
    def extract_and_sanitize(file_bytes: bytes, clinical_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Extracts safe diagnostic metadata, sanitizes tracking EXIF tags,
        and constructs the structured clinical record.
        """
        raw_exif_data = {}
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                exif = img.getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        # Only keep safe non-identifying technical metadata
                        if tag_name in ("Make", "Model", "Software", "DateTime", "Orientation"):
                            raw_exif_data[tag_name] = str(value)
        except Exception:
            pass  # Non-JPEG/PNG or unreadable EXIF safely skipped

        clinical = clinical_input or {}
        
        return {
            "modality": clinical.get("modality", "GENERAL").upper(),
            "body_part": clinical.get("body_part") or "UNSPECIFIED",
            "patient_pseudonym": clinical.get("patient_pseudonym") or "ANONYMOUS_PATIENT",
            "acquisition_date": clinical.get("acquisition_date") or datetime.utcnow().isoformat(),
            "clinical_notes": clinical.get("clinical_notes") or "",
            "safe_technical_tags": raw_exif_data
        }
