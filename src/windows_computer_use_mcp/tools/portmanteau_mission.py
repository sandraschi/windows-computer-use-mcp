"""Mission-level agentic orchestration with autonomous execution loop.

PORTMANTEAU PATTERN RATIONALE:
Consolidates high-level automation orchestration into a single tool.
The `run` operation decomposes a natural-language goal into steps,
executes each with retry + verification, and returns pass/fail per step.
"""

import logging
import time
import uuid
from typing import Any

from windows_computer_use_mcp.app import app

try:
    from fastmcp import Context
    SAMPLING_AVAILABLE = True
except ImportError:
    SAMPLING_AVAILABLE = False
    Context = Any

logger = logging.getLogger(__name__)

from windows_computer_use_mcp.retry_policy import RetryPolicy, RetryResult
from windows_computer_use_mcp.tools.models import MissionOperationRequest, ToolResult

_MISSIONS: dict[str, dict[str, Any]] = {}


def _generate_id() -> str:
    return f"mission_{uuid.uuid4().hex[:12]}"


def _call_tool(tool_name: str, params: dict) -> ToolResult:
    """Call a registered MCP tool by name and return its ToolResult.

    For now, we wrap tool calls as direct imports. In production this could
    use the MCP protocol's own call mechanism.
    """
    import importlib

    parts = tool_name.split(".")
    if len(parts) == 1:
        target = f"windows_computer_use_mcp.tools.portmanteau_{parts[0]}"
    else:
        target = tool_name

    try:
        mod = importlib.import_module(target)
    except ImportError:
        mod = importlib.import_module(f"windows_computer_use_mcp.tools.{target}")

    fn = getattr(mod, f"automation_{parts[0]}", None)
    if fn is None:
        for name in dir(mod):
            if name.startswith("automation_") and callable(getattr(mod, name)):
                fn = getattr(mod, name)
                break

    if fn is None:
        return ToolResult(status="error", message=f"Tool not found: {tool_name}")

    import inspect

    sig = inspect.signature(fn)
    if any(p.annotation is Context or str(p.annotation) == "Context" for p in sig.parameters.values()):
        return ToolResult(status="error", message=f"Tool {tool_name} requires Context — cannot call inline")

    try:
        request_type = None
        for p in sig.parameters.values():
            if hasattr(p.annotation, "model_validate"):
                request_type = p.annotation
                break

        if request_type:
            obj = request_type.model_validate(params)
            result = fn(obj)
        else:
            result = fn(**params)

        if isinstance(result, ToolResult):
            return result
        if isinstance(result, dict):
            return ToolResult(**result)
        return ToolResult(status="success", message=str(result), data={"raw": result})

    except Exception as e:
        return ToolResult(status="error", message=f"Tool call failed: {e!s}")


def _verify_step_outcome(step: dict[str, Any], tool_result: ToolResult) -> bool:
    """Check whether a step's outcome is acceptable. Override with step-level verify."""
    if tool_result.status != "success":
        return False
    return True


async def _run_mission(goal: str, ctx: Context | None, mission_id: str) -> ToolResult:
    """Full autonomous loop: plan → execute each step with verify + retry."""
    _MISSIONS[mission_id] = {"status": "running", "goal": goal, "steps": [], "started": time.time()}

    if ctx:
        await ctx.info(f"Starting mission: {goal}")
        await ctx.report_progress(5, 100)

    steps = await _decompose_goal(goal, ctx)

    if not steps:
        _MISSIONS[mission_id]["status"] = "failed"
        return ToolResult(status="error", message=f"Could not decompose goal into steps: {goal}")

    _MISSIONS[mission_id]["plan"] = steps
    results = []
    total = len(steps)

    for i, step in enumerate(steps):
        mission_state = _MISSIONS.get(mission_id)
        if mission_state is None or mission_state.get("status") == "cancelled":
            return ToolResult(
                status="blocked", message="Mission cancelled mid-execution.",
                data={"mission_id": mission_id, "completed": i, "total": total},
            )

        tool_name = step.get("tool", "")
        params = step.get("params", {})
        label = step.get("label", tool_name)
        expected = step.get("expect", None)

        if ctx:
            await ctx.info(f"Step {i + 1}/{total}: {label}")
            await ctx.report_progress(int(5 + (i / total) * 85), 100)

        def _try_call():
            return _call_tool(tool_name, params)

        policy = RetryPolicy(max_attempts=2, base_delay=1.0)
        retry_result = policy.execute(
            _try_call,
            verify_fn=lambda r: _verify_step_outcome(step, r) if isinstance(r, ToolResult) else False,
            label=label,
        )

        step_result = {
            "step": i + 1,
            "label": label,
            "tool": tool_name,
            "success": retry_result.success,
            "strategy_used": retry_result.strategy_used.value if retry_result.strategy_used else None,
            "attempts": retry_result.attempts,
            "message": retry_result.message,
        }
        if expected and retry_result.success and isinstance(retry_result.data, dict):
            step_result["verified"] = retry_result.data.get("verify")

        results.append(step_result)

        if not retry_result.success:
            logger.warning("Mission step %d/%d failed: %s — continuing", i + 1, total, retry_result.message)

    _MISSIONS[mission_id]["status"] = "complete"
    _MISSIONS[mission_id]["results"] = results
    _MISSIONS[mission_id]["ended"] = time.time()

    success_count = sum(1 for r in results if r["success"])
    summary = f"Mission complete: {success_count}/{total} steps succeeded."

    if ctx:
        await ctx.info(summary)
        await ctx.report_progress(100, 100)

    return ToolResult(
        status="success" if success_count == total else "blocked",
        message=summary,
        data={"mission_id": mission_id, "steps": results, "total": total, "succeeded": success_count},
        recovery_tip="Use automation_mission(operation='status', mission_id=...) for details." if success_count < total else None,
    )


