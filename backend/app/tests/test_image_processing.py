"""
Phase 3 Automated Verification Suite: Image Preprocessing Pipeline
Tests format detection, magic bytes enforcement, tensor flattening,
exact pixel reconstruction, and REST upload endpoints.
"""
import pytest
import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.database.connection import SessionLocal
from app.database.init_db import init_database
from app.models.db_models import User
from app.image_processing.validator import (
    validate_image_payload, 
    detect_image_format_from_bytes, 
    ImageValidationError
)
from app.image_processing.preprocessor import ImagePreprocessor
from app.security.token_util import create_access_token

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    init_database()

@pytest.fixture
def auth_headers():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "dr_alice_radiology").first()
        token = create_access_token({
            "sub": user.user_id, 
            "username": user.username, 
            "role": user.role.role_name if user.role else "USER"
        })
        return {"Authorization": f"Bearer {token}"}
    finally:
        db.close()

@pytest.fixture
def sample_png_bytes():
    # Create 64x64 synthetic RGB test image
    arr = np.random.randint(0, 256, (64, 64, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@pytest.fixture
def sample_grayscale_bytes():
    # Create 64x64 synthetic Grayscale test image
    arr = np.random.randint(0, 256, (64, 64), dtype=np.uint8)
    img = Image.fromarray(arr, mode="L")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_magic_byte_detection_and_validation(sample_png_bytes):
    fmt = detect_image_format_from_bytes(sample_png_bytes)
    assert fmt == "PNG"

    info = validate_image_payload(sample_png_bytes, "test.png")
    assert info["valid"] is True
    assert info["format"] == "PNG"
    assert info["width"] == 64
    assert info["height"] == 64
    assert info["channels"] == 3

def test_rejection_of_disguised_fake_image():
    fake_payload = b"MZ\x90\x00This is an executable or text file disguised as a png!"
    with pytest.raises(ImageValidationError) as exc:
        detect_image_format_from_bytes(fake_payload)
    assert "Unsupported or unrecognized" in str(exc.value)

def test_rejection_of_corrupted_image():
    # Valid magic bytes but corrupted payload over 64 bytes
    corrupted_bytes = b"\x89PNG\r\n\x1a\n" + b"CorruptedHeaderGarbage123456789" * 4
    with pytest.raises(ImageValidationError) as exc:
        validate_image_payload(corrupted_bytes, "corrupt.png")
    assert "Corrupted image data" in str(exc.value)

def test_preprocessing_and_bit_exact_reconstruction(sample_png_bytes):
    # Process image
    res = ImagePreprocessor.process(sample_png_bytes, "test.png")
    assert res["height"] == 64
    assert res["width"] == 64
    assert res["channels"] == 3
    assert len(res["original_sha256"]) == 64
    assert res["vector"].size == 64 * 64 * 3

    # Reconstruct from vector
    reconstructed_bytes = ImagePreprocessor.reconstruct_image(
        res["vector"], res["height"], res["width"], res["channels"], output_format="PNG"
    )
    
    # Re-process reconstructed image and verify hash matches exactly
    re_res = ImagePreprocessor.process(reconstructed_bytes, "reconstructed.png")
    assert re_res["original_sha256"] == res["original_sha256"]
    np.testing.assert_array_equal(res["vector"], re_res["vector"])

def test_grayscale_channel_preservation(sample_grayscale_bytes):
    res = ImagePreprocessor.process(sample_grayscale_bytes, "xray.png")
    assert res["channels"] == 1
    assert res["vector"].size == 64 * 64 * 1

def test_api_upload_endpoint(auth_headers, sample_png_bytes):
    response = client.post(
        "/api/v1/images/upload",
        headers=auth_headers,
        data={
            "title": "Laboratory Diagnostic Scan",
            "modality": "X-RAY",
            "body_part": "CHEST",
            "patient_pseudonym": "PT-TEST-001"
        },
        files={"file": ("scan.png", sample_png_bytes, "image/png")}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "image_id" in data
    assert data["dimensions"]["width"] == 64
    assert data["dimensions"]["height"] == 64
    assert data["dimensions"]["channels"] == 3
    assert len(data["original_sha256"]) == 64

def test_api_load_synthetic_medical_sample(auth_headers):
    response = client.post(
        "/api/v1/images/samples/load/synthetic_chest_xray.png",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["title"] == "Synthetic PA Chest X-Ray"
    assert data["dimensions"]["width"] == 512
    assert data["dimensions"]["height"] == 512
