"""Desktop State Capture - Main orchestrator for desktop state capture."""

from typing import Literal

from .annotator import ScreenshotAnnotator
from .formatter import DesktopStateFormatter
from .ocr import OCRExtractor
from .walker import UIElementWalker

CaptureMode = Literal["ax", "som", "vision"]


class DesktopStateCapture:
    """Main desktop state capture orchestrator."""

    def __init__(self, max_depth: int = 10, element_timeout: float = 0.5, tesseract_cmd: str | None = None):
        self.walker = UIElementWalker(max_depth, element_timeout)
        self.annotator = ScreenshotAnnotator()
        self.ocr = OCRExtractor(tesseract_cmd)
        self.formatter = DesktopStateFormatter()

    def capture(
        self,
        use_vision: bool = False,
        use_ocr: bool = False,
        *,
        capture_mode: CaptureMode | None = None,
        window_handle: int | None = None,
    ) -> dict:
        """Capture desktop or single-window state.

        Args:
            use_vision: Legacy flag — include annotated screenshot (som)
            use_ocr: Use OCR to enrich elements
            capture_mode: Cua-style mode: ax | som | vision (overrides use_* when set)
            window_handle: Scope capture to one HWND when set

        Returns:
            Dictionary with text report, element data, and optional screenshot

        """
        mode = capture_mode or _legacy_capture_mode(use_vision, use_ocr)

        if mode == "vision":
            elements: list[dict] = []
            screenshot = self._grab_scope(window_handle)
            formatted = self.formatter.format(elements, screenshot, capture_mode=mode)
            formatted["capture_mode"] = mode
            return formatted

        if window_handle is not None:
            elements = self.walker.walk_window(window_handle)
        else:
            elements = self.walker.walk()

        screenshot = None
        if mode == "som":
            from windows_computer_use_mcp.dispatch import should_avoid_foreground_reads
            from windows_computer_use_mcp.win32_window import get_window_bbox, grab_window_image

            bbox = None
            if window_handle is not None:
                try:
                    bbox = get_window_bbox(window_handle)
                except Exception:
                    bbox = None
            screenshot = grab_window_image(
                window_handle,
                avoid_foreground=should_avoid_foreground_reads(),
            )
            if use_ocr:
                elements = self.ocr.enhance_elements(elements, screenshot)
            screenshot = self.annotator.capture_and_annotate(elements, bbox=bbox)

        output = self.formatter.format(elements, screenshot)
        output["capture_mode"] = mode
        return output

    def _grab_scope(self, window_handle: int | None):
        """Screenshot for vision-only mode (window rect when scoped)."""
        from windows_computer_use_mcp.dispatch import should_avoid_foreground_reads
        from windows_computer_use_mcp.win32_window import grab_window_image

        return grab_window_image(
            window_handle,
            avoid_foreground=should_avoid_foreground_reads(),
        )


def _legacy_capture_mode(use_vision: bool, use_ocr: bool) -> CaptureMode:
    if use_vision or use_ocr:
        return "som"
    return "ax"


def normalize_elements_for_snapshot(elements: list[dict]) -> list[dict]:
    """Assign element_index and snapshot-friendly fields."""
    out: list[dict] = []
    for idx, elem in enumerate(elements):
        row = dict(elem)
        row["element_index"] = idx
        row.pop("id", None)
        out.append(row)
    return out
