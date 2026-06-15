"""Element interaction tools for PyWinAuto MCP.

This module provides functions for interacting with UI elements within windows,
including clicking, double-clicking, right-clicking, and hovering.
"""

import logging
import time
from typing import Any

import pyautogui
from pywinauto.base_wrapper import ElementNotVisible
from pywinauto.controls.uia_controls import ButtonWrapper, ComboBoxWrapper, EditWrapper
from pywinauto.findwindows import ElementNotFoundError

# Import the FastMCP app instance from the main package
try:
    from windows_computer_use_mcp.main import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in element tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in element tools: {e}")
    app = None

# Only proceed with tool registration if app is available
if app is not None:
    logger.info("Registering element tools with FastMCP")

    def _get_element(window, control_id: str | None = None, x: int | None = None, y: int | None = None):
        """Get an element by control ID or coordinates.

        Args:
            window: The parent window
            control_id: The control ID
            x: X coordinate (if using coordinates)
            y: Y coordinate (if using coordinates)

        Returns:
            The UI element

        """
        try:
            if control_id is not None:
                return window.child_window(control_id=control_id)
            elif x is not None and y is not None:
                return window.from_point(x, y)
            else:
                raise ValueError("Either control_id or both x and y must be provided")
        except (ElementNotFoundError, ElementNotVisible) as e:
            logger.error(f"Element not found or not visible: {e}")
            raise
        except Exception as e:
            logger.error(f"Error getting element: {e}")
            raise

    @app.tool()
    def click_element(
        window_handle: int,
        control_id: str | None = None,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
        double: bool = False,
        absolute: bool = False,
    ) -> dict[str, Any]:
        """Click on a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element to click (optional if x and y are provided)
            x: X coordinate relative to the window (optional if control_id is provided)
            y: Y coordinate relative to the window (optional if control_id is provided)
            button: The mouse button to use ("left", "right", "middle")
            double: Whether to perform a double-click
            absolute: Whether the coordinates are screen-absolute (default: window-relative)

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)

            if control_id is not None:
                element = window.child_window(control_id=control_id)
                if not element.exists():
                    return {
                        "status": "error",
                        "error": f"Element with control_id '{control_id}' not found",
                        "error_type": "ElementNotFoundError",
                    }

                if double:
                    element.double_click(button=button)
                else:
                    element.click(button=button)

                return {
                    "status": "success",
                    "action": "double_click" if double else "click",
                    "control_id": control_id,
                    "button": button,
                    "timestamp": time.time(),
                }

            elif x is not None and y is not None:
                if absolute:
                    if double:
                        pyautogui.doubleClick(x, y, button=button)
                    else:
                        pyautogui.click(x, y, button=button)

                    return {
                        "status": "success",
                        "action": "double_click" if double else "click",
                        "x": x,
                        "y": y,
                        "absolute": True,
                        "button": button,
                        "timestamp": time.time(),
                    }
                else:
                    window_rect = window.rectangle()
                    screen_x = window_rect.left + x
                    screen_y = window_rect.top + y

                    if double:
                        pyautogui.doubleClick(screen_x, screen_y, button=button)
                    else:
                        pyautogui.click(screen_x, screen_y, button=button)

                    return {
                        "status": "success",
                        "action": "double_click" if double else "click",
                        "x": x,
                        "y": y,
                        "screen_x": screen_x,
                        "screen_y": screen_y,
                        "absolute": False,
                        "button": button,
                        "timestamp": time.time(),
                    }
            else:
                return {
                    "status": "error",
                    "error": "Either control_id or both x and y must be provided",
                    "error_type": "ValueError",
                }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except ElementNotVisible as e:
            return {
                "status": "error",
                "error": f"Element not visible: {e!s}",
                "error_type": "ElementNotVisible",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def double_click_element(
        window_handle: int,
        control_id: str | None = None,
        x: int | None = None,
        y: int | None = None,
        button: str = "left",
    ) -> dict[str, Any]:
        """Double-click on a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element to click (optional if x and y are provided)
            x: X coordinate relative to the window (optional if control_id is provided)
            y: Y coordinate relative to the window (optional if control_id is provided)
            button: The mouse button to use ("left", "right", "middle")

        Returns:
            Dict containing the result of the operation

        """
        return click_element(window_handle=window_handle, control_id=control_id, x=x, y=y, button=button, double=True)

    @app.tool()
    def right_click_element(
        window_handle: int,
        control_id: str | None = None,
        x: int | None = None,
        y: int | None = None,
    ) -> dict[str, Any]:
        """Right-click on a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element to click (optional if x and y are provided)
            x: X coordinate relative to the window (optional if control_id is provided)
            y: Y coordinate relative to the window (optional if control_id is provided)

        Returns:
            Dict containing the result of the operation

        """
        return click_element(window_handle=window_handle, control_id=control_id, x=x, y=y, button="right")

    @app.tool()
    def hover_element(
        window_handle: int,
        control_id: str | None = None,
        x: int | None = None,
        y: int | None = None,
        duration: float = 0.5,
    ) -> dict[str, Any]:
        """Hover the mouse over a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element to hover over (optional if x and y are provided)
            x: X coordinate relative to the window (optional if control_id is provided)
            y: Y coordinate relative to the window (optional if control_id is provided)
            duration: Duration of the hover in seconds

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)

            if control_id is not None:
                element = window.child_window(control_id=control_id)
                if not element.exists():
                    return {
                        "status": "error",
                        "error": f"Element with control_id '{control_id}' not found",
                        "error_type": "ElementNotFoundError",
                    }

                element.draw_outline()
                rect = element.rectangle()
                center_x = rect.left + (rect.width() // 2)
                center_y = rect.top + (rect.height() // 2)

                pyautogui.moveTo(center_x, center_y, duration=0.5)
                time.sleep(duration)

                return {
                    "status": "success",
                    "action": "hover",
                    "control_id": control_id,
                    "position": (center_x, center_y),
                    "duration": duration,
                    "timestamp": time.time(),
                }

            elif x is not None and y is not None:
                window_rect = window.rectangle()
                screen_x = window_rect.left + x
                screen_y = window_rect.top + y

                pyautogui.moveTo(screen_x, screen_y, duration=0.5)
                time.sleep(duration)

                return {
                    "status": "success",
                    "action": "hover",
                    "x": x,
                    "y": y,
                    "screen_x": screen_x,
                    "screen_y": screen_y,
                    "duration": duration,
                    "timestamp": time.time(),
                }
            else:
                return {
                    "status": "error",
                    "error": "Either control_id or both x and y must be provided",
                    "error_type": "ValueError",
                }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_element_info(window_handle: int, control_id: str) -> dict[str, Any]:
        """Get detailed information about a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element

        Returns:
            Dict containing element information

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)
            element = window.child_window(control_id=control_id)

            if not element.exists():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' not found",
                    "error_type": "ElementNotFoundError",
                }

            rect = element.rectangle()

            info = {
                "status": "success",
                "control_id": control_id,
                "class_name": element.class_name(),
                "text": element.window_text(),
                "is_visible": element.is_visible(),
                "is_enabled": element.is_enabled(),
                "has_keyboard_focus": element.has_keyboard_focus(),
                "position": {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.width(),
                    "height": rect.height(),
                },
                "timestamp": time.time(),
            }

            # Add element-specific properties
            if isinstance(element, ButtonWrapper):
                info["element_type"] = "button"
            elif isinstance(element, EditWrapper):
                info["element_type"] = "edit"
                info["is_readonly"] = element.is_read_only()
            elif isinstance(element, ComboBoxWrapper):
                info["element_type"] = "combobox"
                try:
                    info["items"] = element.item_texts()
                    info["selected_index"] = element.selected_index()
                    info["selected_text"] = element.selected_text()
                except:
                    pass

            return info

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_element_text(window_handle: int, control_id: str) -> dict[str, Any]:
        """Get the text of a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element

        Returns:
            Dict containing the element text

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)
            element = window.child_window(control_id=control_id)

            if not element.exists():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' not found",
                    "error_type": "ElementNotFoundError",
                }

            text = element.window_text()

            return {
                "status": "success",
                "control_id": control_id,
                "text": text,
                "length": len(text),
                "timestamp": time.time(),
            }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def set_element_text(window_handle: int, control_id: str, text: str) -> dict[str, Any]:
        """Set the text of a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element
            text: The text to set

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)
            element = window.child_window(control_id=control_id)

            if not element.exists():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' not found",
                    "error_type": "ElementNotFoundError",
                }

            if not element.is_enabled():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' is not enabled",
                    "error_type": "ElementNotEnabled",
                }

            if not element.is_visible():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' is not visible",
                    "error_type": "ElementNotVisible",
                }

            # Try to set the text directly first
            try:
                element.set_text(text)
                return {
                    "status": "success",
                    "control_id": control_id,
                    "text_set": text,
                    "length": len(text),
                    "method": "direct",
                    "timestamp": time.time(),
                }
            except:
                # Fall back to keyboard input if direct setting fails
                try:
                    element.set_focus()
                    element.type_keys("{VK_HOME}+{VK_SHIFT}{END}{DELETE}")  # Select all and delete
                    element.type_keys(text)
                    return {
                        "status": "success",
                        "control_id": control_id,
                        "text_set": text,
                        "length": len(text),
                        "method": "keyboard",
                        "timestamp": time.time(),
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "error": f"Failed to set text: {e!s}",
                        "error_type": type(e).__name__,
                    }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_element_rect(window_handle: int, control_id: str) -> dict[str, Any]:
        """Get the rectangle of a UI element.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element

        Returns:
            Dict containing the element rectangle

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)
            element = window.child_window(control_id=control_id)

            if not element.exists():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' not found",
                    "error_type": "ElementNotFoundError",
                }

            rect = element.rectangle()

            return {
                "status": "success",
                "control_id": control_id,
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.width(),
                "height": rect.height(),
                "timestamp": time.time(),
            }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def is_element_visible(window_handle: int, control_id: str) -> dict[str, Any]:
        """Check if a UI element is visible.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element

        Returns:
            Dict containing the visibility status

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)
            element = window.child_window(control_id=control_id)

            if not element.exists():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' not found",
                    "error_type": "ElementNotFoundError",
                }

            visible = element.is_visible()

            return {
                "status": "success",
                "control_id": control_id,
                "is_visible": visible,
                "timestamp": time.time(),
            }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def is_element_enabled(window_handle: int, control_id: str) -> dict[str, Any]:
        """Check if a UI element is enabled.

        Args:
            window_handle: The handle of the parent window
            control_id: The control ID of the element

        Returns:
            Dict containing the enabled status

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)
            element = window.child_window(control_id=control_id)

            if not element.exists():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' not found",
                    "error_type": "ElementNotFoundError",
                }

            enabled = element.is_enabled()

            return {
                "status": "success",
                "control_id": control_id,
                "is_enabled": enabled,
                "timestamp": time.time(),
            }

        except ElementNotFoundError as e:
            return {
                "status": "error",
                "error": f"Element not found: {e!s}",
                "error_type": "ElementNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_all_elements(window_handle: int, max_depth: int = 3) -> dict[str, Any]:
        """Get all UI elements in a window.

        Args:
            window_handle: The handle of the parent window
            max_depth: Maximum depth to traverse the element tree

        Returns:
            Dict containing information about all elements

        """

        def get_element_info(element, depth=0):
            if depth > max_depth:
                return None

            try:
                control_id = element.element_info.control_id
                class_name = element.class_name()
                text = element.window_text()

                info = {
                    "control_id": control_id,
                    "class_name": class_name,
                    "text": text,
                    "is_visible": element.is_visible(),
                    "is_enabled": element.is_enabled(),
                    "children": [],
                }

                # Get element type
                if isinstance(element, ButtonWrapper):
                    info["element_type"] = "button"
                elif isinstance(element, EditWrapper):
                    info["element_type"] = "edit"
                    info["is_readonly"] = element.is_read_only()
                elif isinstance(element, ComboBoxWrapper):
                    info["element_type"] = "combobox"
                    try:
                        info["items"] = element.item_texts()
                        info["selected_index"] = element.selected_index()
                        info["selected_text"] = element.selected_text()
                    except:
                        pass

                # Get position if available
                try:
                    rect = element.rectangle()
                    info["position"] = {
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": rect.width(),
                        "height": rect.height(),
                    }
                except:
                    pass

                # Recursively get children
                try:
                    children = element.children()
                    for child in children:
                        child_info = get_element_info(child, depth + 1)
                        if child_info:
                            info["children"].append(child_info)
                except:
                    pass

                return info

            except Exception as e:
                logger.warning(f"Error getting element info: {e}")
                return None

        try:
            desktop = get_desktop()
            window = desktop.window(handle=window_handle)

            if not window.exists():
                return {
                    "status": "error",
                    "error": f"Window with handle {window_handle} not found",
                    "error_type": "WindowNotFoundError",
                }

            # Start with the root element (window itself)
            elements = []
            try:
                children = window.children()
                for child in children:
                    element_info = get_element_info(child)
                    if element_info:
                        elements.append(element_info)
            except Exception as e:
                logger.warning(f"Error getting window children: {e}")

            return {
                "status": "success",
                "window_handle": window_handle,
                "element_count": len(elements),
                "elements": elements,
                "max_depth": max_depth,
                "timestamp": time.time(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}


def get_desktop():
    """Get a Desktop instance with proper error handling."""
    try:
        from pywinauto import Desktop

        return Desktop(backend="uia")
    except Exception as e:
        logger.error(f"Failed to get Desktop instance: {e}")
        raise


# Add all tools to __all__
__all__ = [
    "click_element",
    "double_click_element",
    "get_all_elements",
    "get_element_info",
    "get_element_rect",
    "get_element_text",
    "hover_element",
    "is_element_enabled",
    "is_element_visible",
    "right_click_element",
    "set_element_text",
]
