"""OCR API endpoints for text extraction from images.

This module provides endpoints for performing Optical Character Recognition (OCR)
on images, including text extraction, region-based extraction, and text search.
"""

import logging
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastmcp import mcp
from pydantic import BaseModel, Field

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from windows_computer_use_mcp.core.config import get_config  # noqa: E402
from windows_computer_use_mcp.services.ocr_service import OCRService  # noqa: E402

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router with OpenAPI tags
router = APIRouter(tags=["ocr"], prefix="/ocr")

# Initialize OCR service with configuration
config = get_config()
ocr_service = OCRService(tesseract_cmd=config.TESSERACT_CMD)


# Response Models
class OCRTextResult(BaseModel):
    """Result of text extraction from an image."""

    success: bool = Field(..., description="Whether the operation was successful")
    text: str = Field(..., description="Extracted text from the image")
    confidence: float = Field(..., description="Confidence score of the OCR result (0-100)")
    language: str = Field(..., description="Language code used for OCR")
    raw_data: dict[str, Any] | None = Field(None, description="Raw OCR data including bounding boxes and confidences")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "success": True,
                "text": "Hello, World!",
                "confidence": 95.5,
                "language": "eng",
            }
        }


class OCRRegionResult(OCRTextResult):
    """Result of text extraction from a specific region of an image."""

    region: dict[str, int] = Field(..., description="Region of interest where text was extracted from")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "success": True,
                "text": "Extracted text",
                "confidence": 90.0,
                "language": "eng",
                "region": {"x": 100, "y": 100, "width": 200, "height": 50},
            }
        }


class TextPositionResult(BaseModel):
    """Result of a text search within an image."""

    success: bool = Field(..., description="Whether the operation was successful")
    found: bool = Field(..., description="Whether the text was found in the image")
    search_text: str = Field(..., description="The text that was searched for")
    position: dict[str, int] | None = Field(None, description="Position of the found text (x, y, width, height)")
    confidence: float | None = Field(None, description="Confidence score of the match (0-100)")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "success": True,
                "found": True,
                "search_text": "Submit",
                "position": {"x": 150, "y": 200, "width": 100, "height": 30},
                "confidence": 92.5,
            }
        }


