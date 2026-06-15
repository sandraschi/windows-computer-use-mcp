"""Windows mouse injection via Win32 APIs (not PyAutoGUI).

PyAutoGUI uses the same underlying calls but often misbehaves under per-monitor DPI
scaling and zero-duration moves. This module calls ``SetCursorPos`` and
``mouse_event`` directly after ``SetProcessDpiAwareness``, so move / click / drag
match physical screen coordinates reliably.

Imported only on Windows at runtime; on other OSes ``WIN32_MOUSE_AVAILABLE`` is False.
"""

from __future__ import annotations

import ctypes
import logging
import os
import sys
import time
from typing import Literal

logger = logging.getLogger(__name__)

ButtonName = Literal["left", "right", "middle"]

WIN32_MOUSE_AVAILABLE = sys.platform == "win32"

try:
    if WIN32_MOUSE_AVAILABLE:
        import win32api
        import win32con
    else:
        win32api = None  # type: ignore[assignment]
        win32con = None  # type: ignore[assignment]
except ImportError:
    win32api = None  # type: ignore[assignment]
    win32con = None  # type: ignore[assignment]
    WIN32_MOUSE_AVAILABLE = False


class MouseFailSafeError(Exception):
    """Cursor reached a failsafe corner (same idea as PyAutoGUI)."""


_FAILSAFE_MARGIN = 10


def ensure_dpi_awareness() -> None:
    """Prefer per-monitor DPI awareness so coords match ``SetCursorPos``."""
    if not WIN32_MOUSE_AVAILABLE or win32api is None:
        return
    user32 = ctypes.windll.user32
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception as e:
            logger.debug("DPI awareness not set: %s", e)


ensure_dpi_awareness()


def failsafe_enabled() -> bool:
    """Match ``windows_computer_use_mcp_BYPASS_HITL`` disabling PyAutoGUI failsafe in ``app``."""
    return os.getenv("windows_computer_use_mcp_BYPASS_HITL") not in ("1", "true", "yes", "on")


def _require_win32() -> None:
    if not WIN32_MOUSE_AVAILABLE or win32api is None or win32con is None:
        raise RuntimeError("win32_mouse requires Windows and pywin32")


def screen_size() -> tuple[int, int]:
    _require_win32()
    return int(win32api.GetSystemMetrics(0)), int(win32api.GetSystemMetrics(1))


def get_cursor_pos() -> tuple[int, int]:
    _require_win32()
    p = win32api.GetCursorPos()
    return int(p[0]), int(p[1])


def _check_failsafe_if_enabled(enabled: bool) -> None:
    """Match PyAutoGUI: only the upper-left corner zone aborts automation."""
    if not enabled:
        return
    x, y = get_cursor_pos()
    if x <= _FAILSAFE_MARGIN and y <= _FAILSAFE_MARGIN:
        raise MouseFailSafeError("Failsafe: cursor in upper-left corner")


def set_cursor_pos(x: int, y: int, *, failsafe: bool | None = None) -> None:
    _require_win32()
    if failsafe is None:
        failsafe = failsafe_enabled()
    _check_failsafe_if_enabled(failsafe)
    win32api.SetCursorPos((int(x), int(y)))


def move_to(x: int, y: int, duration: float = 0.0, *, failsafe: bool | None = None) -> None:
    """Move to screen coordinates. Interpolates when ``duration`` > 0."""
    _require_win32()
    if failsafe is None:
        failsafe = failsafe_enabled()
    _check_failsafe_if_enabled(failsafe)
    x, y = int(x), int(y)
    if duration <= 0:
        win32api.SetCursorPos((x, y))
        return
    sx, sy = get_cursor_pos()
    steps = max(1, int(min(200, duration * 120)))
    for i in range(1, steps + 1):
        t = i / steps
        nx = int(sx + (x - sx) * t)
        ny = int(sy + (y - sy) * t)
        win32api.SetCursorPos((nx, ny))
        time.sleep(duration / steps)


def move_rel(dx: int, dy: int, duration: float = 0.0, *, failsafe: bool | None = None) -> None:
    if failsafe is None:
        failsafe = failsafe_enabled()
    sx, sy = get_cursor_pos()
    move_to(sx + int(dx), sy + int(dy), duration=duration, failsafe=failsafe)


