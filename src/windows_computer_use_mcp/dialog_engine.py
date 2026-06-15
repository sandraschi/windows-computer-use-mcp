"""File dialog path entry — clipboard paste preferred over char-by-char typing."""

from __future__ import annotations

import logging
import time
from typing import Any

import pyautogui

logger = logging.getLogger(__name__)

try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


def set_path_field(
    path: str,
    *,
    use_clipboard: bool = True,
    select_all_first: bool = True,
    type_interval: float = 0.02,
) -> dict[str, Any]:
    """Fill the focused path field (Save/Open dialog)."""
    if not path:
        raise ValueError("path is required")

    method = "clipboard"
    if use_clipboard and CLIPBOARD_AVAILABLE:
        pyperclip.copy(path)
        if select_all_first:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
    else:
        method = "type"
        if select_all_first:
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.1)
        pyautogui.write(path, interval=type_interval)

    return {"method": method, "path_length": len(path), "characters_entered": len(path)}


def confirm_dialog(*, confirm_key: str = "enter", pause_s: float = 0.3) -> dict[str, Any]:
    """Press Enter/Esc to confirm or dismiss a dialog."""
    time.sleep(pause_s)
    pyautogui.press(confirm_key)
    return {"confirm_key": confirm_key, "pause_s": pause_s}


def submit_path(
    path: str,
    *,
    use_clipboard: bool = True,
    confirm_key: str = "enter",
    pause_before_confirm_s: float = 0.3,
    select_all_first: bool = True,
    post_confirm_pause_s: float = 0.0,
) -> dict[str, Any]:
    """Set path in focused dialog field and confirm."""
    from windows_computer_use_mcp.retry import with_retry

    def _run() -> dict[str, Any]:
        entry = set_path_field(
            path,
            use_clipboard=use_clipboard,
            select_all_first=select_all_first,
        )
        confirm = confirm_dialog(confirm_key=confirm_key, pause_s=pause_before_confirm_s)
        if post_confirm_pause_s > 0:
            time.sleep(post_confirm_pause_s)
        return {**entry, **confirm, "submitted": True}

    return with_retry(_run, label="dialog:submit_path")
