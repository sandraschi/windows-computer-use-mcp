"""Tests for face recognition functionality."""

import os

# Add the parent directory to the Python path
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

sys.path.append(str(Path(__file__).parent.parent))

from windows_computer_use_mcp.face_recognition import FaceRecognition

# Test data
TEST_IMAGE_DIR = Path(__file__).parent / "test_images"
KNOWN_FACE_IMAGE = TEST_IMAGE_DIR / "known_face.jpg"
UNKNOWN_FACE_IMAGE = TEST_IMAGE_DIR / "unknown_face.jpg"

# Use mocks for face recognition tests instead of requiring actual images
# Tests will create mock image data when needed


@pytest.fixture
def face_rec():
    """Fixture that provides a FaceRecognition instance for testing."""
    import base64

    from cryptography.fernet import Fernet

    # Use a temporary directory for test data
    with patch("windows_computer_use_mcp.face_recognition.KNOWN_FACES_DIR", Path("tests/test_data/known_faces")):
        # Create the test directory if it doesn't exist
        os.makedirs("tests/test_data/known_faces", exist_ok=True)

        # Generate a valid Fernet key (32 bytes, base64-encoded)
        valid_key = Fernet.generate_key()
        # The key is already base64-encoded, but face_recognition.py expects raw bytes
        # So we decode it to get the raw 32 bytes
        raw_key = base64.urlsafe_b64decode(valid_key)

        # Initialize with a valid encryption key (raw bytes)
        with patch("windows_computer_use_mcp.face_recognition.ENCRYPTION_KEY", raw_key):
            yield FaceRecognition(tolerance=0.6, model="hog")

    # Cleanup: Remove test data after tests
    import shutil

    if os.path.exists("tests/test_data"):
        shutil.rmtree("tests/test_data")


@patch("face_recognition.face_encodings")
@patch("face_recognition.face_locations")
@patch("face_recognition.load_image_file")
def test_add_known_face(mock_load_image, mock_face_locations, mock_face_encodings, face_rec):
    """Test adding a known face."""
    # Mock face recognition functions
    mock_load_image.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_face_locations.return_value = [(10, 20, 30, 40)]
    mock_face_encodings.return_value = [np.random.rand(128)]

    # Test with image path (create temp file)
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        tmp_file.write(b"fake image data")
        tmp_path = tmp_file.name

    try:
        success = face_rec.add_known_face("Test User", tmp_path)
        assert success
        assert "Test User" in face_rec.known_faces
    finally:
        os.unlink(tmp_path)

    # Test with image data
    mock_face_encodings.return_value = [np.random.rand(128)]
    success = face_rec.add_known_face("Test User 2", image_data=b"fake image data")
    assert success
    assert "Test User 2" in face_rec.known_faces


@patch("face_recognition.face_encodings")
@patch("face_recognition.face_locations")
@patch("face_recognition.load_image_file")
def test_remove_known_face(mock_load_image, mock_face_locations, mock_face_encodings, face_rec):
    """Test removing a known face."""
    # Mock face recognition functions
    mock_load_image.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_face_locations.return_value = [(10, 20, 30, 40)]
    mock_face_encodings.return_value = [np.random.rand(128)]

    # First add a face
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        tmp_file.write(b"fake image data")
        tmp_path = tmp_file.name

    try:
        face_rec.add_known_face("Test User", tmp_path)
        assert "Test User" in face_rec.known_faces

        # Then remove it
        success = face_rec.remove_known_face("Test User")
        assert success
        assert "Test User" not in face_rec.known_faces

        # Try removing non-existent face
        success = face_rec.remove_known_face("Non-existent User")
        assert not success
    finally:
        os.unlink(tmp_path)


@patch("face_recognition.face_encodings")
@patch("face_recognition.face_locations")
@patch("face_recognition.load_image_file")
@patch("face_recognition.compare_faces")
@patch("face_recognition.face_distance")
def test_recognize_face(
    mock_face_distance,
    mock_compare_faces,
    mock_load_image,
    mock_face_locations,
    mock_face_encodings,
    face_rec,
):
    """Test recognizing a face."""
    # Mock face recognition functions
    known_encoding = np.random.rand(128)
    unknown_encoding = np.random.rand(128)

    mock_load_image.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_face_locations.return_value = [(10, 20, 30, 40)]

    # Add a known face
    mock_face_encodings.return_value = [known_encoding]
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        tmp_file.write(b"fake image data")
        tmp_path = tmp_file.name

    try:
        face_rec.add_known_face("Test User", tmp_path)

        # Test with known face (matching encoding)
        mock_face_encodings.return_value = [known_encoding]
        mock_compare_faces.return_value = [True]
        mock_face_distance.return_value = [0.3]

        success, name, confidence = face_rec.recognize_face(b"fake image data")
        assert success
        assert name == "Test User"
        assert 0.0 <= confidence <= 1.0

        # Test with unknown face (non-matching encoding)
        mock_face_encodings.return_value = [unknown_encoding]
        mock_compare_faces.return_value = [False]
        mock_face_distance.return_value = [0.9]

        success, name, confidence = face_rec.recognize_face(b"fake unknown image data")
        assert not success
        assert name is None
        assert confidence == 0.0
    finally:
        os.unlink(tmp_path)


@patch("cv2.VideoCapture")
def test_capture_and_verify_face(mock_video_capture, face_rec):
    """Test face verification with webcam."""
    # Mock the video capture
    mock_camera = MagicMock()
    mock_video_capture.return_value = mock_camera

    # Mock frame data
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_camera.read.return_value = (True, test_frame)

    # Mock face detection
    with (
        patch("face_recognition.face_locations") as mock_face_locations,
        patch("face_recognition.face_encodings") as mock_face_encodings,
        patch("face_recognition.load_image_file") as mock_load_image,
    ):
        # Setup mock for no face detected
        mock_face_locations.return_value = []

        # Test with no face in frame (should return False)
        success, name, confidence = face_rec.capture_and_verify_face(timeout=1)
        assert not success
        assert name is None
        assert confidence == 0.0

        # Setup mock for face detected but not recognized
        mock_face_locations.return_value = [(100, 200, 300, 400)]
        mock_face_encodings.return_value = [np.zeros(128)]

        # Add a known face with a different encoding
        mock_load_image.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_face_locations.return_value = [(10, 20, 30, 40)]
        mock_face_encodings.return_value = [np.random.rand(128)]
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            tmp_file.write(b"fake image data")
            tmp_path = tmp_file.name
        try:
            face_rec.add_known_face("Test User", tmp_path)

            # Test with face detected but not recognized (different encoding)
            success, name, confidence = face_rec.capture_and_verify_face(timeout=1)
            assert not success
            assert name is None
            assert confidence == 0.0
        finally:
            os.unlink(tmp_path)


def test_face_encryption(face_rec):
    """Test that face encodings are properly encrypted/decrypted."""
    # Create a test encoding
    test_encoding = np.random.rand(128)

    # Encrypt and decrypt
    encrypted = face_rec.encrypt_encoding(test_encoding)
    decrypted = face_rec.decrypt_encoding(encrypted)

    # Check that decrypted data matches original
    assert np.allclose(test_encoding, decrypted)

    # Check that encrypted data is different from original
    assert not np.array_equal(test_encoding.tobytes(), encrypted)
