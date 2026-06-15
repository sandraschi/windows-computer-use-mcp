"""Per-window state capture (Cua Driver-shaped get_window_state)."""

import logging
import time

logger = logging.getLogger(__name__)

try:
    from windows_computer_use_mcp.app import app
    from windows_computer_use_mcp.desktop_state.capture import (
        DesktopStateCapture,
        normalize_elements_for_snapshot,
    )
    from windows_computer_use_mcp.snapshot_store import get_snapshot_store
    from windows_computer_use_mcp.tools.models import ToolResult, WindowStateRequest
    from windows_computer_use_mcp.trajectory import log_trajectory

except ImportError as e:
    logger.error("window_state tools import failed: %s", e)
    app = None


if app is not None:

    @app.tool(
        name="get_window_state",
        description="""Capture UI state for one window (Cua Driver-shaped loop).

WHAT IT DOES:
Returns a snapshot_id, element_index-addressable elements, and optional set-of-mark screenshot
for a single HWND. Use before automation_elements(click, snapshot_id=..., element_index=...).

capture_mode:
- ax: accessibility tree only (no screen grab)
- som: tree + annotated screenshot (default)
- vision: window image only (no element_index clicks)

WHEN TO USE:
- Agent drives one app (Excel, Notepad) while the user keeps another app (Cursor) focused.
- Prefer this over get_desktop_state for targeted loops.

See docs/CUA_PARITY.md and windows_computer_use_mcp_DISPATCH for background vs foreground dispatch.
""",
    )
    def get_window_state(request: WindowStateRequest) -> ToolResult:
        try:
            try:
                from windows_computer_use_mcp import assert_engine

                img = assert_engine.capture_image(window_handle=request.window_handle)
                ui_hash = assert_engine.image_hash(img, "dhash")
                dropped = get_snapshot_store().invalidate_for_handle(request.window_handle, ui_hash)
                if dropped:
                    logger.debug("Invalidated %d stale snapshots for hwnd %s", dropped, request.window_handle)
            except Exception:
                pass

            capturer = DesktopStateCapture(
                max_depth=request.max_depth,
                element_timeout=request.element_timeout,
            )
            raw = capturer.capture(
                use_ocr=request.use_ocr,
                capture_mode=request.capture_mode,
                window_handle=request.window_handle,
            )
            interactive = raw.get("interactive_elements") or []
            elements = normalize_elements_for_snapshot(interactive)
            screenshot_b64 = raw.get("screenshot_base64")
            snapshot_id = get_snapshot_store().put(
                window_handle=request.window_handle,
                capture_mode=request.capture_mode,
                elements=elements,
                screenshot_base64=screenshot_b64,
            )
            log_trajectory(
                "get_window_state",
                window_handle=request.window_handle,
                capture_mode=request.capture_mode,
                snapshot_id=snapshot_id,
                element_count=len(elements),
            )
            return ToolResult(
                status="success",
                message=(
                    f"Window state captured: {len(elements)} interactive elements, "
                    f"mode={request.capture_mode}, snapshot_id={snapshot_id}"
                ),
                data={
                    "snapshot_id": snapshot_id,
                    "window_handle": request.window_handle,
                    "capture_mode": request.capture_mode,
                    "elements": elements,
                    "element_count": len(elements),
                    "screenshot_base64": screenshot_b64,
                    "text": raw.get("text"),
                    "timestamp": time.time(),
                },
            )
        except ValueError as e:
            return ToolResult(
                status="error",
                message=str(e),
                recovery_tip="Use automation_windows(operation='list') to find a valid HWND.",
            )
        except Exception as e:
            logger.exception("get_window_state failed")
            return ToolResult(
                status="error",
                message=f"Window state capture failed: {e!s}",
                recovery_tip="Try capture_mode='ax' or reduce max_depth.",
            )
