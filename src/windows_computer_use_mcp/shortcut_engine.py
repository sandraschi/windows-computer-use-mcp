"""Semantic shortcut execution with optional post-send stability check."""

from __future__ import annotations

import logging
from typing import Any

from windows_computer_use_mcp.app_shortcuts.registry import get_shortcut, list_shortcuts
from windows_computer_use_mcp.keyboard_send import is_modifier_combo, parse_hotkey, send_hotkey, send_press
from windows_computer_use_mcp.retry import with_retry

logger = logging.getLogger(__name__)


def _send_keys(keys: str, *, hwnd: int | None = None, pause: float = 0.0) -> dict[str, Any]:
    parts = parse_hotkey(keys)
    if len(parts) == 1 and not is_modifier_combo(parts):
        return send_press(parts[0], hwnd=hwnd, pause=pause)
    return send_hotkey(parts, hwnd=hwnd, pause=pause)


def _wait_stable_after(hwnd: int | None, timeout_s: float) -> dict[str, Any] | None:
    if not hwnd:
        return None
    from windows_computer_use_mcp import assert_engine

    return assert_engine.wait_stable(
        window_handle=hwnd,
        timeout_s=timeout_s,
        stable_frames_required=2,
        poll_interval_s=0.4,
    )


def send_shortcut(
    app: str,
    action: str,
    *,
    window_handle: int | None = None,
    verify_stable: bool | None = None,
    pause: float = 0.05,
) -> dict[str, Any]:
    """Resolve semantic action and send keys, optionally wait for UI stable."""

    def _execute() -> dict[str, Any]:
        spec = get_shortcut(app, action)
        send_meta = _send_keys(spec.keys, hwnd=window_handle, pause=pause)
        stable_result = None
        do_wait = verify_stable if verify_stable is not None else spec.wait_stable
        if do_wait and window_handle:
            stable_result = _wait_stable_after(window_handle, spec.stable_timeout_s)
            if stable_result and not stable_result.get("stable"):
                raise TimeoutError(f"UI unstable after shortcut '{action}' within {spec.stable_timeout_s}s")

        return {
            "app": app,
            "action": action,
            "keys": spec.keys,
            "description": spec.description,
            "category": spec.category,
            "send": send_meta,
            "stable": stable_result,
        }

    return with_retry(_execute, label=f"shortcut:{app}:{action}")


def describe_shortcut(app: str, action: str) -> dict[str, Any]:
    spec = get_shortcut(app, action)
    return {
        "app": app,
        "action": action,
        "keys": spec.keys,
        "description": spec.description,
        "wait_stable": spec.wait_stable,
        "stable_timeout_s": spec.stable_timeout_s,
        "category": spec.category,
    }


def list_app_shortcuts(app: str) -> list[dict[str, Any]]:
    return [
        {
            "action": name,
            "keys": spec.keys,
            "description": spec.description,
            "category": spec.category,
            "wait_stable": spec.wait_stable,
        }
        for name, spec in sorted(list_shortcuts(app).items())
    ]