@mcp.tool("Extract text from an image")
@router.post(
    "/extract-text",
    response_model=OCRTextResult,
    status_code=status.HTTP_200_OK,
    summary="Extract text from an image",
    response_description="Extracted text and confidence score",
)
async def extract_text_from_image(
    file: UploadFile = File(..., description="Image file to process"),
    preprocess: bool = Query(True, description="Apply image preprocessing for better OCR results"),
    lang: str = Query("eng", description="Language code for OCR (e.g., 'eng', 'deu', 'fra')"),
) -> dict[str, Any]:
    """Extract text from an uploaded image file using OCR.

    This endpoint processes an image and returns the extracted text along with
    confidence scores. The image can be in any common format (JPEG, PNG, etc.).

    Args:
        file: The image file to process
        preprocess: Whether to apply image preprocessing for better OCR results
        lang: Language code for OCR (e.g., 'eng' for English, 'deu' for German)

    Returns:
        OCRTextResult: Extracted text, confidence score, and language

    Raises:
        HTTPException: If there's an error processing the image

    """
    try:
        logger.info("Processing image for text extraction")

        # Read the uploaded file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode the image file")

        # Extract text
        result = ocr_service.extract_text(image=image, preprocess=preprocess, lang=lang, config=config.TESSERACT_CONFIG)

        return {
            "success": True,
            "text": result["text"],
            "confidence": result["confidence"],
            "language": lang,
            "raw_data": result.get("data"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image: {e!s}",
        ) from e


@mcp.tool("Extract text from a specific region of an image")
@router.post(
    "/extract-region",
    response_model=OCRRegionResult,
    status_code=status.HTTP_200_OK,
    summary="Extract text from a specific region of an image",
    response_description="Extracted text and region information",
)
async def extract_text_from_region(
    file: UploadFile = File(..., description="Image file to process"),
    x: int = Query(..., ge=0, description="X coordinate of the top-left corner"),
    y: int = Query(..., ge=0, description="Y coordinate of the top-left corner"),
    width: int = Query(..., gt=0, description="Width of the region"),
    height: int = Query(..., gt=0, description="Height of the region"),
    preprocess: bool = Query(True, description="Apply image preprocessing for better OCR results"),
    lang: str = Query("eng", description="Language code for OCR (e.g., 'eng', 'deu', 'fra')"),
) -> dict[str, Any]:
    """Extract text from a specific region of an image using OCR.

    This endpoint processes a specific region of an image and returns the extracted text.
    The region is defined by its top-left corner (x, y) and dimensions (width, height).

    Args:
        file: The image file to process
        x: X coordinate of the top-left corner of the region
        y: Y coordinate of the top-left corner of the region
        width: Width of the region in pixels
        height: Height of the region in pixels
        preprocess: Whether to apply image preprocessing for better OCR results
        lang: Language code for OCR (e.g., 'eng' for English, 'deu' for German)

    Returns:
        OCRRegionResult: Extracted text, confidence score, and region information

    Raises:
        HTTPException: If there's an error processing the image or region is invalid

    """
    try:
        logger.info(f"Processing image region (x={x}, y={y}, w={width}, h={height}) for text extraction")

        # Read the uploaded file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode the image file")

        # Validate region coordinates
        img_height, img_width = image.shape[:2]
        if x + width > img_width or y + height > img_height:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Region (x={x}, y={y}, w={width}, h={height}) is outside "
                f"image boundaries ({img_width}x{img_height})",
            )

        # Extract text from the specified region
        result = ocr_service.extract_text_from_region(
            image=image,
            x=x,
            y=y,
            width=width,
            height=height,
            preprocess=preprocess,
            lang=lang,
            config=config.TESSERACT_CONFIG,
        )

        return {
            "success": True,
            "text": result["text"],
            "confidence": result["confidence"],
            "language": lang,
            "region": {"x": x, "y": y, "width": width, "height": height},
            "raw_data": result.get("data"),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image region: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image region: {e!s}",
        ) from e


@mcp.tool("Find the position of specific text in an image")
@router.post(
    "/find-text",
    response_model=TextPositionResult,
    status_code=status.HTTP_200_OK,
    summary="Find the position of specific text in an image",
    response_description="Position of the found text or not found status",
)
async def find_text_in_image(
    file: UploadFile = File(..., description="Image file to search in"),
    search_text: str = Query(..., description="Text to search for in the image"),
    lang: str = Query("eng", description="Language code for OCR"),
    case_sensitive: bool = Query(False, description="Whether the search should be case-sensitive"),
) -> dict[str, Any]:
    """Find the position of specific text within an image using OCR.

    This endpoint searches for the specified text in an image and returns
    its position if found. The search can be case-sensitive or case-insensitive.

    Args:
        file: The image file to search in
        search_text: The text to search for (required)
        lang: Language code for OCR (e.g., 'eng' for English, 'deu' for German)
        case_sensitive: Whether the search should be case-sensitive

    Returns:
        TextPositionResult: Position of the found text and confidence score

    Raises:
        HTTPException: If there's an error processing the image or if search_text is empty

    """
    if not search_text.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="search_text parameter cannot be empty")

    try:
        logger.info(f"Searching for text: '{search_text}' (case_sensitive={case_sensitive})")

        # Read the uploaded file
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not decode the image file")

        # Find the text position
        position = ocr_service.find_text_position(
            image=image,
            search_text=search_text,
            lang=lang,
            case_sensitive=case_sensitive,
            config=config.TESSERACT_CONFIG,
        )

        if position:
            x, y, w, h = position
            return {
                "success": True,
                "found": True,
                "search_text": search_text,
                "position": {"x": x, "y": y, "width": w, "height": h},
                "confidence": 0.0,  # Confidence would come from the OCR service
            }
        else:
            return {
                "success": True,
                "found": False,
                "search_text": search_text,
                "position": None,
                "confidence": None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching for text in image: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching for text in image: {e!s}",
        ) from e
