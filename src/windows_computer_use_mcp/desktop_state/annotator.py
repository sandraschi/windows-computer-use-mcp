"""Screenshot Annotator - Annotate screenshots with UI element bounding boxes."""

import base64
import logging
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class ScreenshotAnnotator:
    """Annotate screenshots with UI element bounding boxes."""

    COLOR_MAP = {
        "Button": "#00FF00",  # Green
        "Edit": "#FFFF00",  # Yellow
        "Link": "#00FFFF",  # Cyan
        "ListItem": "#FF00FF",  # Magenta
        "MenuItem": "#FFA500",  # Orange
        "CheckBox": "#87CEEB",  # Sky Blue
        "RadioButton": "#DDA0DD",  # Plum
        "default": "#FFFFFF",  # White
    }

    def __init__(self, font_size: int = 12):
        self.font_size = font_size
        try:
            self.font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            self.font = ImageFont.load_default()

    def capture_and_annotate(self, elements: list[dict], *, bbox: tuple[int, int, int, int] | None = None) -> Image:
        """Capture screenshot and draw element annotations."""
        from PIL import ImageGrab

        try:
            if bbox:
                from windows_computer_use_mcp.win32_window import clamp_bbox
                clamped = clamp_bbox(bbox)
                screenshot = ImageGrab.grab(bbox=clamped)
            else:
                screenshot = ImageGrab.grab()
        except Exception as exc:
            logger.warning("Annotator grab failed (%s); falling back to full screen", exc)
            screenshot = ImageGrab.grab()

        draw = ImageDraw.Draw(screenshot)

        for elem in elements:
            self._draw_element(draw, elem)

        return screenshot

    def _draw_element(self, draw: ImageDraw, elem: dict):
        bounds = elem["bounds"]
        x = bounds["x"]
        y = bounds["y"]
        x2 = x + bounds["width"]
        y2 = y + bounds["height"]

        color = self.COLOR_MAP.get(elem["type"], self.COLOR_MAP["default"])

        draw.rectangle([x, y, x2, y2], outline=color, width=2)

        label = str(elem["id"])
        label_top = max(y - 18, 0)
        label_bottom = max(y - 2, label_top + 1)
        draw.rectangle([x, label_top, x + 30, label_bottom], fill=color)
        draw.text((x + 2, label_top + 2), label, fill="#000000", font=self.font)

    def to_base64(self, image: Image) -> str:
        """Convert image to base64 string."""
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()
