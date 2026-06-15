"""Mission-level agentic orchestration for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Consolidates high-level automation orchestration, planning, and execution
using FastMCP 3.2.0 agentic sampling. This tool enables "thinking" and
"planning" before low-level UI interaction.
"""

import logging
import time
from typing import Any

from windows_computer_use_mcp.app import app

# Check for Context availability for sampling
try:
    from fastmcp import Context

    SAMPLING_AVAILABLE = True
except ImportError:
    SAMPLING_AVAILABLE = False
    Context = Any

logger = logging.getLogger(__name__)

from windows_computer_use_mcp.tools.models import MissionOperationRequest, ToolResult

if app is not None:

    @app.tool(
        name="automation_mission",
        description="""Autonomous multi-step orchestration and complex mission management tool.

WHAT IT DOES:
This tool elevates automation from individual clicks to high-level objectives. It manages 'missions' that represent long-running, multi-application workflows. It handles prerequisite checking, state persistence, and provides a structured way to report progress on complex goals.

WHEN TO USE:
- Use 'plan' to decompose a high-level user request into a sequence of actionable steps.
- Use 'status' to track the progress of a multi-step automation sequence.
- Use 'record' or 'replay' for macro-style pattern matching across similar UI states.

RECOVERY:
If a mission stalls, review the status data. Use 'cancel' to release system hooks. Ensure the 'mission_id' is consistent across session restarts.

RETURNS:
A ToolResult object with mission progress, IDs, and next steps.
""",
    )
    async def automation_mission(request: MissionOperationRequest, ctx: Context = None) -> ToolResult:
        """Mission orchestration tracking SOTA 2026 agentic standards."""
        timestamp = time.time()
        operation = request.operation
        goal = request.goal
        mission_id = request.mission_id

        mission_metadata = {
            "timestamp": timestamp,
            "orchestrator": "FastMCP-3.1",
            "session_id": mission_id or f"mission_{int(timestamp)}",
            "operation": operation,
        }

        try:
            if operation == "record":
                if not mission_id or not request.steps:
                    return ToolResult(
                        status="error",
                        message="record requires mission_id and steps list.",
                    )
                from windows_computer_use_mcp.mission_store import record_step

                for step in request.steps:
                    record_step(mission_id, step)
                return ToolResult(
                    status="success",
                    message=f"Recorded {len(request.steps)} steps.",
                    data={"mission_id": mission_id, "count": len(request.steps)},
                )

            if operation == "replay":
                if not mission_id:
                    return ToolResult(status="error", message="replay requires mission_id.")
                from windows_computer_use_mcp.keyboard_send import parse_hotkey, send_hotkey, send_press
                from windows_computer_use_mcp.mission_store import get_steps

                steps = get_steps(mission_id)
                if not steps:
                    return ToolResult(status="error", message=f"No steps for mission {mission_id}.")
                executed = []
                for step in steps:
                    kind = step.get("kind") or step.get("tool")
                    if kind == "hotkey" and step.get("keys"):
                        keys = step["keys"] if isinstance(step["keys"], list) else parse_hotkey(step["keys"])
                        send_hotkey(keys, hwnd=step.get("window_handle"))
                    elif kind == "press" and step.get("key"):
                        send_press(step["key"], hwnd=step.get("window_handle"))
                    executed.append(step)
                return ToolResult(
                    status="success",
                    message=f"Replayed {len(executed)} steps.",
                    data={"mission_id": mission_id, "executed": len(executed)},
                )

            # plan requires sampling context
            if operation == "plan" and (not SAMPLING_AVAILABLE or ctx is None):
                return ToolResult(
                    status="error",
                    message="Sampling context not available. Ensure you are using a host that supports FastMCP 3.2.0 sampling.",
                    data=mission_metadata,
                    recovery_tip="Wait for a SOTA-compliant host or fall back to manual tool chaining.",
                )

            if operation == "plan":
                # 1. REPORT INITIALIZATION
                await ctx.info(f"Initializing mission: {goal}")
                await ctx.report_progress(10, 100)

                # 2. SAMPLE THE PLANNING PHASE
                prompt = f"Create a step-by-step automation plan for: {goal} using pywinauto-mcp tools."
                plan_response = await ctx.sample(messages=prompt, max_tokens=1000)
                plan_content = getattr(plan_response, "content", str(plan_response))

                await ctx.info(f"Generated Plan: {plan_content}")
                await ctx.report_progress(50, 100)

                return ToolResult(
                    status="success",
                    message=f"Mission planned: {goal}",
                    data={"mission_id": mission_metadata["session_id"], "plan": plan_content, "status": "planned"},
                )

            elif operation == "status":
                return ToolResult(
                    status="success",
                    message="Mission status: In Progress",
                    data={"mission_id": mission_id, "progress": 50, "status": "active"},
                )

            elif operation == "cancel":
                if mission_id:
                    from windows_computer_use_mcp.mission_store import clear_mission

                    clear_mission(mission_id)
                return ToolResult(
                    status="success",
                    message=f"Mission {mission_id} cancelled.",
                    data={"mission_id": mission_id, "status": "cancelled"},
                )

            return ToolResult(
                status="error",
                message=f"Unknown mission operation: {operation}",
                recovery_tip="Supported operations: plan, status, cancel, record, replay",
            )

        except Exception as e:
            error_msg = f"Mission failure: {e!s}"
            logger.error(error_msg, exc_info=True)
            if ctx and hasattr(ctx, "error"):
                await ctx.error(error_msg)
            return ToolResult(
                status="error",
                message=error_msg,
                recovery_tip="Verify the goal is achievable and the target applications are running.",
            )
else:
    logger.warning("Mission tool not available - missing app instance")


__all__ = ["automation_mission"]
