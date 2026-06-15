"""Win32 keyboard input — focus target HWND before SendInput."""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Sequence

logger = logging.getLogger(__name__)

WIN32_KB_AVAILABLE = sys.platform == "win32"

try:
    if WIN32_KB_AVAILABLE:
        import win32gui
    else:
        win32gui = None  # type: ignore[assignment]
except ImportError:
    win32gui = None
    WIN32_KB_AVAILABLE = False


def focus_window(hwnd: int | None) -> bool:
    if hwnd is None or win32gui is None:
        return False
    try:
        win32gui.SetForegroundWindow(int(hwnd))
        time.sleep(0.05)
        return True
    except Exception as exc:
        logger.debug("SetForegroundWindow failed: %s", exc)
        return False


def send_hotkey(keys: Sequence[str], *, hwnd: int | None = None, pause: float = 0.0) -> dict:
    """Send hotkey via pyautogui after optional HWND focus (win32 path)."""
    import pyautogui

    focused = focus_window(hwnd)
    pyautogui.hotkey(*[k.lower() for k in keys])
    if pause > 0:
        time.sleep(pause)
    return {"method": "win32_focus_pyautogui", "keys": list(keys), "hwnd_focused": focused}


def send_press(key: str, *, hwnd: int | None = None, presses: int = 1, pause: float = 0.0) -> dict:
    import pyautogui

    focused = focus_window(hwnd)
    for _ in range(presses):
        pyautogui.press(key.lower())
        if pause > 0:
            time.sleep(pause)
    return {"method": "win32_focus_pyautogui", "key": key, "hwnd_focused": focused}
