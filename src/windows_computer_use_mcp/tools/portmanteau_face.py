"""Face recognition portmanteau tool for PyWinAuto MCP.

Loaded only when the operator sets **windows_computer_use_mcp_ENABLE_FACE=1** (and face deps are installed).
See **docs/SAFETY.md** §5.

PORTMANTEAU PATTERN RATIONALE:
Instead of creating 5+ separate tools (one per face recognition operation), this tool consolidates
related face recognition operations into a single interface. This design:
- Prevents tool explosion (5+ tools → 1 tool) while maintaining full functionality
- Improves discoverability by grouping related operations together
- Follows FastMCP 2.13+ best practices for feature-rich MCP servers

SUPPORTED OPERATIONS:
- add: Add a new face to the recognition database
- recognize: Recognize faces in an image
- list: List all known faces
- delete: Delete a known face
- capture: Capture from a local camera (OpenCV index) and recognize — use built-in or USB UVC webcam; not Tapo/IP cameras
"""

import base64
import logging
import os
import pickle
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cv2
import numpy as np

# Import the FastMCP app instance
try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_face")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_face: {e}")
    app = None

# Try to import face_recognition
try:
    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logger.warning("face_recognition library not available")

# Try to import encryption
try:
    from cryptography.fernet import Fernet, InvalidToken

    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

# Constants
DEFAULT_KNOWN_FACES_DIR = Path("data/known_faces")
DEFAULT_ENCRYPTION_KEY = b"your-32-byte-encryption-key-here"


@dataclass
class FaceData:
    """Stores face encoding and metadata."""

    name: str
    encoding: bytes
    created_at: str
    last_used: str | None = None
    usage_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class FaceRecognitionManager:
    """Manages face recognition operations."""

    def __init__(
        self,
        known_faces_dir: Path = DEFAULT_KNOWN_FACES_DIR,
        tolerance: float = 0.6,
        model: str = "hog",
    ):
        self.known_faces_dir = Path(known_faces_dir)
        self.known_faces_dir.mkdir(parents=True, exist_ok=True)
        self.tolerance = tolerance
        self.model = model
        self.known_faces: dict[str, FaceData] = {}

        if ENCRYPTION_AVAILABLE:
            self.cipher_suite = Fernet(base64.urlsafe_b64encode(DEFAULT_ENCRYPTION_KEY))
        else:
            self.cipher_suite = None

        self.load_known_faces()

    def load_known_faces(self):
        """Load known faces from disk."""
        self.known_faces = {}
        if not self.known_faces_dir.exists():
            return

        for file_path in self.known_faces_dir.glob("*.pkl"):
            try:
                with open(file_path, "rb") as f:
                    data = f.read()

                if self.cipher_suite:
                    try:
                        data = self.cipher_suite.decrypt(data)
                    except InvalidToken:
                        logger.debug("Decryption failed - possibly unencrypted legacy file.")

                face_data = pickle.loads(data)
                if isinstance(face_data, dict):
                    face_data = FaceData(**face_data)

                self.known_faces[face_data.name] = face_data
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

    def save_face(self, name: str) -> bool:
        """Save face data to disk."""
        if name not in self.known_faces:
            return False

        face_data = self.known_faces[name]
        try:
            from datetime import datetime

            face_data.last_used = datetime.now().isoformat()
            face_data.usage_count += 1

            data = pickle.dumps(face_data)
            if self.cipher_suite:
                data = self.cipher_suite.encrypt(data)

            file_path = self.known_faces_dir / f"{name.lower().replace(' ', '_')}.pkl"
            with open(file_path, "wb") as f:
                f.write(data)

            return True
        except Exception as e:
            logger.error(f"Error saving face {name}: {e}")
            return False

    def recognize_faces(self, image_path: str, tolerance: float = 0.6) -> list[dict[str, Any]]:
        """Recognize faces in an image and return matches."""
        if not FACE_RECOGNITION_AVAILABLE:
            return []

        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model=self.model)
            face_encodings = face_recognition.face_encodings(image, face_locations)

            results = []
            for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations, strict=False):
                name = "Unknown"
                confidence = 0.0

                if self.known_faces:
                    known_names = list(self.known_faces.keys())
                    known_encodings = [
                        np.frombuffer(self.known_faces[n].encoding, dtype=np.float64) for n in known_names
                    ]

                    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)

                    if face_distances[best_match_index] <= tolerance:
                        name = known_names[best_match_index]
                        confidence = 1.0 - float(face_distances[best_match_index])

                        # Update metadata
                        self.known_faces[name].last_used = time.strftime("%Y-%m-%dT%H:%M:%S")
                        self.known_faces[name].usage_count += 1

                results.append(
                    {
                        "name": name,
                        "confidence": confidence,
                        "box": {"top": top, "right": right, "bottom": bottom, "left": left},
                    }
                )

            return results
        except Exception as e:
            logger.error(f"Error in recognize_faces: {e}")
            return []


