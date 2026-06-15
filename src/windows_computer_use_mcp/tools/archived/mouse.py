"""Mouse interaction tools for PyWinAuto MCP.

This module provides mouse-related functionality including movement, clicking, dragging, and scrolling.
"""

import logging
from typing import Any

import pyautogui
from typing_extensions import TypedDict


# Define a type for element info dict
class ElementInfo(TypedDict, total=False):
    rect: Any  # Can be a rectangle object with left, top, width, height
    x: int
    y: int
    width: int
    height: int


# Import the FastMCP app instance from the app module
try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in mouse tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in mouse tools: {e}")
    app = None

# Set default delay between mouse actions
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True

# Only proceed with tool registration if app is available
if app is not None:
    logger.info("Registering mouse tools with FastMCP")

    @app.tool()
    def mouse_move_relative(x: int, y: int) -> dict[str, Any]:
        """Move mouse relative to current position.

        Args:
            x: Pixels to move horizontally (positive = right, negative = left)
            y: Pixels to move vertically (positive = down, negative = up)

        Returns:
            dict: Status and new position

        """
        try:
            current_x, current_y = pyautogui.position()
            new_x = current_x + x
            new_y = current_y + y
            pyautogui.moveTo(new_x, new_y)
            return {
                "status": "success",
                "position": (new_x, new_y),
                "moved_from": (current_x, current_y),
                "offset": (x, y),
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def mouse_move_to_element(element: ElementInfo, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        """Move mouse to a UI element.

        Args:
            element: Element info dict with rect/position
            x: Optional x offset from element's center
            y: Optional y offset from element's center

        Returns:
            dict: Status and position

        """
        try:
            # Handle different element info formats
            if "rect" in element and hasattr(element["rect"], "left"):
                # Handle rectangle object
                rect = element["rect"]
                center_x = rect.left + (rect.width() // 2)
                center_y = rect.top + (rect.height() // 2)
            elif all(k in element for k in ["x", "y", "width", "height"]):
                # Handle dict with coordinates
                center_x = element["x"] + (element["width"] // 2)
                center_y = element["y"] + (element["height"] // 2)
            else:
                raise ValueError("Invalid element format. Must contain 'rect' or x/y/width/height")

            target_x = center_x + (x if x is not None else 0)
            target_y = center_y + (y if y is not None else 0)

            pyautogui.moveTo(target_x, target_y)

            return {
                "status": "success",
                "position": (target_x, target_y),
                "element_center": (center_x, center_y),
                "offset": (x or 0, y or 0),
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def mouse_hover(element: ElementInfo, duration: float = 0.5) -> dict[str, Any]:
        """Hover over an element.

        Args:
            element: Element info dict with rect/position
            duration: Time in seconds to hover (default: 0.5)

        Returns:
            dict: Status and hover position

        """
        try:
            # Handle different element info formats
            if "rect" in element and hasattr(element["rect"], "left"):
                # Handle rectangle object
                rect = element["rect"]
                center_x = rect.left + (rect.width() // 2)
                center_y = rect.top + (rect.height() // 2)
            elif all(k in element for k in ["x", "y", "width", "height"]):
                # Handle dict with coordinates
                center_x = element["x"] + (element["width"] // 2)
                center_y = element["y"] + (element["height"] // 2)
            else:
                raise ValueError("Invalid element format. Must contain 'rect' or x/y/width/height")

            pyautogui.moveTo(center_x, center_y, duration=duration)

            return {"status": "success", "position": (center_x, center_y), "duration": duration}
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def drag_and_drop(source: ElementInfo, target: ElementInfo, duration: float = 0.5) -> dict[str, Any]:
        """Drag from source to target element.

        Args:
            source: Source element info dict with rect/position
            target: Target element info dict with rect/position
            duration: Duration of the drag in seconds (default: 0.5)

        Returns:
            dict: Status and positions

        """
        try:
            # Get source center
            if "rect" in source and hasattr(source["rect"], "left"):
                # Handle rectangle object
                src_rect = source["rect"]
                src_x = src_rect.left + (src_rect.width() // 2)
                src_y = src_rect.top + (src_rect.height() // 2)
            elif all(k in source for k in ["x", "y", "width", "height"]):
                # Handle dict with coordinates
                src_x = source["x"] + (source["width"] // 2)
                src_y = source["y"] + (source["height"] // 2)
            else:
                raise ValueError("Invalid source element format. Must contain 'rect' or x/y/width/height")

            # Get target center
            if "rect" in target and hasattr(target["rect"], "left"):
                # Handle rectangle object
                tgt_rect = target["rect"]
                tgt_x = tgt_rect.left + (tgt_rect.width() // 2)
                tgt_y = tgt_rect.top + (tgt_rect.height() // 2)
            elif all(k in target for k in ["x", "y", "width", "height"]):
                # Handle dict with coordinates
                tgt_x = target["x"] + (target["width"] // 2)
                tgt_y = target["y"] + (target["height"] // 2)
            else:
                raise ValueError("Invalid target element format. Must contain 'rect' or x/y/width/height")

            # Perform drag and drop
            pyautogui.moveTo(src_x, src_y)
            pyautogui.dragTo(tgt_x, tgt_y, duration=duration, button="left")

            return {
                "status": "success",
                "source_position": (src_x, src_y),
                "target_position": (tgt_x, tgt_y),
                "duration": duration,
            }
        except Exception as e:
            # Ensure mouse button is released on error
            try:
                pyautogui.mouseUp(button="left")
            except:
                pass

            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def right_click(element: ElementInfo | None = None, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        """Right-click on an element or at specific coordinates.

        Args:
            element: Optional element info dict to click on
            x: X coordinate (if element not provided)
            y: Y coordinate (if element not provided)

        Returns:
            dict: Status and click position

        """
        try:
            if element is not None:
                if "rect" in element and hasattr(element["rect"], "left"):
                    # Handle rectangle object
                    rect = element["rect"]
                    x = rect.left + (rect.width() // 2)
                    y = rect.top + (rect.height() // 2)
                elif all(k in element for k in ["x", "y", "width", "height"]):
                    # Handle dict with coordinates
                    x = element["x"] + (element["width"] // 2)
                    y = element["y"] + (element["height"] // 2)
                else:
                    raise ValueError("Invalid element format. Must contain 'rect' or x/y/width/height")
            elif x is not None and y is not None:
                pass  # Use provided coordinates
            else:
                # Click at current position if no element or coordinates provided
                x, y = pyautogui.position()

            pyautogui.rightClick(x, y)

            return {"status": "success", "position": (x, y), "action": "right_click"}
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def double_click(element: ElementInfo | None = None, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        """Double-click on an element or at specific coordinates.

        Args:
            element: Optional element info dict to click on
            x: X coordinate (if element not provided)
            y: Y coordinate (if element not provided)

        Returns:
            dict: Status and click position

        """
        try:
            if element is not None:
                if "rect" in element and hasattr(element["rect"], "left"):
                    # Handle rectangle object
                    rect = element["rect"]
                    x = rect.left + (rect.width() // 2)
                    y = rect.top + (rect.height() // 2)
                elif all(k in element for k in ["x", "y", "width", "height"]):
                    # Handle dict with coordinates
                    x = element["x"] + (element["width"] // 2)
                    y = element["y"] + (element["height"] // 2)
                else:
                    raise ValueError("Invalid element format. Must contain 'rect' or x/y/width/height")
            elif x is not None and y is not None:
                pass  # Use provided coordinates
            else:
                # Click at current position if no element or coordinates provided
                x, y = pyautogui.position()

            pyautogui.doubleClick(x, y)

            return {"status": "success", "position": (x, y), "action": "double_click", "clicks": 2}
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def mouse_scroll(amount: int, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        """Scroll the mouse wheel.

        Args:
            amount: Number of 'clicks' to scroll (positive = up, negative = down)
            x: Optional X coordinate to move to before scrolling
            y: Optional Y coordinate to move to before scrolling

        Returns:
            dict: Status and scroll position

        """
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
                position = (x, y)
            else:
                position = pyautogui.position()

            pyautogui.scroll(amount)

            return {"status": "success", "position": position, "scroll_amount": amount}
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_cursor_position() -> dict[str, Any]:
        """Get current cursor position.

        Returns:
            dict: Current cursor position (x, y)

        """
        try:
            x, y = pyautogui.position()
            return {"status": "success", "position": (x, y), "x": x, "y": y}
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}


# Add all tools to __all__
__all__ = [
    "double_click",
    "drag_and_drop",
    "get_cursor_position",
    "mouse_hover",
    "mouse_move_relative",
    "mouse_move_to_element",
    "mouse_scroll",
    "right_click",
]