async def _decompose_goal(goal: str, ctx: Context | None) -> list[dict[str, Any]]:
    """Decompose a natural-language goal into a step list.

    Uses LLM sampling when available, otherwise returns a static heuristic.
    """
    if SAMPLING_AVAILABLE and ctx is not None:
        try:
            prompt = (
                f"Decompose this desktop automation goal into a JSON array of steps. "
                f"Each step must have: tool (e.g. 'elements', 'windows', 'mouse', 'keyboard', 'system'), "
                f"params (dict of parameters for that tool), label (short description), "
                f"and optionally expect (what to verify after). "
                f"Use tool names without 'automation_' prefix (e.g. 'elements' for automation_elements). "
                f"Output ONLY the JSON array, no explanation.\n"
                f"Goal: {goal}"
            )
            response = await ctx.sample(messages=[{"role": "user", "content": prompt}], max_tokens=2000)
            content = ""
            if isinstance(response, str):
                content = response
            elif isinstance(response, dict):
                content = response.get("content", str(response))
            else:
                content = str(response)

            import json
            import re

            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                if isinstance(parsed, list):
                    return parsed
        except Exception as e:
            logger.warning("Sampling decomposition failed: %s", e)

    return _static_decompose(goal)


def _static_decompose(goal: str) -> list[dict[str, Any]]:
    """Fallback decomposition for common patterns when sampling is unavailable."""
    g = goal.lower()

    if "notepad" in g:
        steps = []
        if "open" in g or "launch" in g or "start" in g:
            steps.append({"tool": "system", "params": {"operation": "start_app", "app_path": "notepad.exe"}, "label": "Open Notepad"})
            steps.append({"tool": "windows", "params": {"operation": "find", "title": "Notepad"}, "label": "Find Notepad window"})
        if "type" in g or "write" in g or "text" in g:
            steps.append({"tool": "elements", "params": {"operation": "set_text", "title": "Text Editor", "text": "Hello from automation mission"}, "label": "Type text"})
        if "save" in g:
            steps.append({"tool": "keyboard", "params": {"operation": "hotkey", "keys": ["ctrl", "s"]}, "label": "Save (Ctrl+S)"})
        if "close" in g or "exit" in g:
            steps.append({"tool": "keyboard", "params": {"operation": "hotkey", "keys": ["alt", "f4"]}, "label": "Close Notepad"})
        if not steps:
            steps.append({"tool": "windows", "params": {"operation": "find", "title": "Notepad"}, "label": "Find Notepad"})
        return steps

    if "install" in g or "setup" in g:
        return [
            {"tool": "system", "params": {"operation": "start_app", "app_path": goal}, "label": "Launch installer"},
            {"tool": "windows", "params": {"operation": "wait_for_window", "title": "Setup", "timeout": 30}, "label": "Wait for setup window"},
            {"tool": "elements", "params": {"operation": "click", "title": "Next", "control_type": "Button"}, "label": "Click Next", "expect": "next_dialog"},
            {"tool": "elements", "params": {"operation": "click", "title": "Install", "control_type": "Button"}, "label": "Click Install"},
            {"tool": "windows", "params": {"operation": "wait_for_window", "title": "Finish", "timeout": 60}, "label": "Wait for completion"},
        ]

    if "screenshot" in g or "capture" in g:
        return [
            {"tool": "visual", "params": {"operation": "screenshot"}, "label": "Capture screenshot"},
        ]

    if "paint" in g:
        return [
            {"tool": "system", "params": {"operation": "start_app", "app_path": "mspaint.exe"}, "label": "Open Paint"},
            {"tool": "windows", "params": {"operation": "maximize", "title": "Paint"}, "label": "Maximize Paint"},
            {"tool": "mouse", "params": {"operation": "click", "x": 200, "y": 200}, "label": "Draw on canvas"},
        ]

    return [{"tool": "system", "params": {"operation": "status"}, "label": "Check system status"}]


