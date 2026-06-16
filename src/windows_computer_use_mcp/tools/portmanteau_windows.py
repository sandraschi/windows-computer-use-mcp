"""Window management portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Consolidates all window-level lifecycle and state management into a single interface.
This design prevents tool explosion while ensuring atomic control over window
visibility, z-order, and spatial positioning. Follows FastMCP 3.1 SOTA
standards for robust desktop automation.
"""

import logging
import time
from typing import Any

from pywinauto import Desktop
from pywinauto.findwindows import WindowNotFoundError

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.display_utils import (
    get_monitor_at_point,
    enum_monitors,
    translate_coords,
)
from windows_computer_use_mcp.tools.models import ToolResult, WindowOperationRequest

logger = logging.getLogger(__name__)


def _get_desktop():
    """Get a Desktop instance with proper error handling."""
    try:
        return Desktop(backend="uia")
    except Exception as e:
        logger.error(f"Failed to get Desktop instance: {e}")
        raise


def _fast_find_by_title(title: str, *, partial: bool = True) -> list[dict[str, Any]]:
    """Fast title search via pygetwindow — avoids slow UIA desktop enumeration."""
    try:
        import pygetwindow as gw

        needle = title.lower()
        matches: list[dict[str, Any]] = []
        for win in gw.getAllWindows():
            wt = win.title or ""
            if partial:
                if needle not in wt.lower():
                    continue
            elif wt != title:
                continue
            matches.append(
                {
                    "handle": int(win._hWnd),
                    "title": wt,
                    "class_name": "",
                    "is_visible": True,
                    "is_enabled": True,
                    "process_id": None,
                }
            )
        return matches
    except Exception as exc:
        logger.debug("fast title find failed: %s", exc)
        return []


def _get_window_info(window) -> dict[str, Any]:
    """Extract standard window information."""
    try:
        info = {
            "handle": window.handle,
            "title": window.window_text(),
            "class_name": window.class_name(),
            "is_visible": window.is_visible(),
            "is_enabled": window.is_enabled(),
            "process_id": window.process_id(),
        }

        try:
            rect = window.rectangle()
            info["rect"] = {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.width(),
                "height": rect.height(),
            }
            # Add monitor info based on window center
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
            try:
                mon = get_monitor_at_point(cx, cy)
                info["monitor_index"] = mon.index
                info["monitor_name"] = mon.name
            except Exception:
                pass
        except Exception:
            pass

        return info
    except Exception as e:
        logger.warning(f"Error getting window info: {e}")
        return {}


