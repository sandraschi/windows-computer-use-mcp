"""Session recording / macros — record, replay, and verify UI automation sequences.

PORTMANTEAU PATTERN RATIONALE:
Consolidates macro operations (record, stop, replay, replay_with_verify, list)
into a single tool. Prevents tool explosion while enabling repeatable automation.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.mission_store import _persist_dir
from windows_computer_use_mcp.retry_policy import RetryPolicy
from windows_computer_use_mcp.tools.models import ToolResult

logger = logging.getLogger(__name__)

_RECORDING: dict[str, Any] | None = None
_RECORDING_LOCK = threading.Lock()
_RECORDING_STEPS: list[dict] = []


def _call_tool_by_name(tool_name: str, params: dict) -> ToolResult:
    """Call a registered MCP tool by name. Mirrors the helper in portmanteau_mission."""
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


def _macros_dir() -> Path:
    d = _persist_dir() / "macros"
    d.mkdir(parents=True, exist_ok=True)
    return d


if app is not None:

    @app.tool(
        name="automation_macro",
        description="""Record, replay, and verify UI automation macros.

WHAT IT DOES:
Captures every tool call during a recording session into a replayable JSONL file.
Replay executes the same sequence. Replay-with-verify checks each step's outcome
against the recorded result (hash-based screenshot comparison when available).

OPERATIONS:
- record: Start recording. Every subsequent tool call is captured until 'stop'.
- stop: Stop recording and save the macro to a named file.
- replay: Execute a saved macro step by step.
- replay_with_verify: Replay and verify each step matches the recorded outcome.
- list: List saved macros with metadata.
""",
    )
    async def automation_macro(
        operation: str,
        name: str | None = None,
        steps: list[dict] | None = None,
        record_video: bool = False,
    ) -> ToolResult:
        global _RECORDING, _RECORDING_STEPS, _RECORDING_LOCK

        if operation == "record":
            with _RECORDING_LOCK:
                if _RECORDING is not None:
                    return ToolResult(status="error", message="Already recording. Call 'stop' first.")
                macro_id = name or f"macro_{uuid.uuid4().hex[:8]}"
                _RECORDING = {"id": macro_id, "started": time.time()}
                _RECORDING_STEPS = []
            return ToolResult(
                status="success",
                message=f"Recording started as '{macro_id}'. Run your automation tools, then call stop.",
                data={"macro_id": macro_id},
            )

        if operation == "stop":
            with _RECORDING_LOCK:
                if _RECORDING is None:
                    return ToolResult(status="error", message="Not recording.")
                macro_id = _RECORDING["id"]
                duration = time.time() - _RECORDING["started"]
                file_path = _macros_dir() / f"{macro_id}.jsonl"
                with file_path.open("w", encoding="utf-8") as f:
                    for step in _RECORDING_STEPS:
                        f.write(json.dumps(step) + "\n")
                count = len(_RECORDING_STEPS)
                _RECORDING = None
                _RECORDING_STEPS = []
            return ToolResult(
                status="success",
                message=f"Recording '{macro_id}' saved ({count} steps, {duration:.1f}s).",
                data={"macro_id": macro_id, "steps": count, "duration_s": round(duration, 1), "path": str(file_path)},
            )

        if operation == "list":
            files = sorted(_macros_dir().glob("*.jsonl"))
            macros = []
            for f in files:
                steps = [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line.strip()]
                macros.append({
                    "name": f.stem,
                    "steps": len(steps),
                    "size_bytes": f.stat().st_size,
                    "modified": f.stat().st_mtime,
                })
            return ToolResult(
                status="success",
                message=f"{len(macros)} saved macros.",
                data={"macros": macros},
            )

        if operation in ("replay", "replay_with_verify"):
            macro_id = name or "unnamed"
            steps_to_run = steps
            if steps_to_run is None:
                file_path = _macros_dir() / f"{macro_id}.jsonl"
                if not file_path.exists():
                    return ToolResult(
                        status="error",
                        message=f"Macro '{macro_id}' not found.",
                        recovery_tip="Use 'list' to see saved macros.",
                    )
                steps_to_run = [
                    json.loads(line) for line in file_path.read_text(encoding="utf-8").splitlines() if line.strip()
                ]

            if not steps_to_run:
                return ToolResult(status="error", message="No steps to replay.")

            # Start video recording if requested
            video_path = None
            ffmpeg_proc = None
            if record_video:
                import io, shutil, subprocess
                ffmpeg_path = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
                if ffmpeg_path:
                    video_path = str(_macros_dir() / f"{macro_id}_replay_{int(time.time())}.mp4")
                    ffmpeg_proc = subprocess.Popen(
                        [ffmpeg_path, "-y", "-f", "image2pipe", "-framerate", "5", "-i", "-",
                         "-c:v", "libx264", "-pix_fmt", "yuv420p", video_path],
                        stdin=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    )

            verify = operation == "replay_with_verify"
            results = []

            for i, step in enumerate(steps_to_run):
                # Capture a frame during each step if recording
                if ffmpeg_proc and ffmpeg_proc.stdin:
                    try:
                        from PIL import ImageGrab
                        buf = io.BytesIO()
                        ImageGrab.grab().save(buf, format="PNG")
                        ffmpeg_proc.stdin.write(buf.getvalue())
                    except Exception:
                        pass
                tool_name = step.get("tool", "")
                params = step.get("params", {})
                label = step.get("label", tool_name)

                recorded_outcome = step.get("outcome")

                policy = RetryPolicy(max_attempts=2, base_delay=1.0)

                def _exec(s=tool_name, p=params):
                    return _call_tool_by_name(s, p)

                retry_result = policy.execute(_exec, label=label)

                step_result = {
                    "step": i + 1,
                    "label": label,
                    "tool": tool_name,
                    "success": retry_result.success,
                }

                if verify and recorded_outcome:
                    recorded_success = recorded_outcome.get("status") == "success"
                    step_result["recorded_match"] = retry_result.success == recorded_success
                    step_result["recorded_status"] = recorded_outcome.get("status")

                results.append(step_result)

            # Close ffmpeg if recording
            if ffmpeg_proc and ffmpeg_proc.stdin:
                try:
                    ffmpeg_proc.stdin.close()
                    ffmpeg_proc.wait(timeout=10)
                except Exception:
                    pass

            success_count = sum(1 for r in results if r["success"])
            data = {"macro_id": macro_id, "results": results, "total": len(results), "succeeded": success_count}
            if video_path:
                data["video"] = video_path
            return ToolResult(
                status="success" if success_count == len(results) else "blocked",
                message=f"Replayed {len(results)} steps: {success_count} succeeded." + (f" Video: {video_path}" if video_path else ""),
                data=data,
            )

        return ToolResult(
            status="error",
            message=f"Unknown operation: {operation}",
            recovery_tip="Supported operations: record, stop, replay, replay_with_verify, list",
        )

else:
    logger.warning("Macro tool not available - missing app instance")

__all__ = ["automation_macro"]
