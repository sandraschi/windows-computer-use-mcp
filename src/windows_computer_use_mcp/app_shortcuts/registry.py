"""Shortcut registry lookup across supported applications."""

from __future__ import annotations

from windows_computer_use_mcp.app_shortcuts.vroidstudio import VROIDSTUDIO_SHORTCUTS, ShortcutDef

REGISTRIES: dict[str, dict[str, ShortcutDef]] = {
    "vroidstudio": VROIDSTUDIO_SHORTCUTS,
    "vroid": VROIDSTUDIO_SHORTCUTS,
    "vroid_studio": VROIDSTUDIO_SHORTCUTS,
}


def list_apps() -> list[str]:
    return ["vroidstudio"]


def list_shortcuts(app: str) -> dict[str, ShortcutDef]:
    reg = REGISTRIES.get(app.lower())
    if not reg:
        raise KeyError(f"Unknown app shortcut registry: {app}")
    return dict(reg)


def get_shortcut(app: str, action: str) -> ShortcutDef:
    reg = list_shortcuts(app)
    key = action.lower()
    if key not in reg:
        raise KeyError(f"Unknown action '{action}' for app '{app}'")
    return reg[key]
