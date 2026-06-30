"""Closed-loop task runner — observe, act, verify, recover."""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from windows_computer_use_mcp.app_profiles import get_profile
from windows_computer_use_mcp.retry import retry_attempts

logger = logging.getLogger(__name__)

OnFail = Literal["retry", "refocus_retry", "abort"]
StepKind = Literal[
    "shortcut",
    "dialog",
    "focus",
    "wait_stable",
    "assert_file",
    "assert_template",
    "screenshot",
    "sleep",
    "click",
    "preflight",
]

_TASKS: dict[str, TaskSession] = {}

_MUTATING_KINDS = frozenset({"shortcut", "dialog", "click"})


@dataclass
class TaskSession:
    task_id: str
    app: str
    steps: list[dict[str, Any]]
    status: str = "pending"
    current_step: int = 0
    window_handle: int | None = None
    evidence: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "app": self.app,
            "status": self.status,
            "current_step": self.current_step,
            "window_handle": self.window_handle,
            "evidence": self.evidence,
            "error": self.error,
            "steps_total": len(self.steps),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def assert_outcome(kind: str, **params: Any) -> dict[str, Any]:
    """Task-level outcome verification (not pixel diff)."""
    if kind == "file_exists":
        path = Path(params["path"])
        exists = path.is_file()
        return {"kind": kind, "path": str(path), "exists": exists, "passed": exists}

    if kind == "file_min_kb":
        path = Path(params["path"])
        min_kb = float(params.get("min_kb", 1))
        if not path.is_file():
            return {"kind": kind, "path": str(path), "passed": False, "size_kb": 0}
        size_kb = path.stat().st_size / 1024
        passed = size_kb >= min_kb
        return {"kind": kind, "path": str(path), "size_kb": round(size_kb, 2), "passed": passed}

    raise ValueError(f"Unknown outcome kind: {kind}")


def _capture_screenshot(hwnd: int | None, label: str, output_dir: str | None) -> str | None:
    if not output_dir:
        return None
    try:
        from windows_computer_use_mcp import assert_engine

        out = Path(output_dir) / f"task_{label}_{int(time.time() * 1000)}.png"
        img = assert_engine.capture_image(window_handle=hwnd)
        img.save(out)
        return str(out)
    except Exception as exc:
        logger.debug("task screenshot failed: %s", exc)
        return None


def _resolve_hwnd(session: TaskSession, step: dict[str, Any]) -> int | None:
    if step.get("window_handle"):
        return int(step["window_handle"])
    if session.window_handle:
        return session.window_handle
    title = step.get("window_title")
    profile = get_profile(session.app)
    if not title and profile:
        title = profile.window_title
    if not title:
        return None
    try:
        import pygetwindow as gw

        wins = [w for w in gw.getAllWindows() if title.lower() in (w.title or "").lower()]
        if wins:
            return int(wins[0]._hWnd)
    except Exception as exc:
        logger.debug("hwnd resolve failed: %s", exc)
    return None


def _refocus(hwnd: int | None) -> None:
    if hwnd:
        from windows_computer_use_mcp.win32_keyboard import focus_window

        focus_window(hwnd)


def _invalidate_snapshots_after_mutation(hwnd: int | None) -> dict[str, Any]:
    """Drop stale element snapshots after UI mutation (T2.2)."""
    if not hwnd:
        return {"invalidated": 0, "reason": "no_hwnd"}
    try:
        from windows_computer_use_mcp import assert_engine
        from windows_computer_use_mcp.snapshot_store import get_snapshot_store

        img = assert_engine.capture_image(window_handle=hwnd)
        ui_hash = assert_engine.image_hash(img)
        count = get_snapshot_store().invalidate_for_handle(hwnd, ui_hash)
        return {"invalidated": count, "ui_hash": ui_hash}
    except Exception as exc:
        logger.debug("snapshot invalidation failed: %s", exc)
        try:
            from windows_computer_use_mcp.snapshot_store import get_snapshot_store

            count = get_snapshot_store().invalidate_for_handle(hwnd)
            return {"invalidated": count, "fallback": True}
        except Exception:
            return {"invalidated": 0, "error": str(exc)}


