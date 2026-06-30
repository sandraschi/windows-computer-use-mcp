"""VRoid Studio semantic shortcut registry — shortcut-first automation.

Official reference: https://vroid.pixiv.help/hc/en-us/articles/900006050066
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ShortcutDef:
    action: str
    keys: str
    description: str = ""
    wait_stable: bool = True
    stable_timeout_s: float = 10.0
    category: str = "general"


# Clicks only for sample tile + preset thumbnails — everything else is here.
VROIDSTUDIO_SHORTCUTS: dict[str, ShortcutDef] = {
    "save": ShortcutDef("save", "ctrl+s", "Save project", category="file"),
    "save_as": ShortcutDef(
        "save_as", "ctrl+shift+s", "Save As dialog", wait_stable=True, stable_timeout_s=12, category="file"
    ),
    "open": ShortcutDef("open", "ctrl+o", "Open project dialog", category="file"),
    "new": ShortcutDef("new", "ctrl+n", "New project", category="file"),
    "undo": ShortcutDef("undo", "ctrl+z", "Undo", wait_stable=False, category="edit"),
    "redo": ShortcutDef("redo", "ctrl+shift+z", "Redo", wait_stable=False, category="edit"),
    "face_editor": ShortcutDef("face_editor", "f1", "Face editor tab", category="editor"),
    "hairstyle_editor": ShortcutDef("hairstyle_editor", "f2", "Hair editor tab", category="editor"),
    "body_editor": ShortcutDef("body_editor", "f3", "Body editor tab", category="editor"),
    "outfits_editor": ShortcutDef("outfits_editor", "f4", "Outfits editor tab", category="editor"),
    "accessories_editor": ShortcutDef("accessories_editor", "f5", "Accessories editor tab", category="editor"),
    "looks_editor": ShortcutDef("looks_editor", "f6", "Looks editor tab", category="editor"),
    "photo_booth": ShortcutDef("photo_booth", "f7", "Photo booth", category="editor"),
    "export_vrm": ShortcutDef("export_vrm", "f8", "Export VRM dialog", stable_timeout_s=12, category="export"),
    "export": ShortcutDef("export", "f8", "Alias for export_vrm", stable_timeout_s=12, category="export"),
    "upload_to_vroid_hub": ShortcutDef("upload_to_vroid_hub", "f9", "Upload to Hub", category="export"),
    "preset_tab": ShortcutDef("preset_tab", "ctrl+1", "Preset panel", category="panel"),
    "custom_tab": ShortcutDef("custom_tab", "ctrl+2", "Custom panel", category="panel"),
    "dialog_ok": ShortcutDef("dialog_ok", "enter", "Confirm dialog", wait_stable=True, category="dialog"),
    "dialog_cancel": ShortcutDef("dialog_cancel", "escape", "Cancel dialog", wait_stable=True, category="dialog"),
    "dialog_tab_next": ShortcutDef("dialog_tab_next", "tab", "Next field", wait_stable=False, category="dialog"),
    "dialog_tab_prev": ShortcutDef(
        "dialog_tab_prev", "shift+tab", "Previous field", wait_stable=False, category="dialog"
    ),
    "front_view": ShortcutDef("front_view", "1", "Camera front", wait_stable=False, category="camera"),
    "zoom_in": ShortcutDef("zoom_in", "ctrl+;", "Zoom in", wait_stable=False, category="camera"),
    "zoom_out": ShortcutDef("zoom_out", "ctrl+-", "Zoom out", wait_stable=False, category="camera"),
}
