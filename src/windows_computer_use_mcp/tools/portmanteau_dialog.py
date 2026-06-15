"""File dialog portmanteau — path entry with clipboard paste fallback."""

from __future__ import annotations

import logging
import time

from windows_computer_use_mcp import dialog_engine

try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    app = None

from windows_computer_use_mcp.tools.models import DialogOperationRequest, ToolResult

if app is not None:

    @app.tool(
        name="automation_dialog",
        description="""Windows file dialog helpers — set path field and confirm.

WHAT IT DOES:
Fills Save/Open/Export dialog path fields using clipboard paste (default) or typed
entry, then confirms with Enter. Prefer this over manual ctrl+a + type sequences.

WHEN TO USE:
- submit_path: full flow after a Save As / Open / Export shortcut opened a dialog
- set_path: only fill the path field (confirm separately)
- confirm: press Enter after path is already set

RECOVERY:
Ensure the target dialog field is focused (Tab into it if needed). Call
automation_windows(focus) on the parent app first. For long paths, keep use_clipboard=true.
""",
    )
    def automation_dialog(request: DialogOperationRequest) -> ToolResult:
        """Dialog path entry portmanteau."""
        try:
            op = request.operation
            ts = time.time()

            if op == "set_path":
                if not request.path:
                    return ToolResult(status="error", message="set_path requires path.")
                data = dialog_engine.set_path_field(
                    request.path,
                    use_clipboard=request.use_clipboard,
                    select_all_first=request.select_all_first,
                    type_interval=request.type_interval,
                )
                return ToolResult(
                    status="success",
                    message=f"Path field set via {data['method']}.",
                    data={**data, "timestamp": ts},
                )

            if op == "confirm":
                data = dialog_engine.confirm_dialog(
                    confirm_key=request.confirm_key,
                    pause_s=request.pause_before_confirm_s,
                )
                return ToolResult(status="success", message="Dialog confirmed.", data={**data, "timestamp": ts})

            if op == "submit_path":
                if not request.path:
                    return ToolResult(status="error", message="submit_path requires path.")
                data = dialog_engine.submit_path(
                    request.path,
                    use_clipboard=request.use_clipboard,
                    confirm_key=request.confirm_key,
                    pause_before_confirm_s=request.pause_before_confirm_s,
                    select_all_first=request.select_all_first,
                    post_confirm_pause_s=request.post_confirm_pause_s,
                )
                return ToolResult(
                    status="success",
                    message=f"Dialog path submitted via {data['method']}.",
                    data={**data, "timestamp": ts},
                )

            return ToolResult(status="error", message=f"Unknown operation: {op}")

        except ValueError as exc:
            return ToolResult(status="error", message=str(exc))
        except Exception as exc:
            logger.exception("automation_dialog failed")
            return ToolResult(
                status="error",
                message=f"Dialog operation failed: {exc}",
                recovery_tip="Focus the dialog path field and retry. Use automation_windows(focus) first.",
            )
