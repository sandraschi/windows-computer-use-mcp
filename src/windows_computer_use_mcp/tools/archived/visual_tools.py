"""Visual tools for PyWinAuto MCP.

This module provides visual tools for screen capture, image recognition, and
other visual automation tasks.
"""

import logging
import os
from typing import Any

import cv2
import numpy as np
import pyautogui
from pywinauto import Application
from typing_extensions import TypedDict


# Define a type for element info dict
class ElementInfo(TypedDict, total=False):
    rect: Any  # Can be a rectangle object with left, top, width, height
    x: int
    y: int
    width: int
    height: int
    class_name: str
    text: str
    control_id: int
    process_id: int
    is_visible: bool
    is_enabled: bool
    handle: int
    runtime_id: Any
    automation_id: str
    name: str
    control_type: str


# Import the FastMCP app instance from the app module
try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in visual_tools: {e}")
    app = None


def _nms_matches(matches: list, overlap_threshold: float = 0.5) -> list:
    """Apply non-maximum suppression to remove overlapping matches."""
    if not matches:
        return []

    # Convert to numpy array for easier calculations
    matches = np.array(matches)

    # If no scores, just return all matches
    if matches.size == 0:
        return []

    # Initialize the list of picked indexes
    pick = []

    # Grab the coordinates of the bounding boxes
    x1 = matches[:, 0]
    y1 = matches[:, 1]
    x2 = matches[:, 0] + matches[:, 2]
    y2 = matches[:, 1] + matches[:, 3]

    # Compute the area of the bounding boxes and sort by the bottom-right
    # y-coordinate of the bounding box
    area = (x2 - x1 + 1) * (y2 - y1 + 1)
    idxs = np.argsort(y2)

    # Keep looping while some indexes still remain in the indexes list
    while len(idxs) > 0:
        # Grab the last index in the indexes list and add the index value
        # to the list of picked indexes
        last = len(idxs) - 1
        i = idxs[last]
        pick.append(i)

        # Find the largest (x, y) coordinates for the start of the bounding
        # box and the smallest (x, y) coordinates for the end of the bounding box
        xx1 = np.maximum(x1[i], x1[idxs[:last]])
        yy1 = np.maximum(y1[i], y1[idxs[:last]])
        xx2 = np.minimum(x2[i], x2[idxs[:last]])
        yy2 = np.minimum(y2[i], y2[idxs[:last]])

        # Compute the width and height of the bounding box
        w = np.maximum(0, xx2 - xx1 + 1)
        h = np.maximum(0, yy2 - yy1 + 1)

        # Compute the ratio of overlap
        overlap = (w * h) / area[idxs[:last]]

        # Delete all indexes from the index list that have overlap greater than
        # the provided overlap threshold
        idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlap_threshold)[0])))

    # Return only the bounding boxes that were picked
    return matches[pick].tolist()


