"""Win32 window geometry and background-safe capture helpers."""

from __future__ import annotations

import logging
import sys
from typing import Any

logger = logging.getLogger(__name__)

WIN32_AVAILABLE = sys.platform == "win32"

try:
    if WIN32_AVAILABLE:
        import win32api
        import win32con
        import win32gui
    else:
        win32api = win32con = win32gui = None  # type: ignore[assignment]
except ImportError:
    win32api = win32con = win32gui = None  # type: ignore[assignment]
    WIN32_AVAILABLE = False


def _require_win32() -> None:
    if not WIN32_AVAILABLE or win32gui is None:
        raise RuntimeError("win32_window requires Windows and pywin32")


def get_window_bbox(window_handle: int) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) for an HWND."""
    _require_win32()
    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
    return int(left), int(top), int(right), int(bottom)


def virtual_screen_bounds() -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of the entire virtual screen.

    Spans all monitors — unlike GetSystemMetrics(SM_CXSCREEN) which
    only returns the primary monitor.
    """
    _require_win32()
    vs_left = win32api.GetSystemMetrics(76)   # SM_XVIRTUALSCREEN
    vs_top = win32api.GetSystemMetrics(77)    # SM_YVIRTUALSCREEN
    vs_width = win32api.GetSystemMetrics(78)  # SM_CXVIRTUALSCREEN
    vs_height = win32api.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
    return vs_left, vs_top, vs_left + vs_width, vs_top + vs_height


def clamp_bbox(
    bbox: tuple[int, int, int, int],
    vs: tuple[int, int, int, int] | None = None,
) -> tuple[int, int, int, int]:
    """Clamp (left, top, right, bottom) so it stays within virtual screen."""
    if vs is None:
        vs = virtual_screen_bounds()
    left, top, right, bottom = bbox
    vs_left, vs_top, vs_right, vs_bottom = vs
    return (
        max(left, vs_left),
        max(top, vs_top),
        min(right, vs_right),
        min(bottom, vs_bottom),
    )


def grab_window_image(window_handle: int | None, *, avoid_foreground: bool = True):
    """Capture window or full screen without activating the window when avoid_foreground."""
    from PIL import ImageGrab

    if window_handle is None:
        return ImageGrab.grab()
    try:
        left, top, right, bottom = get_window_bbox(window_handle)
        if right <= left or bottom <= top:
            raise ValueError("invalid window rectangle")
        if not avoid_foreground:
            try:
                win32gui.SetForegroundWindow(window_handle)
            except Exception as exc:
                logger.debug("SetForegroundWindow skipped: %s", exc)
        left, top, right, bottom = clamp_bbox((left, top, right, bottom))
        return ImageGrab.grab(bbox=(left, top, right, bottom))
    except Exception as exc:
        logger.warning("Window grab failed (%s); falling back to full screen", exc)
        return ImageGrab.grab()


def postmessage_click_at(
    window_handle: int,
    screen_x: int,
    screen_y: int,
    *,
    button: str = "left",
    double: bool = False,
) -> dict[str, Any]:
    """Post mouse messages to HWND (background-oriented; may not reach all controls)."""
    _require_win32()
    cx, cy = win32gui.ScreenToClient(window_handle, (int(screen_x), int(screen_y)))
    lparam = win32api.MAKELONG(cx & 0xFFFF, cy & 0xFFFF)
    if button == "right":
        down, up = win32con.WM_RBUTTONDOWN, win32con.WM_RBUTTONUP
    elif button == "middle":
        down, up = win32con.WM_MBUTTONDOWN, win32con.WM_MBUTTONUP
    else:
        down, up = win32con.WM_LBUTTONDOWN, win32con.WM_LBUTTONUP
    win32gui.PostMessage(window_handle, down, 0, lparam)
    win32gui.PostMessage(window_handle, up, 0, lparam)
    if double:
        win32gui.PostMessage(window_handle, down, 0, lparam)
        win32gui.PostMessage(window_handle, up, 0, lparam)
    return {"method": "postmessage", "dispatch": "background", "x": screen_x, "y": screen_y}
