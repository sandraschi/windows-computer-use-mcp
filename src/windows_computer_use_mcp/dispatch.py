"""Dispatch mode for UI mutations (Cua-style foreground vs background)."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal

logger = logging.getLogger(__name__)

ENV_DISPATCH = "windows_computer_use_mcp_DISPATCH"

DispatchMode = Literal["foreground", "background"]
BACKGROUND_UNAVAILABLE = "background_unavailable"


def default_dispatch_mode() -> DispatchMode:
    val = (os.getenv(ENV_DISPATCH) or "foreground").strip().lower()
    if val == "background":
        return "background"
    return "foreground"


def should_avoid_foreground_reads() -> bool:
    """When True, capture/screenshot paths must not call SetForegroundWindow."""
    return default_dispatch_mode() == "background"


def resolve_dispatch(explicit: str | None) -> DispatchMode:
    if explicit is None:
        return default_dispatch_mode()
    val = explicit.strip().lower()
    if val == "background":
        return "background"
    return "foreground"


def background_unavailable_result(reason: str, *, attempted: list[str] | None = None) -> dict[str, Any]:
    return {
        "code": BACKGROUND_UNAVAILABLE,
        "background_unavailable": True,
        "reason": reason,
        "attempted": attempted or [],
        "dispatch": "background",
    }


def click_element(
    element: Any,
    *,
    dispatch: DispatchMode,
    button: str = "left",
    double: bool = False,
    window_handle: int | None = None,
) -> dict[str, Any]:
    """Click a PyWinAuto wrapper with background-first attempt when requested."""
    attempted: list[str] = []
    if dispatch == "background":
        try:
            if hasattr(element, "invoke"):
                attempted.append("invoke")
                element.invoke()
                return {"method": "invoke", "dispatch": "background", "code": "ok"}
        except Exception as exc:
            logger.info("invoke failed: %s", exc)
        try:
            attempted.append("click_input")
            element.click_input(button=button)
            return {"method": "click_input", "dispatch": "background", "code": "ok"}
        except Exception as exc:
            logger.info("click_input failed: %s", exc)
        if window_handle is not None:
            try:
                from windows_computer_use_mcp.agent_overlay import show_agent_cursor
                from windows_computer_use_mcp.win32_window import postmessage_click_at

                rect = element.rectangle()
                cx = rect.left + rect.width() // 2
                cy = rect.top + rect.height() // 2
                attempted.append("postmessage")
                meta = postmessage_click_at(window_handle, cx, cy, button=button, double=double)
                show_agent_cursor(cx, cy)
                return {**meta, "code": "ok"}
            except Exception as exc:
                logger.info("postmessage failed: %s", exc)
        return background_unavailable_result(
            "UIA invoke/click_input and PostMessage did not succeed",
            attempted=attempted,
        )

    if double:
        element.double_click(button=button)
        return {"method": "double_click", "dispatch": "foreground", "code": "ok"}
    element.click(button=button)
    return {"method": "click", "dispatch": "foreground", "code": "ok"}
