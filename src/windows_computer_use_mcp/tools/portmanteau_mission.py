"""Mission-level agentic orchestration with autonomous execution loop.

PORTMANTEAU PATTERN RATIONALE:
Consolidates high-level automation orchestration into a single tool.
The `run` operation decomposes a natural-language goal into steps,
executes each with retry + verification, and returns pass/fail per step.
"""

import logging
import time
import uuid
from pathlib import Path
from typing import Any

from windows_computer_use_mcp.app import app

try:
    from fastmcp import Context

    SAMPLING_AVAILABLE = True
except ImportError:
    SAMPLING_AVAILABLE = False
    Context = Any

logger = logging.getLogger(__name__)

from windows_computer_use_mcp.retry_policy import RetryPolicy
from windows_computer_use_mcp.tools.models import MissionOperationRequest, ToolResult

_MISSIONS: dict[str, dict[str, Any]] = {}
_MAX_CONSECUTIVE_FAILURES = 5
_WORKFLOW_CONTEXT: dict[str, Any] = {}


def _presets_dir() -> Path:
    """Return the presets directory (project root/presets/)."""
    return Path(__file__).resolve().parent.parent.parent.parent / "presets"


def _check_window_alive(handle: int | None) -> bool:
    """Return True if the window handle still exists."""
    if handle is None:
        return True
    try:
        from pywinauto import Desktop

        Desktop(backend="uia").window(handle=handle).exists(timeout=0.5)
        return True
    except Exception:
        return False


def _relaunch_app(app_path: str | None) -> bool:
    """Try to re-launch an application."""
    if not app_path:
        return False
    try:
        from pywinauto import Application

        Application().start(app_path)
        return True
    except Exception as e:
        logger.warning("relaunch failed for %s: %s", app_path, e)
        return False


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


async def _run_steps(steps: list[dict], ctx: Context | None, mission_id: str, label: str = "") -> ToolResult:
    """Execute a list of steps with verify + retry. Shared by run_mission and run_preset."""
    _MISSIONS[mission_id] = {"status": "running", "goal": label, "steps": steps, "started": time.time()}
    if ctx:
        await ctx.info(f"Running {label or 'workflow'} ({len(steps)} steps)")
    results = []
    total = len(steps)
    consecutive_failures = 0
    _WORKFLOW_CONTEXT[mission_id] = {}

    for i, step in enumerate(steps):
        mission_state = _MISSIONS.get(mission_id)
        if mission_state is None or mission_state.get("status") == "cancelled":
            return ToolResult(
                status="blocked",
                message="Mission cancelled mid-execution.",
                data={"mission_id": mission_id, "completed": i, "total": total},
            )

        tool_name = step.get("tool", "")
        params = step.get("params", {})
        label = step.get("label", tool_name)
        expected = step.get("expect", None)
        window_handle = step.get("window_handle") or params.get("window_handle") or params.get("handle")

        # Self-heal: check if target window is still alive
        app_path = step.get("app_path")
        if not _check_window_alive(window_handle) and app_path:
            if ctx:
                await ctx.info(f"Window lost — re-launching {app_path}")
            if _relaunch_app(app_path):
                time.sleep(2)
            else:
                logger.warning("Could not re-launch %s — skipping step", app_path)
                consecutive_failures += 1
                results.append(
                    {
                        "step": i + 1,
                        "label": label,
                        "tool": tool_name,
                        "success": False,
                        "message": "Window dead, relaunch failed",
                    }
                )
                if consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
                    break
                continue

        # Cross-app data flow: resolve $ref references in params
        if tool_name in ("elements", "smart", "keyboard", "mouse"):
            for k, v in list(params.items()):
                if isinstance(v, str) and v.startswith("$ref:"):
                    ref_key = v[5:]
                    params[k] = _WORKFLOW_CONTEXT[mission_id].get(ref_key, v)

        if ctx:
            await ctx.info(f"Step {i + 1}/{total}: {label}")
            await ctx.report_progress(int(5 + (i / total) * 85), 100)

        # Telemetry-driven strategy selection
        step_op = params.get("operation", "")
        best_strategy = None
        try:
            from windows_computer_use_mcp.telemetry import get_best_strategy

            best_strategy = get_best_strategy(tool_name, step_op)
            if best_strategy and tool_name in ("elements",):
                if best_strategy in ("by_title", "by_auto_id", "by_control_id", "by_class_and_type"):
                    params["_prefer_strategy"] = best_strategy
        except Exception:
            pass

        def _try_call(_tn=tool_name, _tp=params):
            return _call_tool(_tn, _tp)

        def _verify(r, _step=step):
            return _verify_step_outcome(_step, r) if isinstance(r, ToolResult) else False

        policy = RetryPolicy(max_attempts=2, base_delay=1.0)
        retry_result = policy.execute(
            _try_call,
            verify_fn=_verify,
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

        # Log step outcome to telemetry
        try:
            from windows_computer_use_mcp.telemetry import log_action

            log_action(
                tool=f"mission.{tool_name}",
                operation=step_op,
                target=label,
                strategy_used=best_strategy,
                success=retry_result.success,
                error=retry_result.message if not retry_result.success else None,
                session_id=mission_id,
            )
        except Exception:
            pass

        # Self-heal: track consecutive failures
        if retry_result.success:
            consecutive_failures = 0
        else:
            consecutive_failures += 1
            logger.warning(
                "Mission step %d/%d failed (%d consecutive): %s",
                i + 1,
                total,
                consecutive_failures,
                retry_result.message,
            )

        if expected and retry_result.success and isinstance(retry_result.data, dict):
            step_result["verified"] = retry_result.data.get("verify")

        # Data flow: store extract results in workflow context
        if retry_result.success and tool_name in ("elements", "smart") and step.get("store_as"):
            store_key = step["store_as"]
            result_data = {}
            if isinstance(retry_result.data, dict):
                result_data = retry_result.data
            _WORKFLOW_CONTEXT[mission_id][store_key] = result_data
            step_result["stored"] = store_key

        results.append(step_result)

        if consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
            logger.warning("Aborting mission: %d consecutive failures", consecutive_failures)
            if ctx:
                await ctx.info(f"Aborting — {consecutive_failures} consecutive failures.")
            break

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
        recovery_tip="Use automation_mission(operation='status', mission_id=...) for details."
        if success_count < total
        else None,
    )


