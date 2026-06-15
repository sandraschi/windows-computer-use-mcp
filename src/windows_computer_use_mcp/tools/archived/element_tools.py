"""UI Element tools for PyWinAuto MCP.

This module provides tools for interacting with and validating UI elements.
"""

import logging
import time
from typing import Any

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
    logger.error(f"Failed to import FastMCP app in element_tools: {e}")
    app = None


def _get_element_info(element) -> ElementInfo:
    """Extract relevant information from a UI element."""
    element_info: ElementInfo = {}

    try:
        # Handle both element objects and dicts
        if hasattr(element, "class_name"):
            # It's a UI element object
            element_info = {
                "class_name": element.class_name(),
                "text": element.window_text(),
                "control_id": element.control_id(),
                "process_id": element.process_id(),
                "is_visible": element.is_visible(),
                "is_enabled": element.is_enabled(),
                "handle": element.handle,
                "runtime_id": element.runtime_id() if hasattr(element, "runtime_id") else None,
                "automation_id": element.automation_id() if hasattr(element, "automation_id") else None,
                "name": element.element_info.name if hasattr(element, "element_info") else None,
                "control_type": str(element.element_info.control_type) if hasattr(element, "element_info") else None,
            }

            try:
                rect = element.rectangle()
                element_info.update({"x": rect.left, "y": rect.top, "width": rect.width(), "height": rect.height()})
            except Exception:
                pass
        elif isinstance(element, dict):
            # It's already a dict, just ensure it has the right structure
            element_info = element
    except Exception as e:
        logger.error(f"Error getting element info: {e}")

    return element_info


# Only register tools if app is available
if app is not None:

    @app.tool()
    def element_exists(
        selector: str | ElementInfo, timeout: float = 5.0, app_param: Application | None = None
    ) -> dict[str, Any]:
        """Check if a UI element exists.

        Args:
            selector: Element selector (title, class_name, or dict of properties)
            timeout: Maximum time to wait for element (default: 5 seconds)
            app_param: Optional Application instance to use for finding the element

        Returns:
            dict: Status and existence information

        """
        start_time = time.time()
        last_error = None

        while time.time() - start_time < timeout:
            try:
                if app_param is None:
                    app_param = Application(backend="uia").connect(active_only=True)

                if isinstance(selector, dict):
                    element = app_param.window(**selector)
                elif isinstance(selector, str):
                    # Try to find by title first, then by class name
                    try:
                        element = app_param.window(title=selector)
                        if not element.exists():
                            element = app_param.window(class_name=selector)
                    except Exception:
                        element = app_param.window(class_name=selector)
                else:
                    return {
                        "status": "error",
                        "message": "Invalid selector type. Must be string or dict.",
                    }

                if element.exists():
                    return {
                        "status": "success",
                        "exists": True,
                        "element": _get_element_info(element),
                    }

            except Exception as e:
                last_error = str(e)
                time.sleep(0.1)

        return {
            "status": "success" if last_error is None else "error",
            "exists": False,
            "message": last_error or f"Element not found within {timeout} seconds",
        }

    @app.tool()
    def wait_for_element(
        selector: str | ElementInfo, timeout: float = 10.0, app_param: Application | None = None
    ) -> dict[str, Any]:
        """Wait for a UI element to appear.

        Args:
            selector: Element selector (title, class_name, or dict of properties)
            timeout: Maximum time to wait in seconds (default: 10)
            app_param: Optional Application instance to use for finding the element

        Returns:
            dict: Status and element information if found

        """
        result = element_exists(selector, timeout, app_param)
        if result.get("exists", False):
            return {"status": "success", "element": result["element"]}
        else:
            return {"status": "error", "message": f"Element not found within {timeout} seconds"}

    @app.tool()
    def verify_text(
        selector: str | ElementInfo,
        expected_text: str,
        exact_match: bool = True,
        timeout: float = 5.0,
        app_param: Application | None = None,
    ) -> dict[str, Any]:
        """Verify that an element contains the expected text.

        Args:
            selector: Element selector (title, class_name, or dict of properties)
            expected_text: Text to verify
            exact_match: If True, text must match exactly (default: True)
            timeout: Maximum time to wait for element (default: 5 seconds)
            app_param: Optional Application instance to use for finding the element

        Returns:
            dict: Status and verification result

        """
        result = wait_for_element(selector, timeout, app_param)
        if result["status"] != "success":
            return result

        element_info = result["element"]
        actual_text = element_info.get("text", "")

        if exact_match:
            text_matches = actual_text == expected_text
        else:
            text_matches = expected_text.lower() in actual_text.lower()

        return {
            "status": "success" if text_matches else "failure",
            "expected_text": expected_text,
            "actual_text": actual_text,
            "exact_match": exact_match,
            "match_found": text_matches,
        }

    @app.tool()
    def get_element_rect(
        selector: str | ElementInfo, timeout: float = 5.0, app_param: Application | None = None
    ) -> dict[str, Any]:
        """Get the position and size of a UI element.

        Args:
            selector: Element selector (title, class_name, or dict of properties)
            timeout: Maximum time to wait for element (default: 5 seconds)
            app_param: Optional Application instance to use for finding the element

        Returns:
            dict: Status and rectangle information

        """
        result = wait_for_element(selector, timeout, app_param)
        if result["status"] != "success":
            return result

        element_info = result["element"]
        if "rect" not in element_info:
            return {"status": "error", "message": "Element does not have rectangle information"}

        rect = element_info["rect"]
        return {
            "status": "success",
            "rect": rect,
            "width": rect["right"] - rect["left"],
            "height": rect["bottom"] - rect["top"],
            "position": {"x": rect["left"], "y": rect["top"]},
        }


# Add all tools to __all__
__all__ = ["element_exists", "get_element_rect", "verify_text", "wait_for_element"]
