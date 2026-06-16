"""App-specific automation profiles — YAML-based interaction blueprints.

Each profile defines how to detect, launch, shortcut, and verify a Windows application.
Profiles live in ``profiles/`` (built-in) and ``~/.windows-computer-use-mcp/profiles/`` (user).

Profile format (YAML):
    name: unique identifier
    detect.window_class: UIA window class name
    detect.title_pattern: regex for window title
    detect.process_names: [list of .exe names]
    launch.command: shell command to launch
    launch.wait_for_window: seconds to wait after launch
    shortcuts: {friendly_name: {hotkey: "ctrl+s"}}
    elements: {friendly_name: {control_type, class_name, auto_id, title}}
    recovery: {state_name: [{action, ...}]}
    verification: {name: {op, element, timeout, text}}
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

PROFILES_DIR = Path(__file__).parent / "profiles"
USER_PROFILES_DIR = Path.home() / ".windows-computer-use-mcp" / "profiles"

_cached_profiles: dict[str, dict[str, Any]] = {}


def _load_yaml(path: Path) -> dict[str, Any] | None:
    """Load a YAML profile file, returning None on failure."""
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning("Failed to load profile %s: %s", path, e)
        return None


def _discover_profiles() -> dict[str, dict[str, Any]]:
    """Scan both built-in and user profile directories."""
    profiles: dict[str, dict[str, Any]] = {}
    for d in [PROFILES_DIR, USER_PROFILES_DIR]:
        if not d.exists():
            continue
        for fpath in sorted(d.glob("*.yaml")):
            data = _load_yaml(fpath)
            if data and isinstance(data, dict) and data.get("name"):
                profiles[data["name"]] = data
    return profiles


def reload_profiles() -> dict[str, str]:
    """Re-scan all profile directories and return {name: status}."""
    global _cached_profiles
    _cached_profiles = _discover_profiles()
    return {name: "loaded" for name in _cached_profiles}


def get_profile(name: str) -> dict[str, Any] | None:
    """Get a profile by name. Caches on first call."""
    global _cached_profiles
    if not _cached_profiles:
        _cached_profiles = _discover_profiles()
    return _cached_profiles.get(name)


def list_profiles() -> list[dict[str, Any]]:
    """List all discovered profiles with summary metadata."""
    global _cached_profiles
    if not _cached_profiles:
        _cached_profiles = _discover_profiles()
    result = []
    for name, data in _cached_profiles.items():
        result.append({
            "name": name,
            "display_name": data.get("display_name", name),
            "description": data.get("description", ""),
            "version": data.get("version", "0.1"),
            "shortcut_count": len(data.get("shortcuts", {})),
            "element_count": len(data.get("elements", {})),
        })
    return sorted(result, key=lambda p: p["name"])


def detect_app(window_title: str, window_class: str | None = None,
               process_name: str | None = None) -> Optional[dict[str, Any]]:
    """Auto-detect which profile matches a given window.

    Args:
        window_title: Current window title text.
        window_class: UIA class name (optional).
        process_name: Process .exe name (optional).

    Returns:
        Matching profile dict, or None.
    """
    global _cached_profiles
    if not _cached_profiles:
        _cached_profiles = _discover_profiles()

    for name, data in _cached_profiles.items():
        detect = data.get("detect", {})

        # Match process name
        if process_name and detect.get("process_names"):
            if process_name.lower() in [p.lower() for p in detect["process_names"]]:
                return data

        # Match window class
        if window_class and detect.get("window_class"):
            if window_class.lower() == detect["window_class"].lower():
                return data

        # Match title pattern
        if window_title and detect.get("title_pattern"):
            try:
                if re.search(detect["title_pattern"], window_title, re.IGNORECASE):
                    return data
            except re.error:
                continue

    return None


def get_profile_shortcut(name: str, shortcut_name: str) -> str | None:
    """Get a hotkey string from a profile's shortcuts.

    Args:
        name: Profile name.
        shortcut_name: Friendly shortcut name (e.g. 'save', 'bold').

    Returns:
        Hotkey string (e.g. 'ctrl+s') or None.
    """
    profile = get_profile(name)
    if not profile:
        return None
    shortcuts = profile.get("shortcuts", {})
    entry = shortcuts.get(shortcut_name, {})
    if isinstance(entry, str):
        return entry
    return entry.get("hotkey") if isinstance(entry, dict) else None


def get_profile_element(name: str, element_name: str) -> dict[str, Any] | None:
    """Get element selectors for a friendly element name from a profile.

    Args:
        name: Profile name.
        element_name: Friendly element name (e.g. 'text_editor').

    Returns:
        Dict with control_type, class_name, auto_id, title, or None.
    """
    profile = get_profile(name)
    if not profile:
        return None
    return profile.get("elements", {}).get(element_name)


def get_profile_launch(name: str) -> dict[str, Any] | None:
    """Get launch configuration for a profile.

    Args:
        name: Profile name.

    Returns:
        Dict with command, wait_for_window, or None.
    """
    profile = get_profile(name)
    if not profile:
        return None
    return profile.get("launch")


def get_profile_verification(name: str, verify_name: str) -> dict[str, Any] | None:
    """Get a verification check from a profile.

    Args:
        name: Profile name.
        verify_name: Verification name.

    Returns:
        Dict with op, element, timeout, text, or None.
    """
    profile = get_profile(name)
    if not profile:
        return None
    return profile.get("verification", {}).get(verify_name)
