"""OCR-related Pydantic models for request/response validation."""

from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class OCRResult(BaseModel):
    """Result of an OCR operation."""

    text: str = Field(..., description="Extracted text from the image")
    confidence: float = Field(..., description="Average confidence of the OCR result (0-100)")
    language: str = Field(..., description="Language used for OCR")
    raw_data: dict[str, Any] | None = Field(
        None, description="Raw Tesseract OCR data including bounding boxes and confidences"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            # Handle any non-serializable data in raw_data
            dict: lambda v: {k: str(v) for k, v in v.items()}
        }


class OCRRequest(BaseModel):
    """Request model for OCR operations."""

    image_url: HttpUrl | None = Field(
        None, description="URL of the image to process (mutually exclusive with image_data)"
    )
    image_data: str | None = Field(None, description="Base64-encoded image data (mutually exclusive with image_url)")
    language: str = Field("eng", description="Language code for OCR (e.g., 'eng', 'deu', 'fra')")
    preprocess: bool = Field(True, description="Whether to preprocess the image for better OCR results")
    config: str = Field("--psm 6 --oem 3", description="Tesseract configuration parameters")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "image_url": "https://example.com/image.png",
                "language": "eng",
                "preprocess": True,
                "config": "--psm 6 --oem 3",
            }
        }


class OCRRegionRequest(OCRRequest):
    """Request model for OCR on a specific image region."""

    x: int = Field(..., ge=0, description="X coordinate of the top-left corner")
    y: int = Field(..., ge=0, description="Y coordinate of the top-left corner")
    width: int = Field(..., gt=0, description="Width of the region")
    height: int = Field(..., gt=0, description="Height of the region")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "image_url": "https://example.com/image.png",
                "x": 100,
                "y": 200,
                "width": 300,
                "height": 100,
                "language": "eng",
            }
        }


class TextPositionRequest(OCRRequest):
    """Request model for finding text position in an image."""

    search_text: str = Field(..., description="Text to search for in the image")
    case_sensitive: bool = Field(False, description="Whether the search should be case-sensitive")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "image_url": "https://example.com/image.png",
                "search_text": "Submit",
                "case_sensitive": False,
                "language": "eng",
            }
        }


class TextPositionResult(BaseModel):
    """Result of a text position search."""

    found: bool = Field(..., description="Whether the text was found")
    x: int | None = Field(None, description="X coordinate of the text")
    y: int | None = Field(None, description="Y coordinate of the text")
    width: int | None = Field(None, description="Width of the text region")
    height: int | None = Field(None, description="Height of the text region")
    confidence: float | None = Field(None, description="Confidence of the text match (0-100)")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "found": True,
                "x": 150,
                "y": 250,
                "width": 200,
                "height": 30,
                "confidence": 95.5,
            }
        }
