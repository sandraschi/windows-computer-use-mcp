"""CUA-MCP environment aliases (Phase 6 rename transition)."""

from __future__ import annotations

import os


def cua_getenv(primary: str, *legacy: str, default: str | None = None) -> str | None:
    """Read CUA_MCP_* first, then windows_computer_use_mcp_* legacy names."""
    val = os.environ.get(primary)
    if val is not None:
        return val
    for name in legacy:
        val = os.environ.get(name)
        if val is not None:
            return val
    return default


def cua_truthy(primary: str, *legacy: str, default: str = "0") -> bool:
    raw = cua_getenv(primary, *legacy, default=default) or default
    return raw.lower() in ("1", "true", "yes", "on")


def keyboard_backend() -> str:
    """pyautogui (default) or win32."""
    return (cua_getenv("CUA_MCP_KEYBOARD", "windows_computer_use_mcp_KEYBOARD", default="pyautogui") or "pyautogui").lower()