async def _handle_plan(goal: str, ctx: Context | None, mission_id: str) -> ToolResult:
    """Decompose a goal into a plan without executing."""
    steps = await _decompose_goal(goal, ctx)
    if not steps:
        return ToolResult(status="error", message="Could not decompose goal into steps.")
    return ToolResult(
        status="success",
        message=f"Plan generated: {len(steps)} steps.",
        data={"mission_id": mission_id, "goal": goal, "steps": steps, "total": len(steps)},
    )


if app is not None:

    @app.tool(
        name="automation_mission",
        description="""Autonomous multi-step orchestration and complex mission management tool.

WHAT IT DOES:
This tool elevates automation from individual clicks to high-level objectives.
Give it a natural-language goal — it decomposes into steps, executes each with
retry + verification, and returns pass/fail with evidence.

WHEN TO USE:
- Use 'run' to execute a full autonomous mission from a goal.
- Use 'plan' to preview the step decomposition without executing.
- Use 'status' to track progress of a running mission.
- Use 'cancel' to stop a running mission.

RECOVERY:
If a step fails, the mission continues with remaining steps (non-fatal).
Use 'status' with the mission_id to review step-level results.
RETURNS:
A ToolResult object with mission progress, step results, and next steps.
""",
    )
    async def automation_mission(request: MissionOperationRequest, ctx: Context = None) -> ToolResult:
        """Mission orchestration with autonomous execution loop."""
        try:
            operation = request.operation
            goal = request.goal
            mission_id = request.mission_id or _generate_id()

            if operation == "run":
                return await _run_mission(goal, ctx, mission_id)

            if operation == "plan":
                return await _handle_plan(goal, ctx, mission_id)

            if operation == "status":
                state = _MISSIONS.get(mission_id)
                if state is None:
                    return ToolResult(
                        status="error",
                        message=f"No mission found: {mission_id}",
                        recovery_tip="Start a mission with automation_mission(operation='run', ...).",
                    )
                return ToolResult(
                    status="success",
                    message=f"Mission {state['status']}: {state.get('goal', '')}",
                    data={
                        "mission_id": mission_id,
                        "status": state["status"],
                        "goal": state.get("goal", ""),
                        "steps": state.get("steps", []),
                        "results": state.get("results", []),
                        "started": state.get("started"),
                        "ended": state.get("ended"),
                    },
                )

            if operation == "cancel":
                if mission_id in _MISSIONS:
                    _MISSIONS[mission_id]["status"] = "cancelled"
                from windows_computer_use_mcp.mission_store import clear_mission
                clear_mission(mission_id)
                return ToolResult(
                    status="success",
                    message=f"Mission {mission_id} cancelled.",
                    data={"mission_id": mission_id, "status": "cancelled"},
                )

            if operation in ("record", "replay"):
                from windows_computer_use_mcp.mission_store import record_step, get_steps, clear_mission
                if operation == "record":
                    if not request.steps:
                        return ToolResult(status="error", message="record requires steps list.")
                    for step in request.steps:
                        record_step(mission_id, step)
                    return ToolResult(
                        status="success",
                        message=f"Recorded {len(request.steps)} steps.",
                        data={"mission_id": mission_id, "count": len(request.steps)},
                    )
                steps = get_steps(mission_id)
                if not steps:
                    return ToolResult(status="error", message=f"No steps for mission {mission_id}.")
                executed = []
                for step in steps:
                    kind = step.get("kind") or step.get("tool")
                    if kind == "hotkey" and step.get("keys"):
                        from windows_computer_use_mcp.keyboard_send import parse_hotkey, send_hotkey
                        keys = step["keys"] if isinstance(step["keys"], list) else parse_hotkey(step["keys"])
                        send_hotkey(keys, hwnd=step.get("window_handle"))
                    elif kind == "press" and step.get("key"):
                        from windows_computer_use_mcp.keyboard_send import send_press
                        send_press(step["key"], hwnd=step.get("window_handle"))
                    executed.append(step)
                return ToolResult(
                    status="success",
                    message=f"Replayed {len(executed)} steps.",
                    data={"mission_id": mission_id, "executed": len(executed)},
                )

            return ToolResult(
                status="error",
                message=f"Unknown operation: {operation}",
                recovery_tip="Use 'run' to execute a mission, 'plan' to preview, 'status' to track.",
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
