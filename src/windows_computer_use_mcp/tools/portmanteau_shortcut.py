"""Semantic app shortcut portmanteau — VRoid Studio and future registries."""

from __future__ import annotations

import logging
import time

from windows_computer_use_mcp import shortcut_engine

try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    app = None

from windows_computer_use_mcp.tools.models import ShortcutOperationRequest, ToolResult

if app is not None:

    @app.tool(
        name="automation_shortcut",
        description="""Semantic application shortcuts — send by action name, not raw key codes.

WHAT IT DOES:
Maps app-specific action names (e.g. vroidstudio/export_vrm → F8) to keyboard sequences,
optionally focuses the target HWND (win32 backend), and waits for UI stability after send.

WHEN TO USE:
- send: execute a named shortcut (prefer over raw automation_keyboard hotkey)
- list: enumerate shortcuts for an app
- describe: metadata for one action

SUPPORTED APPS: vroidstudio (alias vroid, vroid_studio)

RECOVERY:
Call automation_windows(focus) first. Set windows_computer_use_mcp_KEYBOARD=win32 for HWND-targeted send.
""",
    )
    def automation_shortcut(request: ShortcutOperationRequest) -> ToolResult:
        """App-aware shortcut portmanteau."""
        try:
            op = request.operation
            ts = time.time()
            app_name = (request.app or "").strip().lower()

            if op == "list":
                if not app_name:
                    from windows_computer_use_mcp.app_shortcuts.registry import list_apps

                    return ToolResult(
                        status="success",
                        message="Registered shortcut apps.",
                        data={"apps": list_apps(), "timestamp": ts},
                    )
                shortcuts = shortcut_engine.list_app_shortcuts(app_name)
                return ToolResult(
                    status="success",
                    message=f"{len(shortcuts)} shortcuts for {app_name}.",
                    data={"app": app_name, "shortcuts": shortcuts, "timestamp": ts},
                )

            if op == "describe":
                if not app_name or not request.action:
                    return ToolResult(status="error", message="describe requires app and action.")
                data = shortcut_engine.describe_shortcut(app_name, request.action)
                return ToolResult(status="success", message="Shortcut metadata.", data={**data, "timestamp": ts})

            if op == "send":
                if not app_name or not request.action:
                    return ToolResult(status="error", message="send requires app and action.")
                try:
                    from windows_computer_use_mcp.safety import before_mutation

                    gate = before_mutation(read_only=False)
                    if not gate.get("allow"):
                        return ToolResult(status="blocked", message=gate.get("message", "blocked"))
                    if gate.get("dry_run"):
                        return ToolResult(
                            status="success",
                            message=f"[DRY RUN] Would send {app_name}/{request.action}",
                        )
                except ImportError:
                    pass

                data = shortcut_engine.send_shortcut(
                    app_name,
                    request.action,
                    window_handle=request.window_handle,
                    verify_stable=request.verify_stable,
                    pause=request.pause,
                )
                return ToolResult(
                    status="success",
                    message=f"Sent {app_name}/{request.action} ({data['keys']}).",
                    data={**data, "timestamp": ts},
                )

            return ToolResult(status="error", message=f"Unknown operation: {op}")

        except KeyError as exc:
            return ToolResult(
                status="error",
                message=str(exc),
                recovery_tip="Use operation=list to see valid app and action names.",
            )
        except TimeoutError as exc:
            return ToolResult(
                status="error",
                message=str(exc),
                recovery_tip="Increase stable_timeout or set verify_stable=false if animation is expected.",
            )
        except Exception as exc:
            logger.exception("automation_shortcut failed")
            return ToolResult(
                status="error",
                message=f"Shortcut failed: {exc}",
                recovery_tip="Focus target window with automation_windows(focus) and retry.",
            )
