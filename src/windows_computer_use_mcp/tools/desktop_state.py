"""Desktop State Capture Tools for PyWinAuto MCP tracking SOTA 2026 standards.

Provides comprehensive desktop state capture with UI element discovery,
visual annotations, and OCR capabilities.
"""

import logging
import time

# Import the FastMCP app instance
try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in desktop state tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in desktop state tools: {e}")
    app = None

# Import desktop state capture functionality and models
try:
    from windows_computer_use_mcp.desktop_state import DesktopStateCapture
    from windows_computer_use_mcp.tools.models import DesktopStateRequest, ToolResult

    logger.info("Successfully imported desktop state capture functionality and models")
except ImportError as e:
    logger.error(f"Import error in desktop_state tools: {e}")
    DesktopStateCapture = None
    DesktopStateRequest = None
    ToolResult = None


if app is not None and DesktopStateCapture is not None:

    @app.tool(
        name="get_desktop_state",
        description="""Captures the complete hierarchical state of the Windows desktop UI.

WHAT IT DOES:
This tool traverses the UI tree of all active windows to produce a structured JSON representation of every discoverable element (buttons, panes, edit boxes, etc.). It optionally integrates computer vision (capturing element screenshots) and OCR (reading text from purely graphical controls) to enrich the metadata.

WHEN TO USE:
- Use this as your 'Primary Discovery' tool when starting a new automation task.
- Use it to find stable selectors (Control IDs, Class Names, Names) for 'automation_elements' calls.
- Use 'use_vision=True' to get visual snapshots of the elements for multi-modal analysis.
- Use capture_mode='ax'|'som'|'vision' (Cua-style); prefer get_window_state for one HWND.

RECOVERY:
If the UI tree is exceptionally deep, increase 'max_depth' or target a specific window first using 'automation_windows'. If capture is slow, decrease 'max_depth' or disable 'use_ocr'.
""",
    )
    def get_desktop_state(request: DesktopStateRequest) -> ToolResult:
        """Captures the current desktop state including UI elements and visual metadata."""
        try:
            use_vision = request.use_vision
            use_ocr = request.use_ocr
            capture_mode = request.capture_mode
            max_depth = request.max_depth
            element_timeout = request.element_timeout

            logger.info(
                "Desktop state capture vision=%s ocr=%s capture_mode=%s",
                use_vision,
                use_ocr,
                capture_mode,
            )

            timestamp = time.time()
            visual_metadata = {
                "timestamp": timestamp,
                "engine": "pywinauto-mcp-sota-2026",
                "identity": "desktop-state-capture",
            }

            capturer = DesktopStateCapture(max_depth=max_depth, element_timeout=element_timeout)
            result = capturer.capture(
                use_vision=use_vision,
                use_ocr=use_ocr,
                capture_mode=capture_mode,
            )

            # Inject SOTA metadata
            result["visual_metadata"] = visual_metadata

            return ToolResult(
                status="success",
                message=f"Desktop state capture completed: {result.get('element_count', 0)} elements found",
                data=result,
            )

        except Exception as e:
            logger.error(f"Desktop state capture failed: {e}")
            return ToolResult(
                status="error",
                message=f"Desktop state capture failed: {e!s}",
                recovery_tip="Ensure the desktop session is active and not locked. Try disabling vision/ocr to isolate issues.",
            )
else:
    logger.warning("Desktop state tools not available - missing dependencies or app instance")


__all__ = ["get_desktop_state"]
