"""Global keylogger portmanteau tool (opt-in via windows_computer_use_mcp_ENABLE_KEYLOGGER=1).

Uses pynput's low-level keyboard hook for the current Windows session. High-risk:
only enable on machines you own and for legitimate debugging or automation tasks.

Shows a "CUA at work" HUD overlay while the keylogger is active.
"""

from __future__ import annotations

import logging

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.cua_hud import CuaHUD
from windows_computer_use_mcp.keylogger_service import GlobalKeyloggerService
from windows_computer_use_mcp.tools.models import KeyloggerOperationRequest, ToolResult

logger = logging.getLogger(__name__)

_svc = GlobalKeyloggerService.get()
_hud: CuaHUD | None = None


if app is not None:

    @app.tool(
        name="global_keylogger",
        description="""Session-wide keyboard event capture (Windows low-level hook via pynput).

WHAT IT DOES:
Records key press (and optionally key release) events into a bounded in-memory ring buffer.
Use 'read' to retrieve the most recent events without stopping the listener.

WHEN TO USE:
- Debugging shortcut or focus issues during UI automation.
- Auditing keystrokes in a controlled, authorized environment only.

SECURITY:
- Disabled unless the server is started with windows_computer_use_mcp_ENABLE_KEYLOGGER=1.
- Starting capture requires the same HITL approval window as other input tools
  (unless windows_computer_use_mcp_BYPASS_HITL is set).
- Do not use for spying; comply with law and policy.

OPERATIONS:
- 'start' — begin listening (optional max_buffer, include_release).
- 'stop' — stop listener; buffer remains until cleared or new start.
- 'status' — running flag, buffer fill, limits.
- 'read' — return most recent events (limit, flush removes only those events from buffer).
- 'clear' — empty buffer without stopping the listener.

RETURNS:
ToolResult with status, message, and data (events list, counts, etc.).
""",
    )
    def global_keylogger(request: KeyloggerOperationRequest) -> ToolResult:
        """Global keyboard capture handler."""
        try:
            op = request.operation

            if op == "start":
                try:
                    from windows_computer_use_mcp.app import approval_state

                    if not approval_state.is_approved():
                        return ToolResult(
                            status="clarification_needed",
                            message="Human approval required to start global keylogging.",
                            data={
                                "hitl_prompt": "Approve global keyboard capture (keylogger)?",
                                "technical_details": request.model_dump(exclude_none=True),
                            },
                        )
                except ImportError:
                    pass

                try:
                    from windows_computer_use_mcp.safety import gate_invasive_monitoring

                    gate = gate_invasive_monitoring()
                    if not gate.get("allow"):
                        return ToolResult(
                            status="blocked",
                            message=gate.get("message", "Action blocked."),
                        )
                    if gate.get("dry_run"):
                        return ToolResult(
                            status="success",
                            message="[DRY RUN] Would start global keylogger.",
                            data={"dry_run": True},
                        )
                except ImportError:
                    pass

                out = _svc.start(
                    max_buffer=request.max_buffer,
                    include_release=request.include_release,
                )
                if not out.get("ok"):
                    return ToolResult(
                        status="error",
                        message=out.get("message", "Could not start keylogger."),
                        data=out,
                        recovery_tip="If already running, call 'stop' first.",
                    )
                global _hud
                _hud = CuaHUD()
                _hud.start()
                return ToolResult(
                    status="success",
                    message="Global keylogger started.",
                    data=out,
                )

            if op == "stop":
                out = _svc.stop()
                global _hud
                if _hud:
                    _hud.stop()
                    _hud = None
                return ToolResult(status="success", message="Global keylogger stopped.", data=out)

            if op == "status":
                out = _svc.status()
                global _hud
                out["hud_active"] = _hud is not None
                return ToolResult(status="success", message="Keylogger status.", data=out)

            if op == "read":
                out = _svc.read(limit=request.limit, flush=request.flush)
                return ToolResult(
                    status="success",
                    message=f"Read {out.get('count', 0)} key events.",
                    data=out,
                )

            if op == "clear":
                out = _svc.clear()
                return ToolResult(status="success", message="Keylogger buffer cleared.", data=out)

            return ToolResult(status="error", message=f"Unknown operation: {op}")

        except Exception as e:
            logger.error("global_keylogger error: %s", e)
            global _hud
            if _hud:
                _hud.stop()
                _hud = None
            return ToolResult(
                status="error",
                message=str(e),
                recovery_tip="Ensure pynput can install the low-level hook (user session, not elevated mismatch).",
            )

else:
    logger.warning("global_keylogger not available - missing app instance")


__all__ = ["global_keylogger"]
