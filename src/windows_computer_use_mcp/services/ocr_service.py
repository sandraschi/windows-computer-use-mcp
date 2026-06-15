"""OCR Service for extracting text from images using Tesseract OCR."""

import logging
from typing import Any

import cv2
import numpy as np
import pytesseract
from PIL import Image

logger = logging.getLogger(__name__)


class OCRService:
    """Service for Optical Character Recognition operations."""

    def __init__(self, tesseract_cmd: str | None = None):
        """Initialize the OCR service.

        Args:
            tesseract_cmd: Path to the Tesseract executable. If None,
                         the system PATH will be used.

        """
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        # Verify Tesseract is installed and accessible
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            logger.error(
                "Tesseract is not installed or not in your PATH. "
                "Please install it from https://github.com/UB-Mannheim/tesseract/wiki"
            )
            raise

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results.

        Args:
            image: Input image as a numpy array (BGR format from OpenCV)

        Returns:
            Preprocessed image as a numpy array

        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply thresholding to preprocess the image
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # Apply dilation to connect text components
        kernel = np.ones((1, 1), np.uint8)
        gray = cv2.dilate(gray, kernel, iterations=1)

        return gray

    def extract_text(
        self,
        image_path: str | None = None,
        image: np.ndarray | None = None,
        preprocess: bool = True,
        lang: str = "eng",
        config: str = "--psm 6 --oem 3",
    ) -> dict[str, Any]:
        """Extract text from an image file or numpy array.

        Args:
            image_path: Path to the image file
            image: Image as a numpy array (BGR format from OpenCV)
            preprocess: Whether to preprocess the image for better OCR
            lang: Language code for Tesseract (e.g., 'eng', 'deu', 'fra')
            config: Tesseract configuration parameters

        Returns:
            Dictionary containing:
                - text: Extracted text
                - confidence: Average confidence of the OCR result
                - data: Raw Tesseract data

        """
        if image_path and image is None:
            # Read image from file
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image from {image_path}")
        elif image is None:
            raise ValueError("Either image_path or image must be provided")

        # Preprocess the image if requested
        if preprocess:
            image = self.preprocess_image(image)

        # Convert to PIL Image for pytesseract
        pil_img = Image.fromarray(image)

        try:
            # Use Tesseract to extract text and data
            data = pytesseract.image_to_data(pil_img, output_type=pytesseract.Output.DICT, lang=lang, config=config)

            # Calculate average confidence (excluding -1 values which indicate no text)
            confidences = [float(x) for x in data["conf"] if float(x) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0

            # Join all text lines
            text = "\n".join([line for line in data["text"] if line.strip()])

            return {"text": text, "confidence": avg_confidence, "data": data}

        except Exception as e:
            logger.error(f"Error during OCR processing: {e}")
            raise

    def extract_text_from_region(
        self, image: np.ndarray, x: int, y: int, width: int, height: int, **kwargs
    ) -> dict[str, Any]:
        """Extract text from a specific region of an image.

        Args:
            image: Input image as a numpy array
            x: X coordinate of the top-left corner
            y: Y coordinate of the top-left corner
            width: Width of the region
            height: Height of the region
            **kwargs: Additional arguments to pass to extract_text()

        Returns:
            Dictionary with OCR results (same as extract_text)

        """
        # Extract the region of interest
        roi = image[y : y + height, x : x + width]
        return self.extract_text(image=roi, **kwargs)

    def find_text_position(
        self,
        image: np.ndarray,
        search_text: str,
        lang: str = "eng",
        case_sensitive: bool = False,
    ) -> tuple[int, int, int, int] | None:
        """Find the position of specific text in an image.

        Args:
            image: Input image as a numpy array
            search_text: Text to search for
            lang: Language code for Tesseract
            case_sensitive: Whether the search should be case-sensitive

        Returns:
            Tuple of (x, y, width, height) of the found text, or None if not found

        """
        # Extract text with character-level positioning
        data = self.extract_text(image=image, lang=lang)["data"]

        if not case_sensitive:
            search_text = search_text.lower()

        # Search through each detected text element
        for i, text in enumerate(data["text"]):
            if not text.strip():
                continue

            current_text = text if case_sensitive else text.lower()

            if search_text in current_text:
                # Get the bounding box
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                return (x, y, w, h)

        return None
