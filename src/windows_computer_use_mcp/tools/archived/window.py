"""Window management tools for PyWinAuto MCP.

This module provides functions for managing windows, including maximizing,
minimizing, restoring, and setting window positions.
"""

import logging
import time
from typing import Any

from pywinauto import WindowNotFoundError

# Import the FastMCP app instance from the main package
try:
    from windows_computer_use_mcp.main import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in window tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in window tools: {e}")
    app = None

# Only proceed with tool registration if app is available
if app is not None:
    logger.info("Registering window tools with FastMCP")

    @app.tool()
    def maximize_window(handle: int) -> dict[str, Any]:
        """Maximize a window.

        Args:
            handle: The window handle to maximize

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            window.maximize()

            return {
                "status": "success",
                "handle": handle,
                "action": "maximized",
                "timestamp": time.time(),
            }

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def minimize_window(handle: int) -> dict[str, Any]:
        """Minimize a window.

        Args:
            handle: The window handle to minimize

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            window.minimize()

            return {
                "status": "success",
                "handle": handle,
                "action": "minimized",
                "timestamp": time.time(),
            }

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def restore_window(handle: int) -> dict[str, Any]:
        """Restore a window to its normal state.

        Args:
            handle: The window handle to restore

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            window.restore()

            return {
                "status": "success",
                "handle": handle,
                "action": "restored",
                "timestamp": time.time(),
            }

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def set_window_position(handle: int, x: int, y: int, width: int, height: int) -> dict[str, Any]:
        """Set the position and size of a window.

        Args:
            handle: The window handle
            x: The x-coordinate of the top-left corner
            y: The y-coordinate of the top-left corner
            width: The width of the window
            height: The height of the window

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            window.move(x, y, width, height)

            return {
                "status": "success",
                "handle": handle,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "action": "position_set",
                "timestamp": time.time(),
            }

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_active_window() -> dict[str, Any]:
        """Get the currently active window.

        Returns:
            Dict containing information about the active window

        """
        try:
            desktop = get_desktop()
            window = desktop.window(active_only=True)

            if not window.exists():
                return {
                    "status": "error",
                    "error": "No active window found",
                    "error_type": "NoActiveWindow",
                }

            rect = window.rectangle()

            return {
                "status": "success",
                "handle": window.handle,
                "title": window.window_text(),
                "class_name": window.class_name(),
                "is_visible": window.is_visible(),
                "is_enabled": window.is_enabled(),
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

        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def close_window(handle: int) -> dict[str, Any]:
        """Close a window.

        Args:
            handle: The window handle to close

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            window.close()

            return {
                "status": "success",
                "handle": handle,
                "action": "closed",
                "timestamp": time.time(),
            }

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_window_rect(handle: int) -> dict[str, Any]:
        """Get the rectangle of a window.

        Args:
            handle: The window handle

        Returns:
            Dict containing the window rectangle

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            rect = window.rectangle()

            return {
                "status": "success",
                "handle": handle,
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.width(),
                "height": rect.height(),
                "timestamp": time.time(),
            }

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_window_title(handle: int) -> dict[str, Any]:
        """Get the title of a window.

        Args:
            handle: The window handle

        Returns:
            Dict containing the window title

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            title = window.window_text()

            return {"status": "success", "handle": handle, "title": title, "timestamp": time.time()}

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool(
        name="get_window_state",
        description="Gets the state of a window (minimized, maximized, etc.)",
    )
    def get_window_state(handle: int) -> dict[str, Any]:
        """Get the state of a window.

        Args:
            handle: The window handle

        Returns:
            Dict containing the window state

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)

            state = {
                "is_maximized": window.is_maximized(),
                "is_minimized": window.is_minimized(),
                "is_visible": window.is_visible(),
                "is_enabled": window.is_enabled(),
                "has_focus": window.has_focus(),
            }

            return {"status": "success", "handle": handle, "state": state, "timestamp": time.time()}

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool(
        name="set_window_foreground",
        description="Brings a window to the foreground and activates it.",
    )
    def set_window_foreground(handle: int) -> dict[str, Any]:
        """Bring a window to the foreground and activate it.

        Args:
            handle: The window handle

        Returns:
            Dict containing the result of the operation

        """
        try:
            desktop = get_desktop()
            window = desktop.window(handle=handle)
            window.set_focus()
            window.activate()

            return {
                "status": "success",
                "handle": handle,
                "action": "brought_to_foreground",
                "timestamp": time.time(),
            }

        except WindowNotFoundError:
            return {
                "status": "error",
                "error": f"Window with handle {handle} not found",
                "error_type": "WindowNotFoundError",
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_all_windows() -> dict[str, Any]:
        """Get information about all visible windows.

        Returns:
            Dict containing information about all visible windows

        """
        try:
            desktop = get_desktop()
            windows = desktop.windows()

            result = []
            for window in windows:
                if not window.is_visible():
                    continue

                try:
                    rect = window.rectangle()
                    result.append(
                        {
                            "handle": window.handle,
                            "title": window.window_text(),
                            "class_name": window.class_name(),
                            "is_visible": window.is_visible(),
                            "is_enabled": window.is_enabled(),
                            "position": {
                                "left": rect.left,
                                "top": rect.top,
                                "right": rect.right,
                                "bottom": rect.bottom,
                                "width": rect.width(),
                                "height": rect.height(),
                            },
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error getting window info: {e}")
                    continue

            return {
                "status": "success",
                "window_count": len(result),
                "windows": result,
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
    "close_window",
    "get_active_window",
    "get_all_windows",
    "get_window_rect",
    "get_window_state",
    "get_window_title",
    "maximize_window",
    "minimize_window",
    "restore_window",
    "set_window_foreground",
    "set_window_position",
]