# Only register tools if app is available
if app is not None:

    @app.tool()
    def take_screenshot(region: dict[str, int] | None = None, save_path: str | None = None) -> dict:
        """Take a screenshot of the screen or a specific region.

        Args:
            region: Optional dict with 'left', 'top', 'width', 'height' to capture a specific region
            save_path: Optional path to save the screenshot

        Returns:
            dict: Status and screenshot information

        """
        try:
            if region:
                screenshot = pyautogui.screenshot(
                    region=(
                        region.get("left", 0),
                        region.get("top", 0),
                        region.get("width", 0),
                        region.get("height", 0),
                    )
                )
                region_info = region
            else:
                screenshot = pyautogui.screenshot()
                region_info = {
                    "left": 0,
                    "top": 0,
                    "width": screenshot.width,
                    "height": screenshot.height,
                }

            # Convert to numpy array for OpenCV if needed
            screenshot_np = np.array(screenshot)

            # Save the screenshot if path is provided
            if save_path:
                os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
                screenshot.save(save_path)

            return {
                "status": "success",
                "image": screenshot_np.tolist() if screenshot_np is not None else None,
                "region": region_info,
                "size": {"width": screenshot.width, "height": screenshot.height},
                "saved_path": save_path if save_path else None,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool(
        name="find_image_on_screen",
        description="Find an image on the screen using template matching.",
    )
    def find_image_on_screen(
        image_path: str,
        confidence: float = 0.8,
        grayscale: bool = False,
        region: dict[str, int] | None = None,
    ) -> dict:
        """Find an image on the screen using template matching.

        Args:
            image_path: Path to the template image to find
            confidence: Confidence threshold (0-1) for matching (default: 0.8)
            grayscale: Whether to convert images to grayscale for matching (faster)
            region: Optional dict with 'left', 'top', 'width', 'height' to search within

        Returns:
            dict: Status and match information

        """
        try:
            # Check if the template image exists
            if not os.path.exists(image_path):
                return {"status": "error", "error": f"Template image not found: {image_path}"}

            # Take a screenshot of the specified region or full screen
            screenshot_result = take_screenshot(region=region)
            if screenshot_result["status"] != "success":
                return screenshot_result

            screenshot = np.array(screenshot_result["image"])
            template = cv2.imread(image_path)

            if template is None:
                return {"status": "error", "error": "Failed to load template image"}

            # Convert to grayscale if requested
            if grayscale:
                screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
                template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

                # Perform template matching
                result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            else:
                # For color images, we'll use a multi-channel approach
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

            # Find all matches above the confidence threshold
            locations = np.where(result >= confidence)
            matches = []
            h, w = template.shape[:2]

            for pt in zip(*locations[::-1], strict=False):
                matches.append([pt[0], pt[1], w, h])

            # Apply non-maximum suppression to remove overlapping matches
            matches = _nms_matches(matches, overlap_threshold=0.5)

            # Convert matches to a list of dicts with position and size
            match_results = []
            for x, y, w, h in matches:
                match_results.append(
                    {
                        "x": int(x),
                        "y": int(y),
                        "width": int(w),
                        "height": int(h),
                        "center_x": int(x + w / 2),
                        "center_y": int(y + h / 2),
                    }
                )

            return {
                "status": "success",
                "matches_found": len(match_results),
                "matches": match_results,
                "confidence": confidence,
                "template_size": {"width": template.shape[1], "height": template.shape[0]},
                "search_region": region
                if region
                else {
                    "left": 0,
                    "top": 0,
                    "width": screenshot.shape[1],
                    "height": screenshot.shape[0],
                },
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool(
        name="get_text_under_cursor",
        description="Get text at the current cursor position using OCR.",
    )
    def get_text_under_cursor(region: dict[str, int] | None = None) -> dict:
        """Get text at the current cursor position using OCR.

        Args:
            region: Optional dict with 'width' and 'height' to define a region around the cursor

        Returns:
            dict: Status and extracted text

        """
        try:
            # Get the current cursor position
            x, y = pyautogui.position()

            # Define the region to capture around the cursor
            width = region.get("width", 200) if region else 200
            height = region.get("height", 100) if region else 100

            # Adjust the region to stay within screen bounds
            screen_width, screen_height = pyautogui.size()
            left = max(0, x - width // 2)
            top = max(0, y - height // 2)

            # Ensure the region doesn't go beyond screen bounds
            if left + width > screen_width:
                width = screen_width - left
            if top + height > screen_height:
                height = screen_height - top

            # Take a screenshot of the region
            screenshot = pyautogui.screenshot(region=(left, top, width, height))

            # Convert to grayscale for better OCR
            screenshot_gray = screenshot.convert("L")

            # Use pytesseract for OCR if available
            try:
                import pytesseract

                text = pytesseract.image_to_string(screenshot_gray)
                text = " ".join(text.split())  # Normalize whitespace
            except ImportError:
                # Fallback to simpler method if pytesseract is not available
                text = "OCR functionality requires pytesseract to be installed"

            return {
                "status": "success",
                "text": text.strip(),
                "position": {"x": x, "y": y},
                "region": {"left": left, "top": top, "width": width, "height": height},
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def get_ui_tree(max_depth: int = 3, app_param: Application | None = None) -> dict:
        """Get a hierarchical representation of the UI tree.

        Args:
            max_depth: Maximum depth to traverse the UI tree (default: 3)
            app_param: Optional Application instance to get UI tree from

        Returns:
            dict: Hierarchical UI tree structure

        """

        def get_element_info(element, depth=0):
            if depth > max_depth:
                return None

            try:
                element_info = {
                    "class_name": element.class_name(),
                    "text": element.window_text(),
                    "control_id": element.control_id(),
                    "process_id": element.process_id(),
                    "is_visible": element.is_visible(),
                    "is_enabled": element.is_enabled(),
                    "handle": element.handle,
                    "children": [],
                }

                # Add rectangle info if available
                try:
                    rect = element.rectangle()
                    element_info["rect"] = {
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": rect.width(),
                        "height": rect.height(),
                    }
                except Exception:
                    pass

                # Recursively get children
                if depth < max_depth:
                    for child in element.children():
                        child_info = get_element_info(child, depth + 1)
                        if child_info:
                            element_info["children"].append(child_info)

                return element_info

            except Exception as e:
                logger.error(f"Error getting element info: {e}")
                return None

        try:
            if app_param is None:
                app_param = Application(backend="uia").connect(active_only=True)

            # Get the main window
            main_window = app_param.top_window()

            # Build the UI tree
            ui_tree = get_element_info(main_window)

            return {"status": "success", "ui_tree": ui_tree, "max_depth": max_depth}

        except Exception as e:
            return {"status": "error", "error": str(e)}


# Add all tools to __all__
__all__ = ["find_image_on_screen", "get_text_under_cursor", "get_ui_tree", "take_screenshot"]
