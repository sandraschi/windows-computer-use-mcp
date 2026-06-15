"""OCR Text Extractor - Extract text from UI elements using OCR."""

import pytesseract
from PIL import Image


class OCRExtractor:
    """Extract text from UI elements using OCR."""

    def __init__(self, tesseract_cmd: str | None = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    def enhance_elements(self, elements: list[dict], screenshot: Image) -> list[dict]:
        """Add OCR text to elements without readable text."""
        for elem in elements:
            # Skip if already has good text
            if elem.get("name") and len(elem["name"].strip()) >= 2:
                continue

            # Extract text via OCR
            ocr_text = self._extract_text(elem, screenshot)
            if ocr_text:
                elem["ocr_text"] = ocr_text

        return elements

    def _extract_text(self, elem: dict, screenshot: Image) -> str:
        """OCR text from element region."""
        try:
            bounds = elem["bounds"]

            # Crop element region with padding
            padding = 2
            region = screenshot.crop(
                (
                    bounds["x"] - padding,
                    bounds["y"] - padding,
                    bounds["x"] + bounds["width"] + padding,
                    bounds["y"] + bounds["height"] + padding,
                )
            )

            # OCR with single line mode
            text = pytesseract.image_to_string(
                region,
                config="--psm 7",  # Single text line
            )

            return text.strip()

        except Exception:
            return ""
