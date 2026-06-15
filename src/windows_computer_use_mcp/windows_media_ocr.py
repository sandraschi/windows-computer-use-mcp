"""Windows Media OCR provider — placeholder for future integration.

Windows.Media.Ocr is available on every Windows 10/11 system, but calling
it from Python requires WinRT async interop. Current approaches:
- PowerShell 5.1: engine is available (verified) but async GetResults() fails
- csc.exe compilation: requires .NET SDK with WinRT references
- pythonnet: WinRT type import fails with current version

Tesseract remains the default OCR provider for now.
Windows Media OCR integration is tracked as a future enhancement.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def is_available() -> bool:
    """Windows Media OCR is detected on this system but not yet callable from Python."""
    return False


def extract_text(image_path: str | Path) -> str:
    """Not implemented — Windows Media OCR requires WinRT async interop."""
    raise RuntimeError(
        "Windows Media OCR is not yet integrated. "
        "Use Tesseract (default) or set WINDOWS_COMPUTER_USE_MCP_OCR_PROVIDER=tesseract."
    )
