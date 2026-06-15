"""Basic input and system interaction tools for PyWinAuto MCP.

This module contains fundamental tools for mouse and keyboard interaction.
"""

import logging
from datetime import datetime
from typing import Any

import pyautogui
from pywinauto import Desktop

# Import the FastMCP app instance from the app module
try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in basic_tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in basic_tools: {e}")
    app = None

# Only proceed with tool registration if app is available
if app is not None:
    logger.info("Registering basic tools with FastMCP")

    @app.tool(
        name="health_check",
        description="Check if the PyWinAuto MCP server is running and operational.",
    )
    def health_check() -> dict[str, str]:
        """Check if the PyWinAuto MCP server is running and operational."""
        return {
            "status": "healthy",
            "server": "PyWinAuto MCP",
            "version": "0.2.0",
            "timestamp": datetime.utcnow().isoformat(),
        }

    @app.tool(
        name="get_help",
        description="Get comprehensive help and documentation for all available tools.",
    )
    def get_help(category: str | None = None, tool_name: str | None = None) -> dict[str, Any]:
        """Get comprehensive help and documentation for all available tools.

        This is the main help system for PyWinAuto MCP. Use it to discover,
        understand, and get detailed information about all automation tools.

        Args:
            category: Filter by tool category (system, windows, elements, mouse, input, visual, face-recognition, desktop_state)
            tool_name: Get detailed help for a specific tool

        Returns:
            Comprehensive help information including tool categories, descriptions, and examples

        """
        try:
            help_info = {
                "server": "PyWinAuto MCP v0.2.0",
                "description": "Comprehensive Windows UI automation with 23+ tools across 7 categories",
                "total_tools": 23,
                "categories": {
                    "system": 5,
                    "windows": 6,
                    "elements": 6,
                    "mouse": 8,
                    "input": 3,
                    "visual": 3,
                    "face-recognition": 4,
                    "desktop_state": 1,
                },
            }

            # If specific tool requested
            if tool_name:
                tool_details = _get_tool_details(tool_name)
                if tool_details:
                    help_info["tool_details"] = tool_details
                    help_info["status"] = "success"
                else:
                    help_info["error"] = f"Tool '{tool_name}' not found"
                    help_info["status"] = "error"
                    help_info["available_tools"] = _list_all_tools()
                return help_info

            # If category filter requested
            if category:
                category_tools = _get_category_tools(category)
                if category_tools:
                    help_info["category"] = category
                    help_info["tools"] = category_tools
                    help_info["status"] = "success"
                else:
                    help_info["error"] = f"Category '{category}' not found"
                    help_info["status"] = "error"
                    help_info["available_categories"] = list(help_info["categories"].keys())
                return help_info

            # General help overview
            help_info["overview"] = {
                "System Tools": [
                    "health_check",
                    "wait",
                    "get_system_clipboard",
                    "set_system_clipboard",
                    "get_help",
                ],
                "Window Management": [
                    "list_windows",
                    "find_window_by_title",
                    "maximize_window",
                    "minimize_window",
                    "restore_window",
                    "set_window_position",
                    "get_window_title",
                    "close_window",
                    "set_window_foreground",
                ],
                "UI Elements": [
                    "click_element",
                    "double_click_element",
                    "right_click_element",
                    "hover_element",
                    "get_element_info",
                    "get_element_text",
                    "set_element_text",
                    "get_element_rect",
                    "is_element_visible",
                    "is_element_enabled",
                    "get_all_elements",
                ],
                "Mouse Control": [
                    "get_cursor_position",
                    "click_at_position",
                    "move_mouse",
                    "scroll_mouse",
                    "hover_mouse",
                    "mouse_move_relative",
                    "mouse_move_to_element",
                    "mouse_hover",
                    "drag_and_drop",
                    "right_click",
                    "double_click",
                    "mouse_scroll",
                ],
                "Keyboard Input": ["type_text", "send_keys", "press_key", "press_hotkey"],
                "Visual Intelligence": [
                    "take_screenshot",
                    "extract_text",
                    "find_image",
                    "highlight_element",
                ],
                "Face Recognition": [
                    "add_face",
                    "recognize_face",
                    "list_known_faces",
                    "delete_face",
                    "capture_and_recognize",
                ],
                "Desktop State": ["get_desktop_state"],
            }

            help_info["getting_started"] = [
                "Use 'get_help()' for this overview",
                "Use 'get_help(category=\"windows\")' for window tools",
                "Use 'get_help(tool_name=\"click_element\")' for detailed tool info",
                "Use 'health_check()' to verify the server is running",
                "Use 'get_desktop_state()' for complete UI analysis",
            ]

            help_info["status"] = "success"
            return help_info

        except Exception as e:
            return {"status": "error", "error": str(e), "server": "PyWinAuto MCP v0.2.0"}

    @app.tool()
    def get_cursor_position() -> dict[str, Any]:
        """Get current mouse cursor position."""
        try:
            x, y = pyautogui.position()
            return {
                "status": "success",
                "x": x,
                "y": y,
                "position": (x, y),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def click_at_position(x: int, y: int, button: str = "left") -> dict[str, Any]:
        """Click at specific screen coordinates.

        Args:
            x: X coordinate to click
            y: Y coordinate to click
            button: Mouse button to click ("left", "right", "middle")

        """
        try:
            pyautogui.click(x, y, button=button)
            return {
                "status": "success",
                "action": "click",
                "position": (x, y),
                "button": button,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def move_mouse(x: int, y: int) -> dict[str, Any]:
        """Move mouse to specific coordinates.

        Args:
            x: X coordinate to move to
            y: Y coordinate to move to

        """
        try:
            pyautogui.moveTo(x, y)
            return {
                "status": "success",
                "action": "move",
                "position": (x, y),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def scroll_mouse(amount: int, x: int | None = None, y: int | None = None) -> dict[str, Any]:
        """Scroll mouse wheel at current or specified position.

        Args:
            amount: Scroll amount (positive = up, negative = down)
            x: Optional X coordinate to scroll at
            y: Optional Y coordinate to scroll at

        """
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)

            pyautogui.scroll(amount)

            return {
                "status": "success",
                "action": "scroll",
                "amount": amount,
                "position": (x, y) if x is not None and y is not None else None,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def list_windows() -> dict[str, Any]:
        """List all visible windows on the desktop."""
        try:
            desktop = Desktop(backend="uia")
            windows = []

            for window in desktop.windows():
                try:
                    window_info = {
                        "title": window.window_text(),
                        "class_name": window.class_name(),
                        "handle": window.handle,
                        "is_visible": window.is_visible(),
                        "is_enabled": window.is_enabled(),
                    }

                    try:
                        rect = window.rectangle()
                        window_info["rect"] = {
                            "left": rect.left,
                            "top": rect.top,
                            "right": rect.right,
                            "bottom": rect.bottom,
                            "width": rect.width(),
                            "height": rect.height(),
                        }
                    except Exception:
                        pass

                    windows.append(window_info)
                except Exception as e:
                    logger.warning(f"Error getting window info: {e}")

            return {"status": "success", "windows_found": len(windows), "windows": windows}

        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def find_window_by_title(title: str, partial: bool = True) -> dict[str, Any]:
        """Find window by title text.

        Args:
            title: Window title to search for
            partial: Whether to do partial match (default: True)

        """
        try:
            desktop = Desktop(backend="uia")
            matching_windows = []

            for window in desktop.windows():
                try:
                    window_title = window.window_text()

                    if (partial and title.lower() in window_title.lower()) or (
                        not partial and title.lower() == window_title.lower()
                    ):
                        window_info = {
                            "title": window_title,
                            "class_name": window.class_name(),
                            "handle": window.handle,
                            "is_visible": window.is_visible(),
                            "is_enabled": window.is_enabled(),
                        }

                        try:
                            rect = window.rectangle()
                            window_info["rect"] = {
                                "left": rect.left,
                                "top": rect.top,
                                "right": rect.right,
                                "bottom": rect.bottom,
                                "width": rect.width(),
                                "height": rect.height(),
                            }
                        except Exception:
                            pass

                        matching_windows.append(window_info)
                except Exception as e:
                    logger.warning(f"Error checking window: {e}")

            return {
                "status": "success",
                "windows_found": len(matching_windows),
                "windows": matching_windows,
                "search_term": title,
                "partial_match": partial,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def type_text(text: str) -> dict[str, Any]:
        """Type text at current cursor position.

        Args:
            text: Text to type

        """
        try:
            pyautogui.write(text)
            return {
                "status": "success",
                "action": "type_text",
                "text": text,
                "length": len(text),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def send_keys(keys: str) -> dict[str, Any]:
        """Send special key combinations.

        Args:
            keys: Key combination (e.g., "ctrl+c", "alt+tab", "enter")

        """
        try:
            pyautogui.hotkey(*keys.split("+"))
            return {
                "status": "success",
                "action": "send_keys",
                "keys_sent": keys,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def hover_mouse(x: int, y: int, duration: float = 0.5) -> dict[str, Any]:
        """Move mouse to coordinates and hover for specified duration.

        Args:
            x: X coordinate to hover at
            y: Y coordinate to hover at
            duration: How long to hover in seconds (default: 0.5)

        """
        try:
            pyautogui.moveTo(x, y)
            import time

            time.sleep(duration)
            return {
                "status": "success",
                "action": "hover",
                "position": (x, y),
                "duration": duration,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def wait(seconds: float) -> dict[str, Any]:
        """Pause execution for specified seconds.

        Args:
            seconds: Number of seconds to wait

        """
        try:
            import time

            time.sleep(seconds)
            return {
                "status": "success",
                "action": "wait",
                "duration": seconds,
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def get_system_clipboard() -> dict[str, Any]:
        """Get current clipboard content."""
        try:
            import pyperclip

            content = pyperclip.paste()
            return {
                "status": "success",
                "content": content,
                "length": len(content),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.tool()
    def set_system_clipboard(content: str) -> dict[str, Any]:
        """Set clipboard content.

        Args:
            content: Text content to copy to clipboard

        """
        try:
            import pyperclip

            pyperclip.copy(content)
            return {
                "status": "success",
                "action": "clipboard_set",
                "content": content,
                "length": len(content),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

else:
    logger = logging.getLogger(__name__)
    logger.warning("FastMCP app not available - basic tools will not be registered")

    # Define fallback functions for when app is not available
    def get_help(category=None, tool_name=None):
        """Fallback help function when MCP app is not available."""
        return {
            "status": "error",
            "error": "MCP app not available",
            "server": "PyWinAuto MCP v0.2.0",
        }


# Helper functions (defined at module level)
def _get_tool_details(tool_name: str) -> dict[str, Any] | None:
    """Get detailed information about a specific tool."""
    tool_details = {
        "get_desktop_state": {
            "name": "get_desktop_state",
            "category": "desktop_state",
            "description": "Capture comprehensive desktop state with UI element discovery, visual annotations, and OCR capabilities",
            "parameters": {
                "use_vision": {
                    "type": "boolean",
                    "default": False,
                    "description": "Include annotated screenshot with element boundaries",
                },
                "use_ocr": {
                    "type": "boolean",
                    "default": False,
                    "description": "Use OCR to extract text from visual elements",
                },
                "max_depth": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum UI tree traversal depth",
                },
            },
            "returns": {
                "text": "Human-readable report of all discovered elements",
                "interactive_elements": "List of clickable/actionable UI elements",
                "informative_elements": "List of text/display elements",
                "element_count": "Total number of discovered elements",
                "screenshot_base64": "Base64-encoded annotated screenshot (if use_vision=True)",
            },
            "examples": [
                "get_desktop_state() - Basic UI element discovery",
                "get_desktop_state(use_vision=True) - With visual annotations",
                "get_desktop_state(use_ocr=True) - With OCR text extraction",
                "get_desktop_state(use_vision=True, use_ocr=True, max_depth=15) - Complete analysis",
            ],
            "notes": "Provides similar functionality to Windows-MCP State-Tool but enhanced with OCR and better element classification",
        },
        "health_check": {
            "name": "health_check",
            "category": "system",
            "description": "Verify that the PyWinAuto MCP server is running and operational",
            "parameters": {},
            "returns": {
                "status": "Server health status",
                "version": "Server version",
                "timestamp": "Check timestamp",
            },
            "examples": ["health_check() - Check server status"],
        },
        "click_element": {
            "name": "click_element",
            "category": "elements",
            "description": "Click on a UI element by window handle, control ID, or title",
            "parameters": {
                "window_handle": {
                    "type": "integer",
                    "description": "Handle of the window containing the element",
                },
                "control_id": {"type": "string", "description": "Automation ID of the element"},
                "title": {"type": "string", "description": "Title/text of the element"},
                "button": {
                    "type": "string",
                    "default": "left",
                    "enum": ["left", "right", "middle"],
                },
            },
            "examples": [
                "click_element(window_handle=12345, control_id='btnOK') - Click OK button",
                "click_element(window_handle=12345, title='Save', button='right') - Right-click Save",
            ],
        },
        "take_screenshot": {
            "name": "take_screenshot",
            "category": "visual",
            "description": "Capture screenshot of screen, window, or specific region",
            "parameters": {
                "region": {
                    "type": "object",
                    "description": "Specific region to capture (optional)",
                },
                "window_handle": {
                    "type": "integer",
                    "description": "Specific window to capture (optional)",
                },
            },
            "examples": [
                "take_screenshot() - Full screen capture",
                "take_screenshot(window_handle=12345) - Specific window screenshot",
                "take_screenshot(region={'x': 100, 'y': 100, 'width': 300, 'height': 200}) - Region capture",
            ],
        },
        "type_text": {
            "name": "type_text",
            "category": "input",
            "description": "Type text at the current cursor position",
            "parameters": {"text": {"type": "string", "description": "Text to type"}},
            "examples": ["type_text('Hello World!') - Type text at cursor"],
        },
        "add_face": {
            "name": "add_face",
            "category": "face-recognition",
            "description": "Add a new face to the recognition system for security authentication",
            "parameters": {
                "name": {"type": "string", "description": "Name of the person"},
                "image_path": {
                    "type": "string",
                    "description": "Path to image file containing the face",
                },
            },
            "examples": ["add_face(name='John Doe', image_path='john.jpg') - Add John's face"],
        },
        "hover_mouse": {
            "name": "hover_mouse",
            "category": "mouse",
            "description": "Move mouse to coordinates and hover for specified duration",
            "parameters": {
                "x": {"type": "integer", "description": "X coordinate to hover at"},
                "y": {"type": "integer", "description": "Y coordinate to hover at"},
                "duration": {
                    "type": "number",
                    "default": 0.5,
                    "description": "How long to hover in seconds",
                },
            },
            "examples": ["hover_mouse(x=500, y=300, duration=1.0) - Hover at position for 1 second"],
        },
        "wait": {
            "name": "wait",
            "category": "system",
            "description": "Pause execution for specified seconds",
            "parameters": {"seconds": {"type": "number", "description": "Number of seconds to wait"}},
            "examples": ["wait(seconds=2.5) - Wait 2.5 seconds"],
        },
        "get_system_clipboard": {
            "name": "get_system_clipboard",
            "category": "system",
            "description": "Get current clipboard content",
            "parameters": {},
            "examples": ["get_system_clipboard() - Get clipboard text"],
        },
        "set_system_clipboard": {
            "name": "set_system_clipboard",
            "category": "system",
            "description": "Set clipboard content",
            "parameters": {"content": {"type": "string", "description": "Text content to copy to clipboard"}},
            "examples": ["set_system_clipboard(content='Hello World') - Copy text to clipboard"],
        },
    }

    return tool_details.get(tool_name)


def _get_category_tools(category: str) -> list[dict[str, Any]] | None:
    """Get all tools in a specific category."""
    category_tools = {
        "system": [
            {"name": "health_check", "description": "Check server health and status"},
            {"name": "wait", "description": "Pause execution for specified seconds"},
            {"name": "get_system_clipboard", "description": "Get clipboard content"},
            {"name": "set_system_clipboard", "description": "Set clipboard content"},
            {"name": "get_help", "description": "Get comprehensive help and documentation"},
        ],
        "windows": [
            {"name": "list_windows", "description": "List all visible windows"},
            {"name": "find_window_by_title", "description": "Find window by title text"},
            {"name": "maximize_window", "description": "Maximize a window"},
            {"name": "minimize_window", "description": "Minimize a window"},
            {"name": "restore_window", "description": "Restore window to normal size"},
            {"name": "close_window", "description": "Close a window"},
        ],
        "elements": [
            {"name": "click_element", "description": "Click on UI element"},
            {"name": "get_element_info", "description": "Get element information"},
            {"name": "get_element_text", "description": "Get element text content"},
            {"name": "set_element_text", "description": "Set element text content"},
            {"name": "hover_element", "description": "Hover over element"},
            {"name": "get_all_elements", "description": "Get all elements in window"},
        ],
        "mouse": [
            {"name": "get_cursor_position", "description": "Get current mouse position"},
            {"name": "click_at_position", "description": "Click at screen coordinates"},
            {"name": "move_mouse", "description": "Move mouse to coordinates"},
            {"name": "scroll_mouse", "description": "Scroll mouse wheel"},
            {"name": "hover_mouse", "description": "Move mouse and hover at position"},
            {"name": "drag_and_drop", "description": "Drag element to new position"},
        ],
        "input": [
            {"name": "type_text", "description": "Type text at cursor"},
            {"name": "send_keys", "description": "Send key combinations"},
            {"name": "press_key", "description": "Press individual keys"},
        ],
        "visual": [
            {"name": "take_screenshot", "description": "Capture screen/window image"},
            {"name": "extract_text", "description": "Extract text from images via OCR"},
            {"name": "find_image", "description": "Find template image on screen"},
        ],
        "face-recognition": [
            {"name": "add_face", "description": "Add face to recognition system"},
            {"name": "recognize_face", "description": "Identify faces in images"},
            {"name": "list_known_faces", "description": "List registered faces"},
            {"name": "capture_and_recognize", "description": "Live webcam face recognition"},
        ],
        "desktop_state": [
            {
                "name": "get_desktop_state",
                "description": "Complete UI element discovery and analysis",
            }
        ],
    }

    return category_tools.get(category)


def _list_all_tools() -> list[str]:
    """List all available tool names."""
    return [
        "health_check",
        "get_cursor_position",
        "click_at_position",
        "move_mouse",
        "scroll_mouse",
        "hover_mouse",
        "list_windows",
        "find_window_by_title",
        "type_text",
        "send_keys",
        "wait",
        "get_system_clipboard",
        "set_system_clipboard",
        "get_help",
        "maximize_window",
        "minimize_window",
        "restore_window",
        "close_window",
        "click_element",
        "get_element_info",
        "get_element_text",
        "set_element_text",
        "take_screenshot",
        "extract_text",
        "find_image",
        "add_face",
        "recognize_face",
        "list_known_faces",
        "capture_and_recognize",
        "get_desktop_state",
    ]


# Add all tools to __all__
__all__ = [
    "click_at_position",
    "find_window_by_title",
    "get_cursor_position",
    "get_help",
    "get_system_clipboard",
    "health_check",
    "hover_mouse",
    "list_windows",
    "move_mouse",
    "scroll_mouse",
    "send_keys",
    "set_system_clipboard",
    "type_text",
    "wait",
]
