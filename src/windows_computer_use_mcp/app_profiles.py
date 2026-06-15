"""Per-application automation profiles — foreground policy, window title, regions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegionMask:
    """Window-relative crop for stability asserts and template matching."""

    left: int
    top: int
    right: int
    bottom: int
    label: str = "default"

    def as_tuple(self) -> tuple[int, int, int, int]:
        return (self.left, self.top, self.right, self.bottom)

    def as_dict(self) -> dict[str, int | str]:
        return {
            "region_left": self.left,
            "region_top": self.top,
            "region_right": self.right,
            "region_bottom": self.bottom,
            "label": self.label,
        }


@dataclass(frozen=True)
class AppProfile:
    app_id: str
    window_title: str
    dispatch: str = "foreground"
    keyboard_backend: str = "win32"
    description: str = ""
    stable_region: RegionMask | None = None
    template_version: str = "default"


PROFILES: dict[str, AppProfile] = {
    "vroidstudio": AppProfile(
        app_id="vroidstudio",
        window_title="VRoid Studio",
        dispatch="foreground",
        keyboard_backend="win32",
        description="Unity GPU app — always foreground, shortcut-first",
        stable_region=RegionMask(
            280,
            120,
            1640,
            980,
            label="editor_canvas",
        ),
        template_version="default",
    ),
    "vroid": AppProfile(
        app_id="vroidstudio",
        window_title="VRoid Studio",
        dispatch="foreground",
        keyboard_backend="win32",
        stable_region=RegionMask(280, 120, 1640, 980, label="editor_canvas"),
        template_version="default",
    ),
    "libreoffice": AppProfile(
        app_id="libreoffice",
        window_title="LibreOffice",
        dispatch="background",
        keyboard_backend="pyautogui",
        description="Calc/Writer — background UIA often works",
    ),
    "kicad": AppProfile(
        app_id="kicad",
        window_title="KiCad",
        dispatch="foreground",
        keyboard_backend="win32",
        description="EDA — schematic/PCB design, no API, shortcut-first",
        stable_region=RegionMask(0, 80, 1920, 1040, label="canvas"),
        template_version="default",
    ),
}


def get_profile(app_id: str) -> AppProfile | None:
    return PROFILES.get(app_id.lower())


def get_profile_region(app_id: str) -> tuple[int, int, int, int] | None:
    """Return window-relative stable region for an app profile (T2.4)."""
    profile = get_profile(app_id)
    if profile and profile.stable_region:
        return profile.stable_region.as_tuple()
    return None


def region_dict_for_app(app_id: str) -> dict[str, int | str] | None:
    profile = get_profile(app_id)
    if profile and profile.stable_region:
        return profile.stable_region.as_dict()
    return None


def list_profiles() -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for p in PROFILES.values():
        if p.app_id in seen:
            continue
        seen.add(p.app_id)
        entry: dict = {
            "app_id": p.app_id,
            "window_title": p.window_title,
            "dispatch": p.dispatch,
            "keyboard_backend": p.keyboard_backend,
            "description": p.description,
            "template_version": p.template_version,
        }
        if p.stable_region:
            entry["stable_region"] = p.stable_region.as_dict()
        out.append(entry)
    return out
