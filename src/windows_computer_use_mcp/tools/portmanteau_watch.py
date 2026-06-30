"""Persistent watcher for event-driven automation triggers.

PORTMANTEAU PATTERN RATIONALE:
Consolidates window/text/element watchers into one tool. Watchers run as
background threads and fire callbacks when conditions are met.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.tools.models import ToolResult

logger = logging.getLogger(__name__)

_WATCHERS: dict[str, dict[str, Any]] = {}
_WATCHER_LOCK = threading.Lock()


def _watcher_thread(
    watcher_id: str, condition: str, target: str, interval: float, timeout: float, window_handle: int | None
):
    """Background thread that polls for a condition and stops when met."""
    from pywinauto import Desktop

    start = time.time()
    desktop = Desktop(backend="uia")

    while time.time() - start < timeout:
        with _WATCHER_LOCK:
            state = _WATCHERS.get(watcher_id)
            if state is None or state.get("status") == "stopped":
                return

        try:
            met = False
            detail = None

            if condition == "window_appears":
                for win in desktop.windows():
                    try:
                        if target.lower() in win.window_text().lower():
                            met = True
                            detail = {"title": win.window_text(), "handle": win.handle}
                            break
                    except Exception:
                        continue

            elif condition == "window_closes":
                if window_handle is not None:
                    try:
                        win = desktop.window(handle=window_handle)
                        met = not win.exists(timeout=0.5)
                        detail = {"handle": window_handle, "closed": met}
                    except Exception:
                        met = True
                        detail = {"handle": window_handle, "closed": True}
                else:
                    found = False
                    for win in desktop.windows():
                        try:
                            if target.lower() in win.window_text().lower():
                                found = True
                                break
                        except Exception:
                            continue
                    met = not found
                    detail = {"title": target, "closed": met}

            elif condition == "text_appears":
                if window_handle is not None:
                    try:
                        win = desktop.window(handle=window_handle)
                        if win.exists(timeout=0.5):
                            full = win.window_text()
                            met = target.lower() in full.lower()
                            detail = {"found": target if met else None}
                    except Exception:
                        pass
                else:
                    for win in desktop.windows():
                        try:
                            if target.lower() in win.window_text().lower():
                                met = True
                                detail = {"title": win.window_text(), "handle": win.handle}
                                break
                        except Exception:
                            continue

            elif condition == "element_appears":
                if window_handle is not None:
                    try:
                        win = desktop.window(handle=window_handle)
                        children = win.children(visible_only=True)
                        for child in children:
                            try:
                                if target.lower() in child.window_text().lower():
                                    met = True
                                    detail = {"title": child.window_text(), "handle": child.handle}
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass

            if met:
                with _WATCHER_LOCK:
                    if watcher_id in _WATCHERS:
                        _WATCHERS[watcher_id].update({"status": "triggered", "detail": detail, "ended": time.time()})
                return

        except Exception as e:
            logger.debug("Watcher %s poll error: %s", watcher_id, e)

        time.sleep(interval)

    with _WATCHER_LOCK:
        if watcher_id in _WATCHERS:
            _WATCHERS[watcher_id].update({"status": "timeout", "ended": time.time()})


if app is not None:

    @app.tool(
        name="automation_watch",
        description="""Persistent watcher for event-driven automation triggers.

OPERATIONS:
- start: Begin monitoring for a condition. Runs in a background thread.
  Conditions: window_appears, window_closes, text_appears, element_appears.
  Returns a watcher_id for status/cancel.
- status: Check whether a watcher has triggered.
- stop: Cancel a running watcher.
- list: List all active watchers.
""",
    )
    async def automation_watch(
        operation: str,
        condition: str | None = None,
        target: str | None = None,
        window_handle: int | None = None,
        interval: float = 2.0,
        timeout: float = 120.0,
        watcher_id: str | None = None,
    ) -> ToolResult:
        if operation == "start":
            if not condition or not target:
                return ToolResult(status="error", message="condition and target are required.")
            wid = watcher_id or f"watch_{uuid.uuid4().hex[:8]}"
            with _WATCHER_LOCK:
                _WATCHERS[wid] = {
                    "status": "running",
                    "condition": condition,
                    "target": target,
                    "started": time.time(),
                    "interval": interval,
                    "timeout": timeout,
                }
            t = threading.Thread(
                target=_watcher_thread, args=(wid, condition, target, interval, timeout, window_handle), daemon=True
            )
            t.start()
            return ToolResult(
                status="success",
                message=f"Watcher '{wid}' started: {condition} = '{target}' (timeout={timeout}s).",
                data={"watcher_id": wid, "condition": condition, "target": target},
            )

        if operation == "status":
            if not watcher_id:
                return ToolResult(status="error", message="watcher_id is required.")
            with _WATCHER_LOCK:
                state = _WATCHERS.get(watcher_id)
            if state is None:
                return ToolResult(status="error", message=f"No watcher '{watcher_id}'.")
            elapsed = time.time() - state.get("started", time.time())
            return ToolResult(
                status="success" if state.get("status") == "triggered" else "blocked",
                message=f"Watcher '{watcher_id}' status: {state['status']} ({elapsed:.0f}s elapsed).",
                data=state,
            )

        if operation == "stop":
            if not watcher_id:
                return ToolResult(status="error", message="watcher_id is required.")
            with _WATCHER_LOCK:
                if watcher_id in _WATCHERS:
                    _WATCHERS[watcher_id]["status"] = "stopped"
            return ToolResult(status="success", message=f"Watcher '{watcher_id}' stopped.")

        if operation == "list":
            with _WATCHER_LOCK:
                active = {
                    k: {
                        "status": v["status"],
                        "condition": v["condition"],
                        "target": v["target"],
                        "started": v.get("started"),
                    }
                    for k, v in _WATCHERS.items()
                }
            return ToolResult(
                status="success",
                message=f"{len(active)} watchers.",
                data={"watchers": active},
            )

        return ToolResult(status="error", message=f"Unknown operation: {operation}")

else:
    logger.warning("Watch tool not available - missing app instance")

__all__ = ["automation_watch"]
