"""Mouse interaction portmanteau tool for PyWinAuto MCP.

Pointer injection uses :mod:`windows_computer_use_mcp.win32_mouse` (``SetCursorPos`` +
``mouse_event``) with per-monitor DPI awareness — not raw PyAutoGUI — so move,
click, and drag match screen coordinates reliably on scaled displays.
"""

import logging
import subprocess
import sys
import time
from typing import cast

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.tools.models import MouseOperationRequest, ToolResult
from windows_computer_use_mcp.win32_mouse import (
    ButtonName,
    MouseFailSafeError,
    click,
    double_click,
    drag,
    get_cursor_pos,
    move_rel,
    move_to,
    right_click,
    screen_size,
    scroll,
    scroll_at,
)

logger = logging.getLogger(__name__)


if app is not None:

    @app.tool(
        name="automation_mouse",
        description="""Comprehensive mouse control and cursor simulation system.

WHAT IT DOES:
Moves, clicks, drags, and scrolls using **Win32** ``SetCursorPos`` / ``mouse_event``
(DPI-aware), not PyAutoGUI alone — reliable move/click/drag on scaled monitors.

WHEN TO USE:
- Use 'position' to get current screen coordinates before planning a movement.
- Use 'click' or 'double_click' for rapid UI interaction.
- Use 'move_relative' to nudge the cursor from its current spot.
- Use 'scroll' to browse lists or web pages.
- Use 'telemetry' to visually debug coordinates on the user's screen.

RECOVERY AND TROUBLESHOOTING:
- FailSafe: Moving the cursor to the **upper-left** corner aborts (same idea as PyAutoGUI).
  Disabled when windows_computer_use_mcp_BYPASS_HITL=1.
- If coordinates seem 'off', confirm single-monitor expectations or use 'position' first.

RETURNS:
A ToolResult object containing standardized outcome, message, and movement data.
""",
    )
    def automation_mouse(request: MouseOperationRequest) -> ToolResult:
        """Unified mouse control handler."""
        try:
            operation = request.operation
            timestamp = time.time()

            sw, sh = screen_size()
            metadata = {
                "screen_resolution": f"{sw}x{sh}",
                "timestamp": timestamp,
                "input_backend": "win32_mouse",
            }

            x = request.x
            y = request.y
            target_x = request.target_x or request.x2
            target_y = request.target_y or request.y2
            amount = (
                request.amount if request.amount != 1 else (request.clicks if request.clicks != 1 else request.amount)
            )

            btn = cast(ButtonName, request.button)

            read_only_ops = ["position", "telemetry"]
            if operation not in read_only_ops:
                try:
                    from windows_computer_use_mcp.app import approval_state

                    if not approval_state.is_approved():
                        action_detail = f"Mouse: {operation}"
                        if x is not None and y is not None:
                            action_detail += f" at ({x}, {y})"

                        return ToolResult(
                            status="clarification_needed",
                            message="Human approval required for UI automation.",
                            data={
                                "hitl_prompt": f"Approve mouse action? [{action_detail}]",
                                "technical_details": request.model_dump(exclude_none=True),
                                "metadata": metadata,
                            },
                        )
                except ImportError:
                    pass

            try:
                from windows_computer_use_mcp.safety import before_mutation

                gate = before_mutation(read_only=(operation in read_only_ops))
                if not gate.get("allow"):
                    return ToolResult(status="blocked", message=gate.get("message", "Action blocked."))
                if gate.get("dry_run"):
                    return ToolResult(status="success", message=f"[DRY RUN] Would execute {operation}")
            except ImportError:
                pass

            if operation == "position":
                pos_x, pos_y = get_cursor_pos()
                return ToolResult(
                    status="success",
                    message=f"Cursor at ({pos_x}, {pos_y})",
                    data={"x": pos_x, "y": pos_y, "metadata": metadata},
                )

            elif operation == "move":
                if x is None or y is None:
                    return ToolResult(status="error", message="Coordinates x, y are required for 'move'.")
                move_to(int(x), int(y), duration=request.duration)
                return ToolResult(status="success", message=f"Moved to ({x}, {y})", data={"x": x, "y": y})

            elif operation == "move_relative":
                if x is None or y is None:
                    return ToolResult(status="error", message="Offsets x, y are required for 'move_relative'.")
                move_rel(int(x), int(y), duration=request.duration)
                nx, ny = get_cursor_pos()
                return ToolResult(status="success", message=f"Nudged to ({nx}, {ny})", data={"x": nx, "y": ny})

            elif operation in ["click", "double_click", "right_click"]:
                if x is not None and y is not None:
                    move_to(int(x), int(y), duration=request.duration)

                if operation == "click":
                    click(
                        None,
                        None,
                        button=btn,
                        clicks=max(1, int(amount)),
                        interval=0.05,
                    )
                elif operation == "double_click":
                    double_click(None, None, button=btn)
                elif operation == "right_click":
                    right_click()

                nx, ny = get_cursor_pos()
                return ToolResult(status="success", message=f"Executed {operation} at ({nx}, {ny})")

            elif operation == "scroll":
                if x is not None and y is not None:
                    scroll_at(int(x), int(y), int(amount), horizontal=request.horizontal)
                else:
                    scroll(int(amount), horizontal=request.horizontal)

                return ToolResult(status="success", message=f"Scrolled {amount} units.")

            elif operation == "drag":
                if x is None or y is None or target_x is None or target_y is None:
                    return ToolResult(
                        status="error",
                        message="Start and target coordinates are required for 'drag'.",
                    )
                drag(
                    int(x),
                    int(y),
                    int(target_x),
                    int(target_y),
                    duration=request.duration,
                    button=btn,
                )
                return ToolResult(
                    status="success",
                    message=f"Dragged from ({x}, {y}) to ({target_x}, {target_y})",
                )

            elif operation == "hover":
                if x is None or y is None:
                    return ToolResult(status="error", message="Coordinates x, y are required for 'hover'.")
                move_to(int(x), int(y), duration=request.duration)
                time.sleep(request.hover_duration)
                return ToolResult(
                    status="success",
                    message=f"Hovered at ({x}, {y}) for {request.hover_duration}s.",
                )

            elif operation == "telemetry":
                try:
                    cmd = [
                        sys.executable,
                        "-m",
                        "windows_computer_use_mcp.telemetry_hud",
                        "--duration",
                        str(request.telemetry_duration),
                    ]
                    if request.capture_keys:
                        cmd.append("--capture-keys")

                    subprocess.Popen(
                        cmd,
                        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
                        start_new_session=True,
                    )
                    return ToolResult(status="success", message=f"HUD launched for {request.telemetry_duration}s.")
                except Exception as e:
                    return ToolResult(status="error", message=f"Failed to launch HUD: {e}")

            return ToolResult(status="error", message=f"Unknown operation: {operation}")

        except MouseFailSafeError as e:
            return ToolResult(
                status="blocked",
                message=str(e),
                recovery_tip="Automation aborted by failsafe (cursor in upper-left corner). "
                "Set windows_computer_use_mcp_BYPASS_HITL=1 to disable for trusted runs.",
            )
        except Exception as e:
            logger.error(f"Automation mouse tool error: {e}")
            return ToolResult(status="error", message=str(e))

else:
    logger.warning("Mouse tool not available - missing app instance")


__all__ = ["automation_mouse"]