from windows_computer_use_mcp.tools.models import FaceOperationRequest, ToolResult

# Create global instance if available
face_manager = None
if FACE_RECOGNITION_AVAILABLE:
    try:
        face_manager = FaceRecognitionManager()
    except Exception as e:
        logger.error(f"Failed to initialize face manager: {e}")


if app is not None:
    logger.info("Registering portmanteau_face tool with FastMCP")

    @app.tool(
        name="automation_face",
        description="""Industrialized local face recognition and biometric enrollment tool.

WHAT IT DOES:
This tool provides local-only biometric capabilities for registering and recognizing individuals via facial encodings. It can enroll new faces from static images, match unknown faces against a local encrypted database, and capture live frames from primary or secondary UVC webcams.

WHEN TO USE:
- Use 'add' to enroll a person into the system (e.g., for personalized automation triggers).
- Use 'recognize' to identify individuals present in a provided image file.
- Use 'capture' to engage a local camera (laptop built-in or USB webcam) for real-time identification.
- Use 'list' or 'delete' for managing the local biometric database.

SAFETY AND PRIVACY:
This tool operates entirely locally and requires explicit opt-in via 'windows_computer_use_mcp_ENABLE_FACE=1'. It does not transmit biometric data to remote servers. If recognition fails, ensure adequate lighting and centered positioning of the target face.

RECOVERY:
If 'capture' fails to open the camera, verify the 'camera_index' (0 is usually the default) and ensure no other application is currently locking the device.
""",
    )
    def automation_face(request: FaceOperationRequest) -> ToolResult:
        """Face recognition operations tracking SOTA 2026 biometric standards."""
        try:
            timestamp = time.time()
            operation = request.operation
            name = request.name
            image_path = request.image_path
            camera_index = request.camera_index
            save_capture_path = request.save_capture_path
            tolerance = request.tolerance

            if not FACE_RECOGNITION_AVAILABLE:
                return ToolResult(
                    status="error",
                    message="face_recognition library is not installed.",
                    recovery_tip="Run 'pip install face_recognition' on a system with dlib support.",
                )

            if face_manager is None:
                return ToolResult(
                    status="error",
                    message="Face recognition manager failed to initialize.",
                    recovery_tip="Check if the known_faces directory is writable and dependencies are met.",
                )

            biometric_metadata = {
                "timestamp": timestamp,
                "model": face_manager.model,
                "tolerance": tolerance,
                "encryption": ENCRYPTION_AVAILABLE,
            }

            # === ADD OPERATION ===
            if operation == "add":
                if not name or not image_path:
                    return ToolResult(
                        status="error",
                        message="'name' and 'image_path' are required for 'add' operation.",
                        recovery_tip="Ensure you provide both the individual's name and a path to a clear facial image.",
                    )
                if not os.path.exists(image_path):
                    return ToolResult(
                        status="error",
                        message=f"Image file not found: {image_path}",
                        recovery_tip="Verify the file path is correct and accessible.",
                    )

                image = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image)

                if not encodings:
                    return ToolResult(
                        status="error",
                        message="No faces found in the image",
                        recovery_tip="Ensure the image contains a clear, unobstructed face.",
                    )

                if len(encodings) > 1:
                    return ToolResult(
                        status="error",
                        message="Multiple faces found. Please provide image with single face.",
                        recovery_tip="Crop the image to include only the target individual.",
                    )

                from datetime import datetime

                now = datetime.now().isoformat()
                face_data = FaceData(
                    name=name,
                    encoding=encodings[0].tobytes(),
                    created_at=now,
                    last_used=now,
                    usage_count=1,
                )
                face_manager.known_faces[name] = face_data

                if face_manager.save_face(name):
                    return ToolResult(
                        status="success",
                        message=f"Face '{name}' added successfully.",
                        data={"name": name, "biometric_metadata": biometric_metadata},
                    )
                else:
                    return ToolResult(
                        status="error",
                        message="Failed to save face data",
                        recovery_tip="Check disk permissions for the known_faces directory.",
                    )

            # === RECOGNIZE OPERATION ===
            elif operation == "recognize":
                if not image_path:
                    return ToolResult(
                        status="error",
                        message="'image_path' is required for 'recognize' operation.",
                        recovery_tip="Provide a path to the image containing faces you wish to identify.",
                    )
                if not os.path.exists(image_path):
                    return ToolResult(
                        status="error",
                        message=f"Image file not found: {image_path}",
                        recovery_tip="Verify the file path is correct.",
                    )

                results = face_manager.recognize_faces(image_path, tolerance=tolerance)
                return ToolResult(
                    status="success",
                    message=f"Recognition completed. Identified {len([r for r in results if r['name'] != 'Unknown'])} known faces.",
                    data={
                        "matches": results,
                        "count": len(results),
                        "biometric_metadata": biometric_metadata,
                    },
                )

            # === LIST OPERATION ===
            elif operation == "list":
                faces = []
                for name, face_data in face_manager.known_faces.items():
                    faces.append(
                        {
                            "name": name,
                            "created_at": face_data.created_at,
                            "last_used": face_data.last_used,
                            "usage_count": face_data.usage_count,
                        }
                    )

                return ToolResult(
                    status="success",
                    message=f"Retrieved {len(faces)} biometric profiles.",
                    data={
                        "names": faces,
                        "count": len(faces),
                        "biometric_metadata": biometric_metadata,
                    },
                )

            # === DELETE OPERATION ===
            elif operation == "delete":
                if not name:
                    return ToolResult(
                        status="error",
                        message="'name' is required for 'delete' operation.",
                        recovery_tip="Specify the name of the profile you wish to remove.",
                    )

                if name not in face_manager.known_faces:
                    return ToolResult(
                        status="error",
                        message=f"No face found for '{name}'",
                        recovery_tip="Check the list of existing profiles using the 'list' operation.",
                    )

                del face_manager.known_faces[name]
                file_path = face_manager.known_faces_dir / f"{name.lower().replace(' ', '_')}.pkl"
                if file_path.exists():
                    file_path.unlink()

                return ToolResult(
                    status="success",
                    message=f"Successfully deleted profile '{name}'.",
                    data={
                        "name": name,
                        "biometric_metadata": biometric_metadata,
                    },
                )

            # === CAPTURE OPERATION ===
            elif operation == "capture":
                cap = cv2.VideoCapture(camera_index)
                if not cap.isOpened():
                    return ToolResult(
                        status="error",
                        message=f"Could not open camera at index {camera_index}.",
                        recovery_tip="Check camera connections and ensure 'camera_index' is correct.",
                    )

                ret, frame = cap.read()
                cap.release()

                if not ret:
                    return ToolResult(
                        status="error",
                        message="Failed to capture frame from camera.",
                        recovery_tip="Ensure the camera is not being used by another application.",
                    )

                if save_capture_path:
                    cv2.imwrite(save_capture_path, frame)
                    image_input = save_capture_path
                else:
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                        cv2.imwrite(f.name, frame)
                        image_input = f.name

                results = face_manager.recognize_faces(image_input, tolerance=tolerance)

                if not save_capture_path:
                    try:
                        os.unlink(image_input)
                    except:
                        pass

                return ToolResult(
                    status="success",
                    message="Camera capture and recognition completed.",
                    data={
                        "matches": results,
                        "count": len(results),
                        "camera_index": camera_index,
                        "save_path": save_capture_path,
                        "biometric_metadata": biometric_metadata,
                    },
                )

            else:
                return ToolResult(
                    status="error",
                    message=f"Unknown face operation: {operation}",
                    recovery_tip="Supported operations are: add, recognize, list, delete, capture.",
                )

        except Exception as e:
            return ToolResult(
                status="error",
                message=f"Face recognition operation failed: {e}",
                recovery_tip="Check if 'face_recognition' and 'dlib' are correctly configured and permissions are granted.",
            )


__all__ = ["automation_face"]
