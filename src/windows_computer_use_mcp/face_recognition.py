"""Face recognition module for PyWinAutoMCP security features.

This module provides face recognition capabilities for user verification.
"""

import base64
import logging
import pickle
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import cv2
import face_recognition
import numpy as np
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

# Constants
KNOWN_FACES_DIR = Path("data/known_faces")
KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)
ENCRYPTION_KEY = b"your-32-byte-encryption-key-here"  # In production, load from secure storage


@dataclass
class FaceData:
    """Stores face encoding and metadata."""

    name: str
    encoding: bytes
    created_at: str
    last_used: str | None = None
    usage_count: int = 0


class FaceRecognition:
    """Handles face recognition operations."""

    def __init__(self, tolerance: float = 0.6, model: str = "hog"):
        """Initialize face recognition.

        Args:
            tolerance: How much distance between faces to consider it a match. Lower is more strict.
            model: Which face detection model to use. 'hog' is faster, 'cnn' is more accurate.

        """
        self.tolerance = tolerance
        self.model = model
        self.known_faces: dict[str, FaceData] = {}
        self.cipher_suite = Fernet(base64.urlsafe_b64encode(ENCRYPTION_KEY))
        self.load_known_faces()

    def encrypt_encoding(self, encoding: np.ndarray) -> bytes:
        """Encrypt face encoding for secure storage."""
        return self.cipher_suite.encrypt(encoding.tobytes())

    def decrypt_encoding(self, encrypted: bytes) -> np.ndarray:
        """Decrypt face encoding."""
        decrypted = self.cipher_suite.decrypt(encrypted)
        return np.frombuffer(decrypted, dtype=np.float64)

    def load_known_faces(self) -> None:
        """Load known faces from disk."""
        self.known_faces = {}

        if not KNOWN_FACES_DIR.exists():
            return

        for face_file in KNOWN_FACES_DIR.glob("*.pkl"):
            try:
                with open(face_file, "rb") as f:
                    face_data = pickle.load(f)
                    if isinstance(face_data, dict):
                        # Convert dict to FaceData object if needed
                        face_data = FaceData(**face_data)
                    self.known_faces[face_data.name] = face_data
            except Exception as e:
                logger.error(f"Error loading face data from {face_file}: {e}")

    def save_known_faces(self) -> None:
        """Save known faces to disk."""
        KNOWN_FACES_DIR.mkdir(parents=True, exist_ok=True)

        for name, face_data in self.known_faces.items():
            try:
                face_file = KNOWN_FACES_DIR / f"{name}.pkl"
                with open(face_file, "wb") as f:
                    pickle.dump(asdict(face_data), f)
            except Exception as e:
                logger.error(f"Error saving face data for {name}: {e}")

    def add_known_face(self, name: str, image_path: str | None = None, image_data: bytes | None = None) -> bool:
        """Add a new known face.

        Args:
            name: Name or identifier for the person
            image_path: Path to an image file containing the face
            image_data: Raw image data as bytes (alternative to image_path)

        Returns:
            bool: True if face was added successfully

        """
        if not image_path and not image_data:
            raise ValueError("Either image_path or image_data must be provided")

        # Load image
        if image_path:
            image = face_recognition.load_image_file(image_path)
        else:
            image = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Find face locations and encodings
        face_locations = face_recognition.face_locations(image, model=self.model)
        if not face_locations:
            logger.warning("No faces found in the provided image")
            return False

        # Use the first face found
        face_encoding = face_recognition.face_encodings(image, [face_locations[0]])[0]

        # Create and store face data
        now = datetime.now(UTC).isoformat()

        face_data = FaceData(
            name=name,
            encoding=self.encrypt_encoding(face_encoding),
            created_at=now,
            last_used=now,
            usage_count=0,
        )

        self.known_faces[name] = face_data
        self.save_known_faces()
        return True

    def remove_known_face(self, name: str) -> bool:
        """Remove a known face by name."""
        if name in self.known_faces:
            del self.known_faces[name]

            # Delete the face file if it exists
            face_file = KNOWN_FACES_DIR / f"{name}.pkl"
            if face_file.exists():
                try:
                    face_file.unlink()
                except Exception as e:
                    logger.error(f"Error deleting face file {face_file}: {e}")

            return True
        return False

    def recognize_face(self, image_data: bytes) -> tuple[bool, str | None, float]:
        """Recognize a face from image data.

        Args:
            image_data: Raw image data as bytes

        Returns:
            Tuple of (success, name, confidence)

        """
        try:
            # Convert image data to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if image is None:
                raise ValueError("Could not decode image data")

            # Convert from BGR to RGB (which face_recognition uses)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Find all face locations and encodings in the current frame
            face_locations = face_recognition.face_locations(rgb_image, model=self.model)

            if not face_locations:
                return False, None, 0.0

            # Get face encodings for all faces in the image
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

            # Compare with known faces
            for face_encoding, (_top, _right, _bottom, _left) in zip(face_encodings, face_locations, strict=False):
                # Check if the face matches any known faces
                for name, face_data in self.known_faces.items():
                    known_encoding = self.decrypt_encoding(face_data.encoding)

                    # Compare faces
                    matches = face_recognition.compare_faces([known_encoding], face_encoding, tolerance=self.tolerance)

                    if True in matches:
                        # Calculate face distance (lower is more similar)
                        face_distances = face_recognition.face_distance([known_encoding], face_encoding)
                        confidence = 1.0 - face_distances[0]  # Convert to confidence score (0-1)

                        # Update last used timestamp and usage count
                        face_data.last_used = datetime.now(UTC).isoformat()
                        face_data.usage_count += 1
                        self.save_known_faces()

                        return True, name, confidence

            return False, None, 0.0

        except Exception as e:
            logger.error(f"Error in face recognition: {e}")
            return False, None, 0.0

    def capture_and_verify_face(
        self, timeout: int = 30, confidence_threshold: float = 0.7
    ) -> tuple[bool, str | None, float]:
        """Capture video from webcam and try to recognize a face.

        Args:
            timeout: Maximum time to try recognizing (seconds)
            confidence_threshold: Minimum confidence score to accept a match (0-1)

        Returns:
            Tuple of (success, name, confidence)

        """
        video_capture = cv2.VideoCapture(0)
        if not video_capture.isOpened():
            raise RuntimeError("Could not open video device")

        end_time = datetime.now() + timedelta(seconds=timeout)

        try:
            while datetime.now() < end_time:
                # Grab a single frame of video
                ret, frame = video_capture.read()

                if not ret:
                    logger.warning("Failed to capture frame from webcam")
                    time.sleep(0.1)
                    continue

                # Convert the image from BGR color (which OpenCV uses) to RGB color
                rgb_frame = frame[:, :, ::-1]

                # Find all face locations and encodings in the current frame
                face_locations = face_recognition.face_locations(rgb_frame, model=self.model)

                if not face_locations:
                    # No faces found, show a message
                    cv2.putText(
                        frame,
                        "No face detected",
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )
                else:
                    # Get face encodings for all faces in the image
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                    # Loop through each face in this frame of video
                    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings, strict=False):
                        # Check if the face matches any known faces
                        for name, face_data in self.known_faces.items():
                            known_encoding = self.decrypt_encoding(face_data.encoding)

                            # Compare faces
                            matches = face_recognition.compare_faces(
                                [known_encoding], face_encoding, tolerance=self.tolerance
                            )

                            if True in matches:
                                # Calculate face distance (lower is more similar)
                                face_distances = face_recognition.face_distance([known_encoding], face_encoding)
                                confidence = 1.0 - face_distances[0]  # Convert to confidence score (0-1)

                                if confidence >= confidence_threshold:
                                    # Update last used timestamp and usage count
                                    face_data.last_used = datetime.now(UTC).isoformat()
                                    face_data.usage_count += 1
                                    self.save_known_faces()

                                    # Draw a box around the face
                                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                                    # Draw a label with the name and confidence
                                    label = f"{name} ({confidence:.2f})"
                                    cv2.rectangle(
                                        frame,
                                        (left, bottom - 35),
                                        (right, bottom),
                                        (0, 255, 0),
                                        cv2.FILLED,
                                    )
                                    cv2.putText(
                                        frame,
                                        label,
                                        (left + 6, bottom - 6),
                                        cv2.FONT_HERSHEY_DUPLEX,
                                        0.5,
                                        (0, 0, 0),
                                        1,
                                    )

                                    # Show the frame with the recognized face
                                    cv2.imshow("Face Recognition", frame)
                                    cv2.waitKey(1000)  # Show the match for 1 second

                                    return True, name, confidence

                                # If we get here, face was recognized but confidence is too low
                                label = f"Unknown (confidence: {confidence:.2f})"
                                cv2.rectangle(
                                    frame,
                                    (left, bottom - 35),
                                    (right, bottom),
                                    (0, 0, 255),
                                    cv2.FILLED,
                                )
                                cv2.putText(
                                    frame,
                                    label,
                                    (left + 6, bottom - 6),
                                    cv2.FONT_HERSHEY_DUPLEX,
                                    0.5,
                                    (255, 255, 255),
                                    1,
                                )

                # Display the resulting image
                cv2.imshow("Face Recognition", frame)

                # Hit 'q' on the keyboard to quit
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

                # Small delay to reduce CPU usage
                time.sleep(0.05)

            return False, None, 0.0

        finally:
            # Release handle to the webcam
            video_capture.release()
            cv2.destroyAllWindows()


# Create a global instance
face_recognizer = FaceRecognition()