def _step_region(session: TaskSession, step: dict[str, Any]) -> tuple[int, int, int, int] | None:
    """Resolve crop region from step fields or app profile (T2.4)."""
    from windows_computer_use_mcp import assert_engine
    from windows_computer_use_mcp.app_profiles import get_profile

    explicit = assert_engine._region_tuple(
        step.get("region_left"),
        step.get("region_top"),
        step.get("region_right"),
        step.get("region_bottom"),
    )
    if explicit:
        return explicit

    hint = step.get("region_hint")
    profile = get_profile(session.app)
    if not profile or not profile.stable_region:
        return None

    if hint in (None, "editor_canvas", profile.stable_region.label):
        return profile.stable_region.as_tuple()
    if hint == "full_window":
        return None
    return profile.stable_region.as_tuple()


def _execute_step(session: TaskSession, step: dict[str, Any], hwnd: int | None) -> dict[str, Any]:
    kind = step.get("kind", "shortcut")
    result: dict[str, Any] = {"kind": kind}

    if kind == "focus":
        _refocus(hwnd)
        result["focused"] = hwnd
        return result

    if kind == "sleep":
        secs = float(step.get("seconds", 1.0))
        time.sleep(secs)
        result["slept"] = secs
        return result

    if kind == "shortcut":
        from windows_computer_use_mcp import shortcut_engine

        app = step.get("app") or session.app
        action = step["action"]
        data = shortcut_engine.send_shortcut(
            app,
            action,
            window_handle=hwnd,
            verify_stable=step.get("verify_stable"),
            pause=float(step.get("pause", 0.05)),
        )
        result.update(data)
        return result

    if kind == "dialog":
        from windows_computer_use_mcp import dialog_engine

        path = step["path"]
        data = dialog_engine.submit_path(
            path,
            use_clipboard=step.get("use_clipboard", True),
            post_confirm_pause_s=float(step.get("post_confirm_pause_s", 0.0)),
        )
        result.update(data)
        return result

    if kind == "wait_stable":
        from windows_computer_use_mcp import assert_engine

        region = _step_region(session, step)
        stable = assert_engine.wait_stable(
            window_handle=hwnd,
            region=region,
            timeout_s=float(step.get("timeout_s", 10.0)),
            stable_frames_required=int(step.get("stable_frames_required", 2)),
            hash_algorithm=str(step.get("hash_algorithm", "dhash")),
            output_dir=step.get("output_dir"),
        )
        result["stable"] = stable
        if not stable.get("stable"):
            raise TimeoutError(f"wait_stable failed: {stable}")
        return result

    if kind == "assert_template":
        from windows_computer_use_mcp import assert_engine, template_library

        template_id = step["template_id"]
        version = step.get("version")
        template_path = str(template_library.resolve_template(session.app, template_id, version=version))
        region = _step_region(session, step)
        haystack = assert_engine.capture_image(window_handle=hwnd, region=region)
        entries = {e.template_id: e for e in template_library.list_template_entries(session.app)}
        entry = entries.get(template_id)
        threshold = float(step.get("match_threshold", entry.match_threshold if entry else 0.8))
        match = assert_engine.assert_template_match(
            haystack,
            template_path,
            match_threshold=threshold,
            region=None,
        )
        result["template"] = match
        if not match.get("found"):
            raise RuntimeError(f"assert_template failed: {template_id} {match}")
        return result

    if kind == "assert_file":
        check = step.get("check", "file_exists")
        if check == "file_min_kb":
            outcome = assert_outcome("file_min_kb", path=step["path"], min_kb=step.get("min_kb", 1))
        else:
            outcome = assert_outcome("file_exists", path=step["path"])
        result["outcome"] = outcome
        if not outcome.get("passed"):
            raise RuntimeError(f"assert_file failed: {outcome}")
        return result

    if kind == "screenshot":
        shot = _capture_screenshot(hwnd, step.get("name", "capture"), step.get("output_dir"))
        result["screenshot_path"] = shot
        return result

    if kind == "click":
        from windows_computer_use_mcp.win32_mouse import click

        x = int(step["x"])
        y = int(step["y"])
        button = step.get("button", "left")
        click(x, y, button=button)
        result["clicked"] = {"x": x, "y": y, "button": button}
        return result

    if kind == "preflight":
        from windows_computer_use_mcp.sysadmin_preflight import run_sync_preflight

        pf = run_sync_preflight(
            output_dir=step.get("output_dir"),
            min_memory_mb=float(step.get("min_memory_mb", 2048)),
            min_disk_mb=float(step.get("min_disk_mb", 500)),
            filter_process=step.get("filter_process"),
            sysadmin_url=step.get("sysadmin_url"),
        )
        result["preflight"] = pf
        if not pf.get("ok"):
            raise RuntimeError(pf.get("error") or "preflight failed")
        return result

    raise ValueError(f"Unknown step kind: {kind}")


