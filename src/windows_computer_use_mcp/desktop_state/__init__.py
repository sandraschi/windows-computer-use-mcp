"""Desktop State Capture Module.

Provides comprehensive UI element discovery, visual annotations, and OCR capabilities
for Windows desktop automation.
"""

from .annotator import ScreenshotAnnotator
from .capture import DesktopStateCapture
from .formatter import DesktopStateFormatter
from .ocr import OCRExtractor
from .walker import UIElementWalker

# NEW: Visual state assessment for screenshot-based verification
try:
    from .visual_state import ActionResult, VisualAssessment, VisualChange, VisualStateAssessor

    VISUAL_STATE_AVAILABLE = True
except ImportError:
    VISUAL_STATE_AVAILABLE = False
    VisualStateAssessor = None
    ActionResult = None
    VisualAssessment = None
    VisualChange = None

__all__ = [
    "VISUAL_STATE_AVAILABLE",
    "ActionResult",
    "DesktopStateCapture",
    "DesktopStateFormatter",
    "OCRExtractor",
    "ScreenshotAnnotator",
    "UIElementWalker",
    "VisualAssessment",
    "VisualChange",
    "VisualStateAssessor",
]
