"""Windows Media OCR provider — uses built-in Windows.Media.Ocr API via PyWinRT.

Available on every Windows 10/11 system. Zero external dependencies beyond
the winrt-* packages installed from PyPI.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_AVAILABLE: bool | None = None


def is_available() -> bool:
    """Check if Windows Media OCR is available (Windows 10/11 only)."""
    global _AVAILABLE
    if _AVAILABLE is not None:
        return _AVAILABLE
    if sys.platform != "win32":
        _AVAILABLE = False
        return False
    try:
        from winrt.windows.media.ocr import OcrEngine

        engine = OcrEngine.try_create_from_user_profile_languages()
        _AVAILABLE = engine is not None
    except Exception as e:
        logger.debug("Windows Media OCR not available: %s", e)
        _AVAILABLE = False
    return _AVAILABLE


def extract_text(image_path: str | Path) -> str:
    """Run Windows Media OCR on an image file and return detected text.

    Uses PyWinRT async API via asyncio internally.
    """
    from winrt.windows.globalization import Language
    from winrt.windows.graphics.imaging import BitmapDecoder
    from winrt.windows.media.ocr import OcrEngine
    from winrt.windows.storage import StorageFile

    engine = OcrEngine.try_create_from_language(Language("en"))
    if engine is None:
        engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        raise RuntimeError("No OCR engine available")

    async def _run() -> str:
        file = await StorageFile.get_file_from_path_async(str(Path(image_path).resolve()))
        stream = await file.open_read_async()
        decoder = await BitmapDecoder.create_async(stream)
        bmp = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bmp)
        return "\n".join(line.text for line in result.lines)

    return asyncio.run(_run())