async def _run_mission(goal: str, ctx: Context | None, mission_id: str) -> ToolResult:
    """Decompose goal and execute steps."""
    steps = await _decompose_goal(goal, ctx)
    if not steps:
        return ToolResult(status="error", message=f"Could not decompose goal into steps: {goal}")
    return await _run_steps(steps, ctx, mission_id, goal)


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
            steps.append(
                {
                    "tool": "system",
                    "params": {"operation": "start_app", "app_path": "notepad.exe"},
                    "label": "Open Notepad",
                }
            )
            steps.append(
                {"tool": "windows", "params": {"operation": "find", "title": "Notepad"}, "label": "Find Notepad window"}
            )
        if "type" in g or "write" in g or "text" in g:
            steps.append(
                {
                    "tool": "elements",
                    "params": {
                        "operation": "set_text",
                        "title": "Text Editor",
                        "text": "Hello from automation mission",
                    },
                    "label": "Type text",
                }
            )
        if "save" in g:
            steps.append(
                {"tool": "keyboard", "params": {"operation": "hotkey", "keys": ["ctrl", "s"]}, "label": "Save (Ctrl+S)"}
            )
        if "close" in g or "exit" in g:
            steps.append(
                {"tool": "keyboard", "params": {"operation": "hotkey", "keys": ["alt", "f4"]}, "label": "Close Notepad"}
            )
        if not steps:
            steps.append(
                {"tool": "windows", "params": {"operation": "find", "title": "Notepad"}, "label": "Find Notepad"}
            )
        return steps

    if "install" in g or "setup" in g:
        return [
            {"tool": "system", "params": {"operation": "start_app", "app_path": goal}, "label": "Launch installer"},
            {
                "tool": "windows",
                "params": {"operation": "wait_for_window", "title": "Setup", "timeout": 30},
                "label": "Wait for setup window",
            },
            {
                "tool": "elements",
                "params": {"operation": "click", "title": "Next", "control_type": "Button"},
                "label": "Click Next",
                "expect": "next_dialog",
            },
            {
                "tool": "elements",
                "params": {"operation": "click", "title": "Install", "control_type": "Button"},
                "label": "Click Install",
            },
            {
                "tool": "windows",
                "params": {"operation": "wait_for_window", "title": "Finish", "timeout": 60},
                "label": "Wait for completion",
            },
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

            if operation == "run_preset":
                preset_name = request.preset_name or goal
                presets_dir = _presets_dir()
                if not preset_name or preset_name == "list":
                    presets = sorted(p.stem for p in presets_dir.glob("*.json") if p.stem != "list_presets")
                    return ToolResult(
                        status="success", message=f"Available presets: {', '.join(presets)}", data={"presets": presets}
                    )
                preset_path = presets_dir / f"{preset_name}.json"
                if not preset_path.exists():
                    return ToolResult(
                        status="error",
                        message=f"Preset '{preset_name}' not found.",
                        recovery_tip="Available: "
                        + ", ".join(p.stem for p in presets_dir.glob("*.json") if p.stem != "list_presets"),
                    )
                import json

                preset = json.loads(preset_path.read_text(encoding="utf-8"))
                steps = preset.get("steps", [])
                return await _run_steps(steps, ctx, mission_id, preset.get("name", preset_name))

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

            if operation == "workflow":
                app_name = request.app
                actions = request.actions
                if not actions:
                    return ToolResult(status="error", message="'actions' list required for workflow operation.")
                if app_name:
                    try:
                        from pywinauto import Application

                        Application().start(app_name)
                        if ctx:
                            await ctx.info(f"Started {app_name}")
                    except Exception as e:
                        logger.warning("workflow start_app %s failed: %s", app_name, e)

                results = []
                max_time = request.timeout or 120
                deadline = time.time() + max_time
                for i, action in enumerate(actions):
                    if time.time() > deadline:
                        results.append(
                            {"step": i + 1, "label": action.get("label"), "success": False, "error": "timeout"}
                        )
                        break
                    tool_name = action.get("tool", "")
                    params = action.get("params", {})
                    label = action.get("label", tool_name)
                    if ctx:
                        await ctx.info(f"Workflow step {i + 1}/{len(actions)}: {label}")

                    def _exec(t=tool_name, p=params):
                        return _call_tool(t, p)

                    policy = RetryPolicy(max_attempts=2, base_delay=1.0)
                    retry_result = policy.execute(_exec, label=label)
                    results.append(
                        {
                            "step": i + 1,
                            "label": label,
                            "tool": tool_name,
                            "success": retry_result.success,
                            "attempts": retry_result.attempts,
                            "message": retry_result.message,
                        }
                    )

                success_count = sum(1 for r in results if r["success"])
                return ToolResult(
                    status="success" if success_count == len(results) else "blocked",
                    message=f"Workflow: {success_count}/{len(results)} steps succeeded.",
                    data={"steps": results, "total": len(results), "succeeded": success_count},
                )

            if operation in ("record", "replay"):
                from windows_computer_use_mcp.mission_store import clear_mission, get_steps, record_step

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
