"""Input tools for PyWinAuto MCP.

This module provides functions for simulating keyboard input, mouse movements,
and other input-related operations.
"""

import logging
import time
from typing import Any

import pywinauto.keyboard as keyboard
import pywinauto.mouse as mouse
from pywinauto.base_wrapper import ElementNotVisible
from pywinauto.findwindows import ElementNotFoundError

# Import the FastMCP app instance from the main package
try:
    from windows_computer_use_mcp.main import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in input tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in input tools: {e}")
    app = None

# Only proceed with tool registration if app is available
if app is not None:
    logger.info("Registering input tools with FastMCP")

    @app.tool(
        name="type_text",
        description="Types text at the current keyboard focus or a specified element.",
    )
    def type_text(
        text: str,
        window_handle: int | None = None,
        control_id: str | None = None,
        pause: float = 0.1,
    ) -> dict[str, Any]:
        """Types text at the current keyboard focus or a specified element.

        Args:
            text: The text to type
            window_handle: Optional window handle to type into
            control_id: Optional control ID to type into
            pause: Pause after typing in seconds

        Returns:
            Dict containing the result of the operation

        """
        try:
            if window_handle is not None and control_id is not None:
                # Type into a specific control
                desktop = get_desktop()
                window = desktop.window(handle=window_handle)
                control = window.child_window(control_id=control_id)
                control.type_keys(text, with_spaces=True, with_newlines=True, pause=pause)
            else:
                # Type at current keyboard focus
                keyboard.send_keys(text, pause=pause, with_spaces=True, with_newlines=True)

            return {
                "status": "success",
                "action": "type_text",
                "text_length": len(text),
                "window_handle": window_handle,
                "control_id": control_id,
                "timestamp": time.time(),
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
    def press_key(keys: str | list[str], presses: int = 1, interval: float = 0.1, pause: float = 0.1) -> dict[str, Any]:
        """Press a key or combination of keys.

        Args:
            keys: The key or list of keys to press (e.g., 'a', 'ctrl+c', ['ctrl', 'c'])
            presses: Number of times to press the key(s)
            interval: Delay between repeated presses in seconds
            pause: Pause after pressing in seconds

        Returns:
            Dict containing the result of the operation

        """
        try:
            if isinstance(keys, str):
                keys = [keys]

            for _ in range(presses):
                for key in keys:
                    keyboard.send_keys(key, pause=pause)
                if interval > 0 and _ < presses - 1:
                    time.sleep(interval)

            return {
                "status": "success",
                "action": "press_key",
                "keys": keys,
                "presses": presses,
                "timestamp": time.time(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def press_hotkey(keys: list[str], presses: int = 1, interval: float = 0.1, pause: float = 0.1) -> dict[str, Any]:
        """Press a combination of keys (hotkey/shortcut).

        Args:
            keys: List of keys to press simultaneously (e.g., ['ctrl', 'c'])
            presses: Number of times to press the hotkey
            interval: Delay between repeated presses in seconds
            pause: Pause after pressing in seconds

        Returns:
            Dict containing the result of the operation

        """
        try:
            for _ in range(presses):
                keyboard.send_keystrokes("+".join(keys), pause=pause)
                if presses > 1 and _ < presses - 1:
                    time.sleep(interval)

            if pause > 0:
                time.sleep(pause)

            return {
                "status": "success",
                "keys_pressed": "+".join(keys),
                "presses": presses,
                "timestamp": time.time(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def move_mouse(
        x: int, y: int, relative: bool = False, duration: float = 0.0, tween: str | None = None
    ) -> dict[str, Any]:
        """Move the mouse cursor to the specified coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            relative: If True, coordinates are relative to the current position
            duration: Time in seconds to take for the movement (0 for instant)
            tween: Tweening function for the movement (e.g., 'linear', 'easeInOutQuad')

        Returns:
            Dict containing the result of the operation

        """
        try:
            if relative:
                current_x, current_y = mouse.get_cursor_pos()
                x += current_x
                y += current_y

            mouse.move(coords=(x, y), duration=duration, tween=tween)

            return {
                "status": "success",
                "action": "move_mouse",
                "x": x,
                "y": y,
                "duration": duration,
                "timestamp": time.time(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def drag_mouse(
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        button: str = "left",
        duration: float = 0.5,
        tween: str | None = None,
    ) -> dict[str, Any]:
        """Drag the mouse from one point to another.

        Args:
            x1: Starting X coordinate
            y1: Starting Y coordinate
            x2: Ending X coordinate
            y2: Ending Y coordinate
            button: Mouse button to use ("left", "right", "middle")
            duration: Time in seconds to take for the drag
            tween: Tweening function for the movement

        Returns:
            Dict containing the result of the operation

        """
        try:
            # Move to start position
            mouse.move(coords=(x1, y1))

            # Press the mouse button
            mouse.press(button=button)

            try:
                # Move to end position while button is pressed
                mouse.move(coords=(x2, y2), duration=duration, tween=tween)
            finally:
                # Ensure button is released even if there's an error
                mouse.release(button=button)

            return {
                "status": "success",
                "action": "drag_mouse",
                "start": (x1, y1),
                "end": (x2, y2),
                "button": button,
                "duration": duration,
                "timestamp": time.time(),
            }

        except Exception as e:
            # Ensure button is released even if there's an error
            try:
                mouse.release(button=button)
            except:
                pass

            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def scroll_mouse(
        clicks: int, x: int | None = None, y: int | None = None, horizontal: bool = False
    ) -> dict[str, Any]:
        """Scroll the mouse wheel.

        Args:
            clicks: Number of clicks to scroll (positive for up/right, negative for down/left)
            x: X coordinate to scroll at (None for current position)
            y: Y coordinate to scroll at (None for current position)
            horizontal: If True, scroll horizontally; otherwise scroll vertically

        Returns:
            Dict containing the result of the operation

        """
        try:
            # Move to the specified position if provided
            if x is not None and y is not None:
                mouse.move(coords=(x, y))

            # Scroll
            if horizontal:
                mouse.horizontal_scroll(clicks)
            else:
                mouse.scroll(clicks)

            return {
                "status": "success",
                "action": "scroll_mouse",
                "clicks": clicks,
                "position": (x, y) if x is not None and y is not None else None,
                "direction": "horizontal" if horizontal else "vertical",
                "timestamp": time.time(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    @app.tool()
    def get_mouse_position() -> dict[str, Any]:
        """Get the current mouse cursor position.

        Returns:
            Dict containing the mouse coordinates

        """
        try:
            x, y = mouse.get_cursor_pos()

            return {
                "status": "success",
                "x": x,
                "y": y,
                "position": (x, y),
                "timestamp": time.time(),
            }

        except Exception as e:
            return {"status": "error", "error": str(e), "error_type": type(e).__name__}

    # Helper functions for window/control interaction
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
    "drag_mouse",
    "get_mouse_position",
    "move_mouse",
    "press_hotkey",
    "press_key",
    "scroll_mouse",
    "type_text",
]