def run_task(
    *,
    app: str,
    steps: list[dict[str, Any]],
    task_id: str | None = None,
    window_handle: int | None = None,
    output_dir: str | None = None,
) -> TaskSession:
    """Run a step list with retry/recovery and evidence collection."""
    tid = task_id or str(uuid.uuid4())[:12]
    session = TaskSession(task_id=tid, app=app, steps=steps, window_handle=window_handle)
    _TASKS[tid] = session
    session.status = "running"

    for idx, step in enumerate(steps):
        session.current_step = idx
        on_fail: OnFail = step.get("on_fail", "refocus_retry")
        hwnd = _resolve_hwnd(session, step)
        if hwnd and not session.window_handle:
            session.window_handle = hwnd

        before_shot = _capture_screenshot(hwnd, f"s{idx}_before", output_dir or step.get("output_dir"))
        step_evidence: dict[str, Any] = {
            "step_index": idx,
            "kind": step.get("kind"),
            "before_screenshot": before_shot,
            "attempts": [],
        }

        last_exc: Exception | None = None
        for attempt in range(retry_attempts()):
            try:
                act_result = _execute_step(session, step, hwnd)
                after_shot = _capture_screenshot(hwnd, f"s{idx}_after", output_dir or step.get("output_dir"))
                step_evidence["attempts"].append({"attempt": attempt + 1, "success": True, "result": act_result})
                step_evidence["after_screenshot"] = after_shot
                step_evidence["status"] = "success"
                if step.get("kind") in _MUTATING_KINDS:
                    inv = _invalidate_snapshots_after_mutation(hwnd)
                    step_evidence["snapshot_invalidation"] = inv
                session.evidence.append(step_evidence)
                last_exc = None
                break
            except Exception as exc:
                last_exc = exc
                step_evidence["attempts"].append({"attempt": attempt + 1, "success": False, "error": str(exc)})
                if on_fail == "abort" or attempt >= retry_attempts() - 1:
                    break
                if on_fail == "refocus_retry":
                    _refocus(hwnd)
                time.sleep(0.5 * (attempt + 1))

        if last_exc is not None:
            if step.get("optional"):
                step_evidence["status"] = "skipped_optional"
                step_evidence["error"] = str(last_exc)
                session.evidence.append(step_evidence)
                last_exc = None
            else:
                step_evidence["status"] = "failed"
                step_evidence["error"] = str(last_exc)
                session.evidence.append(step_evidence)
                session.status = "failed"
                session.error = f"Step {idx} ({step.get('kind')}): {last_exc}"
                session.finished_at = time.time()
                return session

    session.status = "complete"
    session.finished_at = time.time()
    return session


def get_task(task_id: str) -> TaskSession | None:
    return _TASKS.get(task_id)


def cancel_task(task_id: str) -> bool:
    session = _TASKS.get(task_id)
    if not session:
        return False
    session.status = "cancelled"
    session.finished_at = time.time()
    return True
