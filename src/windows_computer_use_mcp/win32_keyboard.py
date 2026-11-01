"""Win32 keyboard input - focus target HWND before SendInput, or PostMessage for background."""

from __future__ import annotations

import logging
import sys
import time
from collections.abc import Sequence
from typing import Any

logger = logging.getLogger(__name__)

WIN32_KB_AVAILABLE = sys.platform == "win32"

try:
    if WIN32_KB_AVAILABLE:
        import win32con
        import win32gui
    else:
        win32con = None  # type: ignore[assignment]
        win32gui = None  # type: ignore[assignment]
except ImportError:
    win32con = None
    win32gui = None
    WIN32_KB_AVAILABLE = False

# Name -> virtual-key code for background_key (PostMessage WM_KEYDOWN/WM_KEYUP).
KEY_TO_VK: dict[str, int] = {
    "enter": 0x0D,
    "return": 0x0D,
    "tab": 0x09,
    "escape": 0x1B,
    "esc": 0x1B,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "space": 0x20,
    "f1": 0x70,
    "f2": 0x71,
    "f3": 0x72,
    "f4": 0x73,
    "f5": 0x74,
    "f6": 0x75,
    "f7": 0x76,
    "f8": 0x77,
    "f9": 0x78,
    "f10": 0x79,
    "f11": 0x7A,
    "f12": 0x7B,
}


def _require_win32() -> None:
    if not WIN32_KB_AVAILABLE or win32gui is None or win32con is None:
        raise RuntimeError("Win32 keyboard backend requires Windows with pywin32.")


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


def postmessage_type(hwnd: int, text: str) -> dict[str, Any]:
    """Type text into HWND via PostMessage WM_CHAR - no focus change, no cursor warp.

    Works for standard Edit controls and most UIA text fields. Rich/composed
    input (IME, some Electron apps) may ignore WM_CHAR - fall back to
    automation_keyboard(type) or automation_elements(set_text) then.
    """
    _require_win32()
    if not text:
        return {"method": "postmessage_type", "dispatch": "background", "characters_sent": 0}
    sent = 0
    for ch in text:
        win32gui.PostMessage(int(hwnd), win32con.WM_CHAR, ord(ch), 0)
        sent += 1
    return {"method": "postmessage_type", "dispatch": "background", "characters_sent": sent}


def postmessage_key(hwnd: int, key: str, *, presses: int = 1) -> dict[str, Any]:
    """Send a non-text key (enter, tab, escape, arrows, F-keys) to HWND via
    PostMessage WM_KEYDOWN/WM_KEYUP - no focus change."""
    _require_win32()
    name = (key or "").strip().lower()
    if name not in KEY_TO_VK:
        raise ValueError(f"Unknown background key: {key!r}. Supported: {', '.join(sorted(KEY_TO_VK))}.")
    vk = KEY_TO_VK[name]
    lparam_down = 0x00000001
    lparam_up = 0xC0000001
    for _ in range(max(1, int(presses))):
        win32gui.PostMessage(int(hwnd), win32con.WM_KEYDOWN, vk, lparam_down)
        win32gui.PostMessage(int(hwnd), win32con.WM_KEYUP, vk, lparam_up)
    return {"method": "postmessage_key", "dispatch": "background", "key": name, "vk": vk}
