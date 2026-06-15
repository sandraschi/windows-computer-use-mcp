"""Task runner portmanteau — closed-loop computer use assistant."""

from __future__ import annotations

import logging
import time

from windows_computer_use_mcp import task_engine
from windows_computer_use_mcp.app_profiles import list_profiles
from windows_computer_use_mcp.template_library import list_templates

try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    app = None

from windows_computer_use_mcp.tools.models import TaskOperationRequest, ToolResult

if app is not None:

    @app.tool(
        name="automation_task",
        description="""Closed-loop task runner — the MVP computer use assistant.

WHAT IT DOES:
Executes a list of steps (shortcut, dialog, wait_stable, assert_file, focus, screenshot, click, preflight)
with automatic retry, refocus recovery, and per-step evidence (screenshot paths).

WHEN TO USE:
- Prefer over manual tool chaining for multi-step GUI workflows
- VRoid export: shortcut steps + dialog + assert_file in one call
- Returns evidence trail on failure for host LLM review

OPERATIONS:
- run: execute steps
- status: query task session
- cancel: mark task cancelled
- list_profiles: app profiles (foreground policy, window title, stable_region)
- list_templates: per-app template library manifest (T2.3)

See docs/CUA_ASSISTANT_TODO.md and docs/MEMOPS_CUA.md.
""",
    )
    def automation_task(request: TaskOperationRequest) -> ToolResult:
        """Task runner portmanteau."""
        try:
            op = request.operation
            ts = time.time()

            if op == "list_profiles":
                profiles = list_profiles()
                return ToolResult(
                    status="success",
                    message=f"{len(profiles)} app profiles.",
                    data={"profiles": profiles, "timestamp": ts},
                )

            if op == "list_templates":
                app_name = (request.app or "vroidstudio").strip().lower()
                templates = list_templates(app_name)
                return ToolResult(
                    status="success",
                    message=f"{len(templates)} templates for {app_name}.",
                    data={"app": app_name, "templates": templates, "timestamp": ts},
                )

            if op == "status":
                if not request.task_id:
                    return ToolResult(status="error", message="status requires task_id.")
                session = task_engine.get_task(request.task_id)
                if not session:
                    return ToolResult(status="error", message=f"Unknown task_id: {request.task_id}")
                return ToolResult(
                    status="success",
                    message=f"Task {session.status}.",
                    data=session.to_dict(),
                )

            if op == "cancel":
                if not request.task_id:
                    return ToolResult(status="error", message="cancel requires task_id.")
                ok = task_engine.cancel_task(request.task_id)
                if not ok:
                    return ToolResult(status="error", message=f"Unknown task_id: {request.task_id}")
                return ToolResult(status="success", message="Task cancelled.", data={"task_id": request.task_id})

            if op == "run":
                if not request.steps:
                    return ToolResult(status="error", message="run requires steps list.")
                app_name = (request.app or "vroidstudio").strip().lower()
                session = task_engine.run_task(
                    app=app_name,
                    steps=request.steps,
                    task_id=request.task_id,
                    window_handle=request.window_handle,
                    output_dir=request.output_dir,
                )
                if session.status == "complete":
                    return ToolResult(
                        status="success",
                        message=f"Task {session.task_id} complete ({len(session.steps)} steps).",
                        data=session.to_dict(),
                    )
                return ToolResult(
                    status="error",
                    message=session.error or f"Task {session.status}",
                    data=session.to_dict(),
                    recovery_tip="Review evidence[] screenshots and retry failed step with refocus_retry or abort.",
                )

            return ToolResult(status="error", message=f"Unknown operation: {op}")

        except Exception as exc:
            logger.exception("automation_task failed")
            return ToolResult(
                status="error",
                message=f"Task operation failed: {exc}",
                recovery_tip="Validate step schema in docs/CUA_ASSISTANT_TODO.md.",
            )