if app is not None:

    @app.tool(
        name="automation_windows",
        description="""Comprehensive Windows window management and lifecycle control system.

WHAT IT DOES:
This tool provides a unified interface for discovering, locating, and controlling windows
on the Windows desktop. It handles window state transitions (maximize, minimize, restore),
visibility, and spatial positioning via the unique window handle (HWND).

WHEN TO USE:
- Use 'list' to discover available windows and their handles when starting a task.
- Use 'find' to locate a specific window by its title or class name.
- Use 'focus' or 'activate' to bring a window to the foreground before sending input.
- Use 'manage' with actions (maximize, close, etc.) to control window lifecycle.
- Use 'position' to precisely align windows for multi-window automation scenarios.

RECOVERY AND TROUBLESHOOTING:
- If a 'WindowNotFoundError' occurs, the handle (HWND) may have become stale.
  Call 'list' to refresh your knowledge of active window handles.
- If 'focus' fails, the window might be minimized or blocked.
  The tool automatically attempts to restore minimized windows before focusing.

RETURNS:
A ToolResult object containing standardized outcome, message, and window metadata.
""",
    )
    def automation_windows(request: WindowOperationRequest) -> ToolResult:
        """Unified window management handler."""
        try:
            operation = request.operation
            handle = request.handle
            timestamp = time.time()
            desktop = _get_desktop()

            # === LIST OPERATION ===
            if operation == "list":
                windows = []
                for window in desktop.windows():
                    try:
                        if window.is_visible():
                            windows.append(_get_window_info(window))
                    except Exception as e:
                        logger.warning(f"Error processing window: {e}")

                return ToolResult(
                    status="success",
                    message=f"Successfully listed {len(windows)} visible windows.",
                    data={"count": len(windows), "windows": windows, "timestamp": timestamp},
                )

            # === FIND OPERATION ===
            elif operation == "find":
                if not request.title and not handle and not request.process_id and not request.class_name:
                    return ToolResult(
                        status="error",
                        message="At least one search criterion (title, handle, process_id, class_name) is required.",
                        recovery_tip="Provide a title, handle, or PID to locate the window.",
                    )

                # Title-only search: pygetwindow is orders of magnitude faster than UIA scan.
                if request.title and not request.class_name and not request.process_id and not handle:
                    fast = _fast_find_by_title(request.title, partial=bool(request.partial))
                    return ToolResult(
                        status="success",
                        message=f"Found {len(fast)} matching windows (fast path).",
                        data={"count": len(fast), "windows": fast},
                    )

                matches = []
                for window in desktop.windows():
                    try:
                        match = True
                        if request.title:
                            window_text = window.window_text()
                            if request.partial:
                                if request.title.lower() not in window_text.lower():
                                    match = False
                            elif request.title != window_text:
                                match = False

                        if request.class_name:
                            win_class = window.class_name()
                            if request.partial:
                                if request.class_name.lower() not in win_class.lower():
                                    match = False
                            elif request.class_name != win_class:
                                match = False

                        if handle and window.handle != handle:
                            match = False

                        if request.process_id and window.process_id() != request.process_id:
                            match = False

                        if match:
                            matches.append(_get_window_info(window))
                    except Exception as e:
                        logger.warning(f"Error checking window: {e}")

                return ToolResult(
                    status="success",
                    message=f"Found {len(matches)} matching windows.",
                    data={"count": len(matches), "windows": matches},
                )

            # === GET ACTIVE WINDOW OPERATION ===
            elif operation == "get_active":
                try:
                    active_window = desktop.active_window()
                    if active_window:
                        return ToolResult(
                            status="success",
                            message="Retrieved active window successfully.",
                            data={"window": _get_window_info(active_window)},
                        )
                    return ToolResult(status="success", message="No active window found.", data={"window": None})
                except Exception as e:
                    return ToolResult(status="error", message=f"Failed to get active window: {e}")

            # === OPERATIONS REQUIRING HANDLE ===
            if handle is None:
                return ToolResult(
                    status="error",
                    message=f"The '{operation}' operation requires a valid window handle (HWND).",
                    recovery_tip="Use 'list' or 'find' to obtain the correct handle first.",
                )

            try:
                window = desktop.window(handle=handle)
            except WindowNotFoundError:
                return ToolResult(
                    status="error",
                    message=f"Window with handle {handle} not found.",
                    recovery_tip="The handle may be stale. Use 'find' to get the current handle.",
                )

            # === OPERATION MAPPER ===
            # Many operations correspond to simple method calls on the window object
            # We map them here for reusability
            operation_actions = {
                "maximize": lambda w: w.maximize(),
                "minimize": lambda w: w.minimize(),
                "restore": lambda w: w.restore(),
                "close": lambda w: w.close(),
                "activate": lambda w: w.activate(),
                "focus": lambda w: w.set_focus(),
            }

            if operation in operation_actions:
                try:
                    if operation == "focus" and window.is_minimized():
                        window.restore()

                    operation_actions[operation](window)

                    return ToolResult(
                        status="success",
                        message=f"Executed operation '{operation}' on window {handle}.",
                        data={"handle": handle, "operation": operation},
                    )
                except Exception as e:
                    return ToolResult(status="error", message=f"Failed to execute '{operation}': {e}")

            # === MANAGE OPERATION (Action-based legacy support) ===
            if operation == "manage":
                action = request.action
                if action is None:
                    return ToolResult(
                        status="error",
                        message="A specific 'action' (maximize, close, etc.) is required for 'manage'.",
                        recovery_tip="Provide an 'action' parameter such as 'maximize' or 'close'.",
                    )

                if action in operation_actions:
                    operation_actions[action](window)
                    return ToolResult(
                        status="success",
                        message=f"Executed '{action}' on window {handle}.",
                        data={"handle": handle, "action": action},
                    )
                return ToolResult(status="error", message=f"Unknown action: {action}")

            # === POSITION OPERATION ===
            elif operation == "position":
                wx = request.x
                wy = request.y
                if wx is not None and wy is not None and request.monitor_index is not None:
                    wx, wy = translate_coords(wx, wy, request.monitor_index)
                if wx is None or wy is None or request.width is None or request.height is None:
                    return ToolResult(
                        status="error",
                        message="Spatial coordinates (x, y) and dimensions (width, height) are required for 'position'.",
                    )
                window.move_window(x=wx, y=wy, width=request.width, height=request.height)
                mon = get_monitor_at_point(wx, wy)
                return ToolResult(
                    status="success",
                    message=f"Window {handle} moved to monitor {mon.index} at ({wx}, {wy}).",
                    data={
                        "x": wx, "y": wy, "width": request.width, "height": request.height,
                        "monitor_index": mon.index, "monitor_name": mon.name,
                    },
                )

            # === SIMPLE METADATA OPERATIONS ===
            elif operation == "title":
                val = window.window_text()
                return ToolResult(status="success", message=f"Title: {val}", data={"title": val})

            elif operation == "rect":
                r = window.rectangle()
                cx = (r.left + r.right) // 2
                cy = (r.top + r.bottom) // 2
                mon = get_monitor_at_point(cx, cy)
                return ToolResult(
                    status="success",
                    message=f"Rect on monitor {mon.index}.",
                    data={
                        "left": r.left, "top": r.top,
                        "right": r.right, "bottom": r.bottom,
                        "width": r.width(), "height": r.height(),
                        "monitor_index": mon.index, "monitor_name": mon.name,
                    },
                )

            elif operation == "state":
                r = window.rectangle()
                cx = (r.left + r.right) // 2
                cy = (r.top + r.bottom) // 2
                mon = get_monitor_at_point(cx, cy)
                return ToolResult(
                    status="success",
                    message="State retrieved.",
                    data={
                        "is_visible": window.is_visible(),
                        "is_enabled": window.is_enabled(),
                        "has_focus": window.has_focus(),
                        "is_minimized": window.is_minimized(),
                        "is_maximized": window.is_maximized(),
                        "monitor_index": mon.index,
                        "monitor_name": mon.name,
                    },
                )

            return ToolResult(status="error", message=f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(f"Automation windows tool error: {e}")
            return ToolResult(status="error", message=str(e))

else:
    logger.warning("Windows tool not available - missing app instance")


__all__ = ["automation_windows"]
