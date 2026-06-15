"""Unified keyboard dispatch — pyautogui or win32-focused."""

from __future__ import annotations

from collections.abc import Sequence

from windows_computer_use_mcp.cua_env import keyboard_backend


def send_hotkey(keys: Sequence[str], *, hwnd: int | None = None, pause: float = 0.0) -> dict:
    backend = keyboard_backend()
    if backend == "win32":
        from windows_computer_use_mcp.win32_keyboard import send_hotkey as win32_hotkey

        return win32_hotkey(keys, hwnd=hwnd, pause=pause)

    import pyautogui

    pyautogui.hotkey(*[k.lower() for k in keys])
    if pause > 0:
        import time

        time.sleep(pause)
    return {"method": "pyautogui", "keys": list(keys)}


def send_press(key: str, *, hwnd: int | None = None, presses: int = 1, pause: float = 0.0) -> dict:
    backend = keyboard_backend()
    if backend == "win32":
        from windows_computer_use_mcp.win32_keyboard import send_press as win32_press

        return win32_press(key, hwnd=hwnd, presses=presses, pause=pause)

    import pyautogui

    for _ in range(presses):
        pyautogui.press(key.lower())
        if pause > 0:
            import time

            time.sleep(pause)
    return {"method": "pyautogui", "key": key}


def parse_hotkey(keys: str) -> list[str]:
    return [part.strip() for part in keys.lower().split("+") if part.strip()]


def is_modifier_combo(keys: list[str]) -> bool:
    mods = {"ctrl", "shift", "alt", "win"}
    return len(keys) > 1 and any(k in mods for k in keys)
