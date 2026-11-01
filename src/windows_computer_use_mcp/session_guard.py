"""Session liveness + UAC/secure-desktop detection for CUA preflight.

A CUA mission silently fails when the Windows session is not interactive:
locked screen, RDP-minimized session, screensaver, or a UAC consent prompt
on the secure desktop. All of those move input to a different desktop that
pywinauto/UIA cannot reach, so the honest move is to detect it *before* the
first click and say so plainly.

Signals (all fail-soft - unknown is reported, never raised):
- ``input_desktop_name()``: "Default" means the interactive desktop. Anything
  else (Winlogon, Screen-saver) means input is elsewhere.
- ``detect_uac()``: non-Default desktop + consent.exe running = UAC consent
  prompt most likely. Non-Default desktop without consent.exe = locked /
  screensaver / logged-out.
- ``session_preflight()``: one combined check (interactive + UAC + disk +
  memory) for ``automation_system(preflight)`` and the mission engine.

No package imports - leaf module (ctypes + psutil + shutil only) so tools
and the mission loop can import it without cycles.
"""

from __future__ import annotations

import logging
import shutil
import sys
from typing import Any

logger = logging.getLogger(__name__)

WIN32_AVAILABLE = sys.platform == "win32"

try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None  # type: ignore[assignment]
    _PSUTIL_AVAILABLE = False


def _input_desktop_name() -> str | None:
    """Name of the desktop that currently receives input, or None if unknown.

    Separated from :func:`detect_uac` so tests can patch this one function.
    """
    if not WIN32_AVAILABLE:
        return None
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.OpenInputDesktop.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        user32.OpenInputDesktop.restype = wintypes.HANDLE
        user32.GetUserObjectInformationW.argtypes = [
            wintypes.HANDLE,
            wintypes.INT,
            wintypes.LPVOID,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
        ]
        user32.GetUserObjectInformationW.restype = wintypes.BOOL
        user32.CloseDesktop.argtypes = [wintypes.HANDLE]
        user32.CloseDesktop.restype = wintypes.BOOL

        hdesk = user32.OpenInputDesktop(0, False, 0x0100)  # DESKTOP_READOBJECTS
        if not hdesk:
            return None
        try:
            needed = wintypes.DWORD(0)
            # UOI_NAME = 2. First call with NULL buffer to get length.
            user32.GetUserObjectInformationW(hdesk, 2, None, 0, ctypes.byref(needed))
            buf_len = max(needed.value, 64)
            buf = ctypes.create_unicode_buffer(buf_len)
            ok = user32.GetUserObjectInformationW(hdesk, 2, buf, buf_len * 2, ctypes.byref(needed))
            if not ok:
                return None
            return buf.value or None
        finally:
            user32.CloseDesktop(hdesk)
    except Exception as exc:
        logger.debug("input desktop query failed: %s", exc)
        return None


def _consent_running() -> bool:
    """True if a consent.exe (UAC) process exists. Separated for testability."""
    if not _PSUTIL_AVAILABLE:
        return False
    try:
        for proc in psutil.process_iter(["name"]):
            try:
                name = (proc.info.get("name") or "").lower()
            except Exception as exc:
                logger.debug("consent scan skipped a process: %s", exc)
                continue
            if name == "consent.exe":
                return True
        return False
    except Exception as exc:
        logger.debug("consent scan failed: %s", exc)
        return False


def is_interactive_desktop(desktop_name: str | None = None) -> bool | None:
    """True when input goes to the interactive desktop, False when elsewhere,
    None when the desktop name could not be determined (fail-soft)."""
    name = desktop_name if desktop_name is not None else _input_desktop_name()
    if name is None:
        return None
    return name == "Default"


def detect_uac() -> dict[str, Any]:
    """Detect a UAC consent prompt / secure desktop / locked session.

    Returns dict with:
    - interactive (bool | None): input reaches the Default desktop
    - secure_desktop (bool | None): input is on a non-Default desktop
    - uac_prompt (bool): secure desktop + consent.exe running
    - desktop_name (str | None), consent_running (bool)
    """
    name = _input_desktop_name()
    if name is None:
        return {
            "interactive": None,
            "secure_desktop": None,
            "uac_prompt": False,
            "desktop_name": None,
            "consent_running": _consent_running(),
            "unknown": True,
        }
    secure = name != "Default"
    consent = _consent_running() if secure else False
    return {
        "interactive": not secure,
        "secure_desktop": secure,
        "uac_prompt": bool(secure and consent),
        "desktop_name": name,
        "consent_running": consent,
    }


def foreground_window() -> dict[str, Any]:
    """HWND + title of the current foreground window, fail-soft."""
    if not WIN32_AVAILABLE:
        return {"hwnd": None, "title": None, "unknown": True}
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.GetForegroundWindow.restype = wintypes.HWND
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return {"hwnd": None, "title": None}
        length = user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        return {"hwnd": int(hwnd), "title": buf.value or None}
    except Exception as exc:
        logger.debug("foreground window query failed: %s", exc)
        return {"hwnd": None, "title": None, "unknown": True}


def session_preflight(
    *,
    min_disk_mb: float = 500.0,
    min_memory_mb: float = 512.0,
) -> dict[str, Any]:
    """Combined preflight: interactive session + no UAC prompt + resources.

    Returns {"ok": bool, "checks": [...], "warnings": [...], "uac": {...}}.
    ``ok`` is False when the session is provably non-interactive, a UAC
    prompt is up, or resources fail. Unknown signals produce warnings,
    never a hard fail (except disk, which is local and certain).
    """
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    uac = detect_uac()
    interactive = uac.get("interactive")
    checks.append(
        {
            "name": "interactive_session",
            "passed": interactive is not False,
            "desktop": uac.get("desktop_name"),
            "detail": "unknown desktop - proceeding" if interactive is None else None,
        }
    )
    if interactive is None:
        warnings.append("Could not determine input desktop - proceeding, clicks may not land.")
    checks.append(
        {
            "name": "uac_prompt",
            "passed": not uac.get("uac_prompt", False),
            "consent_running": uac.get("consent_running", False),
        }
    )

    try:
        free_mb = shutil.disk_usage(".").free / (1024 * 1024)
        disk_ok = free_mb >= min_disk_mb
        checks.append({"name": "disk_free", "passed": disk_ok, "free_mb": round(free_mb, 1), "min_mb": min_disk_mb})
    except Exception as exc:
        disk_ok = False
        checks.append({"name": "disk_free", "passed": False, "error": str(exc)})

    if _PSUTIL_AVAILABLE:
        try:
            avail_mb = float(psutil.virtual_memory().available) / (1024 * 1024)
            mem_ok = avail_mb >= min_memory_mb
            checks.append(
                {
                    "name": "memory_available",
                    "passed": mem_ok,
                    "available_mb": round(avail_mb, 1),
                    "min_mb": min_memory_mb,
                }
            )
        except Exception as exc:
            mem_ok = True
            warnings.append(f"Memory probe failed ({exc}) - proceeding.")
            checks.append({"name": "memory_available", "passed": True, "skipped": True})
    else:
        mem_ok = True
        warnings.append("psutil unavailable - memory check skipped.")
        checks.append({"name": "memory_available", "passed": True, "skipped": True})

    ok = bool(interactive is not False) and not uac.get("uac_prompt", False) and disk_ok and mem_ok
    return {"ok": ok, "checks": checks, "warnings": warnings, "uac": uac}


__all__ = [
    "WIN32_AVAILABLE",
    "detect_uac",
    "foreground_window",
    "is_interactive_desktop",
    "session_preflight",
]