def _down_up(button: ButtonName, up: bool) -> None:
    _require_win32()
    if button == "left":
        flag = win32con.MOUSEEVENTF_LEFTUP if up else win32con.MOUSEEVENTF_LEFTDOWN
    elif button == "right":
        flag = win32con.MOUSEEVENTF_RIGHTUP if up else win32con.MOUSEEVENTF_RIGHTDOWN
    else:
        flag = win32con.MOUSEEVENTF_MIDDLEUP if up else win32con.MOUSEEVENTF_MIDDLEDOWN
    win32api.mouse_event(flag, 0, 0, 0, 0)


def click(
    x: int | None = None,
    y: int | None = None,
    *,
    button: ButtonName = "left",
    clicks: int = 1,
    interval: float = 0.05,
    failsafe: bool | None = None,
) -> None:
    if failsafe is None:
        failsafe = failsafe_enabled()
    if x is not None and y is not None:
        move_to(int(x), int(y), duration=0, failsafe=failsafe)
    _check_failsafe_if_enabled(failsafe)
    clicks = max(1, int(clicks))
    for i in range(clicks):
        _down_up(button, False)
        _down_up(button, True)
        if i < clicks - 1:
            time.sleep(interval)


def double_click(
    x: int | None = None,
    y: int | None = None,
    *,
    button: ButtonName = "left",
    failsafe: bool | None = None,
) -> None:
    if failsafe is None:
        failsafe = failsafe_enabled()
    if x is not None and y is not None:
        move_to(int(x), int(y), duration=0, failsafe=failsafe)
    _check_failsafe_if_enabled(failsafe)
    _require_win32()
    dbl_ms = win32api.GetDoubleClickTime()
    interval = max(0.01, (dbl_ms / 1000.0) * 0.5)
    click(None, None, button=button, clicks=2, interval=interval, failsafe=failsafe)


def right_click(x: int | None = None, y: int | None = None, *, failsafe: bool | None = None) -> None:
    click(x, y, button="right", clicks=1, failsafe=failsafe)


def drag(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    *,
    duration: float = 0.5,
    button: ButtonName = "left",
    failsafe: bool | None = None,
) -> None:
    if failsafe is None:
        failsafe = failsafe_enabled()
    move_to(x1, y1, duration=0, failsafe=failsafe)
    _check_failsafe_if_enabled(failsafe)
    _down_up(button, False)
    try:
        if duration <= 0:
            win32api.SetCursorPos((int(x2), int(y2)))
        else:
            steps = max(1, int(min(300, duration * 150)))
            for i in range(1, steps + 1):
                t = i / steps
                nx = int(x1 + (x2 - x1) * t)
                ny = int(y1 + (y2 - y1) * t)
                win32api.SetCursorPos((nx, ny))
                time.sleep(duration / steps)
    finally:
        _down_up(button, True)


def scroll(amount: int, *, horizontal: bool = False, failsafe: bool | None = None) -> None:
    _require_win32()
    if failsafe is None:
        failsafe = failsafe_enabled()
    _check_failsafe_if_enabled(failsafe)
    # One notch ~= 120; pyautogui uses "clicks" similarly
    delta = int(amount) * 120
    if horizontal:
        # Positive = scroll right (same sign convention as common pyautogui hscroll on Windows)
        flag = win32con.MOUSEEVENTF_HWHEEL
    else:
        flag = win32con.MOUSEEVENTF_WHEEL
    win32api.mouse_event(flag, 0, 0, delta, 0)


def scroll_at(x: int, y: int, amount: int, *, horizontal: bool = False, failsafe: bool | None = None) -> None:
    move_to(x, y, duration=0, failsafe=failsafe)
    scroll(amount, horizontal=horizontal, failsafe=failsafe)


__all__ = [
    "WIN32_MOUSE_AVAILABLE",
    "ButtonName",
    "MouseFailSafeError",
    "click",
    "double_click",
    "drag",
    "ensure_dpi_awareness",
    "failsafe_enabled",
    "get_cursor_pos",
    "move_rel",
    "move_to",
    "right_click",
    "screen_size",
    "scroll",
    "scroll_at",
    "set_cursor_pos",
]
