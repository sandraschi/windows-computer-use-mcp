"""Face recognition tools for PyWinAuto MCP.

This module provides face recognition capabilities for user verification.
"""

import base64
import logging
import os
import pickle
import tempfile
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

try:
    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("face_recognition library not available. Face recognition features will be disabled.")

# Import the FastMCP app instance
try:
    from windows_computer_use_mcp.main import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in face recognition tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in face recognition tools: {e}")
    app = None

# Constants
DEFAULT_KNOWN_FACES_DIR = Path("data/known_faces")
DEFAULT_ENCRYPTION_KEY = b"your-32-byte-encryption-key-here"  # In production, load from secure storage


@dataclass
class FaceData:
    """Stores face encoding and metadata."""

    name: str
    encoding: bytes
    created_at: str
    last_used: str | None = None
    usage_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


# Only proceed with tool registration if app and dependencies are available
if app is not None and FACE_RECOGNITION_AVAILABLE:
    from datetime import datetime

    from cryptography.fernet import Fernet, InvalidToken

    class FaceRecognition:
        """Handles face recognition operations."""

        def __init__(
            self,
            known_faces_dir: Path = DEFAULT_KNOWN_FACES_DIR,
            tolerance: float = 0.6,
            model: str = "hog",
            encryption_key: bytes = DEFAULT_ENCRYPTION_KEY,
        ):
            """Initialize face recognition.

            Args:
                known_faces_dir: Directory to store known face encodings
                tolerance: How much distance between faces to consider it a match. Lower is more strict.
                model: Which face detection model to use. 'hog' is faster, 'cnn' is more accurate.
                encryption_key: Key for encrypting face data

            """
            self.known_faces_dir = Path(known_faces_dir)
            self.known_faces_dir.mkdir(parents=True, exist_ok=True)
            self.tolerance = tolerance
            self.model = model
            self.known_faces: dict[str, FaceData] = {}

            # Set up encryption
            self.encryption_key = encryption_key
            self.cipher_suite = Fernet(base64.urlsafe_b64encode(self.encryption_key))

            # Load known faces
            self.load_known_faces()

        def _encrypt_data(self, data: bytes) -> bytes:
            """Encrypt binary data."""
            return self.cipher_suite.encrypt(data)

        def _decrypt_data(self, encrypted_data: bytes) -> bytes:
            """Decrypt binary data."""
            return self.cipher_suite.decrypt(encrypted_data)

        def _serialize_face_data(self, face_data: FaceData) -> dict[str, Any]:
            """Convert FaceData to a serializable dictionary."""
            data = asdict(face_data)
            data["encoding"] = base64.b64encode(face_data.encoding).decode("utf-8")
            return data

        def _deserialize_face_data(self, data: dict[str, Any]) -> FaceData:
            """Convert dictionary back to FaceData."""
            if "encoding" in data and isinstance(data["encoding"], str):
                data["encoding"] = base64.b64decode(data["encoding"].encode("utf-8"))
            return FaceData(**data)

        def load_known_faces(self) -> None:
            """Load known faces from the data directory."""
            self.known_faces = {}

            if not self.known_faces_dir.exists():
                return

            for file_path in self.known_faces_dir.glob("*.pkl"):
                try:
                    # Read and decrypt the file
                    with open(file_path, "rb") as f:
                        encrypted_data = f.read()
                    decrypted_data = self._decrypt_data(encrypted_data)

                    # Deserialize the data
                    face_data = pickle.loads(decrypted_data)

                    # Convert to FaceData if it's a dictionary
                    if isinstance(face_data, dict):
                        face_data = self._deserialize_face_data(face_data)

                    self.known_faces[face_data.name] = face_data

                except (InvalidToken, pickle.PickleError, Exception) as e:
                    logger.error(f"Error loading face data from {file_path}: {e}")

        def save_face_data(self, name: str) -> bool:
            """Save face data for a person.

            Args:
                name: Name of the person

            Returns:
                bool: True if saved successfully, False otherwise

            """
            if name not in self.known_faces:
                return False

            face_data = self.known_faces[name]

            try:
                # Update metadata
                face_data.last_used = datetime.now().isoformat()
                face_data.usage_count += 1

                # Serialize the data
                serialized = pickle.dumps(face_data)

                # Encrypt the data
                encrypted_data = self._encrypt_data(serialized)

                # Save to file
                file_path = self.known_faces_dir / f"{name.lower().replace(' ', '_')}.pkl"
                with open(file_path, "wb") as f:
                    f.write(encrypted_data)

                return True

            except Exception as e:
                logger.error(f"Error saving face data for {name}: {e}")
                return False

        def add_face_from_image(self, name: str, image_path: str) -> dict[str, Any]:
            """Add a new face from an image file.

            Args:
                name: Name of the person
                image_path: Path to the image file

            Returns:
                Dict with the result of the operation

            """
            try:
                # Load the image
                image = face_recognition.load_image_file(image_path)

                # Find face encodings
                face_encodings = face_recognition.face_encodings(image)

                if not face_encodings:
                    return {"status": "error", "error": "No faces found in the image"}

                if len(face_encodings) > 1:
                    return {"status": "error", "error": "Multiple faces found in the image"}

                # Store the face data
                now = datetime.now().isoformat()
                face_data = FaceData(
                    name=name,
                    encoding=face_encodings[0].tobytes(),
                    created_at=now,
                    last_used=now,
                    usage_count=1,
                )

                self.known_faces[name] = face_data

                # Save to disk
                if self.save_face_data(name):
                    return {"status": "success", "name": name, "message": "Face added successfully"}
                else:
                    return {"status": "error", "error": "Failed to save face data"}

            except Exception as e:
                logger.error(f"Error adding face from image: {e}")
                return {"status": "error", "error": str(e)}

        def recognize_face(self, image_path: str) -> dict[str, Any]:
            """Recognize a face in an image.

            Args:
                image_path: Path to the image file

            Returns:
                Dict with recognition results

            """
            try:
                # Load the image
                image = face_recognition.load_image_file(image_path)

                # Find face locations and encodings
                face_locations = face_recognition.face_locations(image, model=self.model)
                face_encodings = face_recognition.face_encodings(image, face_locations)

                if not face_encodings:
                    return {"status": "success", "faces_found": 0, "matches": []}

                matches = []

                for face_encoding in face_encodings:
                    # Compare with known faces
                    match_found = False

                    for name, known_face in self.known_faces.items():
                        known_encoding = np.frombuffer(known_face.encoding, dtype=np.float64)

                        # Compare faces
                        match = face_recognition.compare_faces(
                            [known_encoding], face_encoding, tolerance=self.tolerance
                        )

                        if match[0]:
                            # Calculate face distance
                            face_distance = float(face_recognition.face_distance([known_encoding], face_encoding)[0])

                            # Update last used timestamp
                            known_face.last_used = datetime.now().isoformat()
                            known_face.usage_count += 1
                            self.save_face_data(name)

                            matches.append(
                                {
                                    "name": name,
                                    "confidence": 1.0 - face_distance,
                                    "face_distance": face_distance,
                                }
                            )

                            match_found = True
                            break

                    if not match_found:
                        matches.append({"name": "unknown", "confidence": 0.0, "face_distance": 1.0})

                return {
                    "status": "success",
                    "faces_found": len(face_encodings),
                    "matches": matches,
                    "timestamp": time.time(),
                }

            except Exception as e:
                logger.error(f"Error recognizing face: {e}")
                return {"status": "error", "error": str(e)}

        def list_known_faces(self) -> dict[str, Any]:
            """List all known faces.

            Returns:
                Dict with the list of known faces

            """
            faces = []

            for name, face_data in self.known_faces.items():
                faces.append(
                    {
                        "name": name,
                        "created_at": face_data.created_at,
                        "last_used": face_data.last_used,
                        "usage_count": face_data.usage_count,
                    }
                )

            return {
                "status": "success",
                "count": len(faces),
                "faces": faces,
                "timestamp": time.time(),
            }

        def delete_face(self, name: str) -> dict[str, Any]:
            """Delete a known face.

            Args:
                name: Name of the person to delete

            Returns:
                Dict with the result of the operation

            """
            if name not in self.known_faces:
                return {"status": "error", "error": f"No face data found for {name}"}

            try:
                # Remove from memory
                del self.known_faces[name]

                # Delete the file
                file_path = self.known_faces_dir / f"{name.lower().replace(' ', '_')}.pkl"
                if file_path.exists():
                    file_path.unlink()

                return {
                    "status": "success",
                    "message": f"Face data for {name} deleted successfully",
                    "timestamp": time.time(),
                }

            except Exception as e:
                logger.error(f"Error deleting face data for {name}: {e}")
                return {"status": "error", "error": str(e)}

    # Create a global instance
    face_recognizer = FaceRecognition()

    @app.tool()
    def add_face(name: str, image_path: str) -> dict[str, Any]:
        """Add a new face to the recognition system.

        Args:
            name: Name of the person
            image_path: Path to the image file containing the face

        Returns:
            Dict with the result of the operation

        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                "status": "error",
                "error": "Face recognition not available. Install the face_recognition library.",
            }

        if not os.path.exists(image_path):
            return {"status": "error", "error": f"Image file not found: {image_path}"}

        return face_recognizer.add_face_from_image(name, image_path)

    @app.tool()
    def recognize_face(image_path: str) -> dict[str, Any]:
        """Recognize faces in an image.

        Args:
            image_path: Path to the image file

        Returns:
            Dict with recognition results

        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                "status": "error",
                "error": "Face recognition not available. Install the face_recognition library.",
            }

        if not os.path.exists(image_path):
            return {"status": "error", "error": f"Image file not found: {image_path}"}

        return face_recognizer.recognize_face(image_path)

    @app.tool()
    def list_known_faces() -> dict[str, Any]:
        """List all known faces in the system.

        Returns:
            Dict with the list of known faces

        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                "status": "error",
                "error": "Face recognition not available. Install the face_recognition library.",
            }

        return face_recognizer.list_known_faces()

    @app.tool()
    def delete_face(name: str) -> dict[str, Any]:
        """Delete a known face from the system.

        Args:
            name: Name of the person to delete

        Returns:
            Dict with the result of the operation

        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                "status": "error",
                "error": "Face recognition not available. Install the face_recognition library.",
            }

        return face_recognizer.delete_face(name)

    @app.tool(
        name="capture_and_recognize",
        description="Capture an image from the webcam and recognize faces in it.",
    )
    def capture_and_recognize(camera_index: int = 0, save_path: str | None = None) -> dict[str, Any]:
        """Capture an image from the webcam and recognize faces in it.

        Args:
            camera_index: Index of the camera to use (default: 0)
            save_path: Optional path to save the captured image

        Returns:
            Dict with recognition results

        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {
                "status": "error",
                "error": "Face recognition not available. Install the face_recognition library.",
            }

        try:
            # Open the camera
            cap = cv2.VideoCapture(camera_index)

            if not cap.isOpened():
                return {
                    "status": "error",
                    "error": f"Could not open camera at index {camera_index}",
                }

            # Capture a frame
            ret, frame = cap.read()
            cap.release()

            if not ret:
                return {"status": "error", "error": "Failed to capture image from camera"}

            # Save the image if requested
            if save_path:
                try:
                    cv2.imwrite(save_path, frame)
                except Exception as e:
                    logger.error(f"Error saving captured image: {e}")

            # Save to a temporary file for recognition
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_path = temp_file.name
                cv2.imwrite(temp_path, frame)

            try:
                # Recognize faces
                result = face_recognizer.recognize_face(temp_path)

                # Add the image path to the result
                if save_path:
                    result["image_path"] = save_path

                return result

            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error in capture_and_recognize: {e}")
            return {"status": "error", "error": str(e)}

    # Add all tools to __all__
    __all__ = [
        "add_face",
        "capture_and_recognize",
        "delete_face",
        "list_known_faces",
        "recognize_face",
    ]
else:
    # If face recognition is not available, provide dummy implementations
    __all__ = []

    @app.tool(
        name="add_face",
        description="Face recognition not available. Install the face_recognition library.",
    )
    def add_face(name: str, image_path: str) -> dict[str, Any]:
        return {
            "status": "error",
            "error": "Face recognition not available. Install the face_recognition library.",
        }

    @app.tool(
        name="recognize_face",
        description="Face recognition not available. Install the face_recognition library.",
    )
    def recognize_face(image_path: str) -> dict[str, Any]:
        return {
            "status": "error",
            "error": "Face recognition not available. Install the face_recognition library.",
        }

    @app.tool(
        name="list_known_faces",
        description="Face recognition not available. Install the face_recognition library.",
    )
    def list_known_faces() -> dict[str, Any]:
        return {
            "status": "error",
            "error": "Face recognition not available. Install the face_recognition library.",
        }

    @app.tool(
        name="delete_face",
        description="Face recognition not available. Install the face_recognition library.",
    )
    def delete_face(name: str) -> dict[str, Any]:
        return {
            "status": "error",
            "error": "Face recognition not available. Install the face_recognition library.",
        }

    @app.tool(
        name="capture_and_recognize",
        description="Face recognition not available. Install the face_recognition library.",
    )
    def capture_and_recognize(camera_index: int = 0, save_path: str | None = None) -> dict[str, Any]:
        return {
            "status": "error",
            "error": "Face recognition not available. Install the face_recognition library.",
        }
