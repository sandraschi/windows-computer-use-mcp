"""Multi-monitor display utilities using Win32 APIs.

Provides monitor enumeration, per-monitor geometry, DPI scaling,
and coordinate translation for multi-monitor setups.
"""

from __future__ import annotations

import ctypes
import logging
import sys
from dataclasses import dataclass, field
from typing import List

logger = logging.getLogger(__name__)

DISPLAY_AVAILABLE = sys.platform == "win32"

if DISPLAY_AVAILABLE:
    import win32api
    import win32con
    import win32gui

    _user32 = ctypes.windll.user32
    _gdi32 = ctypes.windll.gdi32
    _shcore = ctypes.windll.shcore
else:
    win32api = None
    win32con = None
    win32gui = None


@dataclass
class MonitorInfo:
    index: int
    left: int
    top: int
    right: int
    bottom: int
    width: int
    height: int
    is_primary: bool
    dpi_x: int = 96
    dpi_y: int = 96
    scale_factor: float = 1.0
    name: str = ""


def _require_windows() -> None:
    if not DISPLAY_AVAILABLE:
        raise RuntimeError("display_utils requires Windows")


def _dump_monitors() -> None:
    """Log every available monitor with size, DPI, primary flag."""
    monitors = enum_monitors()
    for m in monitors:
        logger.info(
            "Monitor %d: %s %dx%d @ (%d,%d) DPI=%dx%d scale=%.1f primary=%s",
            m.index, m.name, m.width, m.height,
            m.left, m.top, m.dpi_x, m.dpi_y, m.scale_factor, m.is_primary,
        )


def enum_monitors() -> List[MonitorInfo]:
    """Enumerate all monitors via EnumDisplayMonitors.

    Returns:
        List[MonitorInfo]: one entry per monitor, sorted by (primary first, then left edge).
    """
    _require_windows()
    raw: list[MonitorInfo] = []

    def _enum_proc(hmonitor: int, _hdc: int, rect_ptr: int, _data: int) -> int:
        ptr = ctypes.cast(rect_ptr, ctypes.POINTER(ctypes.c_long * 4))
        left, top, right, bottom = ptr.contents[0], ptr.contents[1], ptr.contents[2], ptr.contents[3]
        info = _get_monitor_info(hmonitor)
        is_primary = bool(info["dwFlags"] & 1)

        mi = MonitorInfo(
            index=0,
            left=left, top=top, right=right, bottom=bottom,
            width=right - left, height=bottom - top,
            is_primary=is_primary,
            name=info["szDevice"] or "",
        )

        try:
            dpi_x = ctypes.c_uint()
            dpi_y = ctypes.c_uint()
            _shcore.GetDpiForMonitor(
                ctypes.c_void_p(hmonitor),
                0,  # MDT_EFFECTIVE_DPI
                ctypes.byref(dpi_x),
                ctypes.byref(dpi_y),
            )
            mi.dpi_x = dpi_x.value
            mi.dpi_y = dpi_y.value
            mi.scale_factor = round(dpi_x.value / 96.0, 1)
        except Exception:
            pass

        raw.append(mi)
        return 1

    cb = ctypes.WINFUNCTYPE(
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_long * 4),
        ctypes.c_long,
    )

    _user32.EnumDisplayMonitors(
        None, None,
        cb(_enum_proc),
        0,
    )

    raw.sort(key=lambda m: (0 if m.is_primary else 1, m.left))
    for i, m in enumerate(raw):
        m.index = i
    return raw


def _get_monitor_info(hmonitor: int) -> dict:
    """Get MONITORINFOEX for a monitor handle."""
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    class MONITORINFOEX(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.c_ulong),
            ("rcMonitor", RECT),
            ("rcWork", RECT),
            ("dwFlags", ctypes.c_ulong),
            ("szDevice", ctypes.c_wchar * 32),
        ]

    info = MONITORINFOEX()
    info.cbSize = ctypes.sizeof(MONITORINFOEX)
    ok = _user32.GetMonitorInfoW(ctypes.c_void_p(hmonitor), ctypes.byref(info))
    if not ok:
        return {"dwFlags": 0, "szDevice": "", "rcMonitor": (0, 0, 0, 0), "rcWork": (0, 0, 0, 0)}
    return {
        "dwFlags": info.dwFlags,
        "szDevice": info.szDevice,
        "rcMonitor": (info.rcMonitor.left, info.rcMonitor.top, info.rcMonitor.right, info.rcMonitor.bottom),
        "rcWork": (info.rcWork.left, info.rcWork.top, info.rcWork.right, info.rcWork.bottom),
    }


def get_primary_monitor() -> MonitorInfo:
    """Return the primary monitor info.

    Returns:
        MonitorInfo for the primary display.

    Raises:
        RuntimeError: if no primary monitor found (unlikely on Windows).
    """
    for m in enum_monitors():
        if m.is_primary:
            return m
    raise RuntimeError("No primary monitor found")


def get_monitor_by_index(index: int) -> MonitorInfo:
    """Resolve a 0-based monitor index to its info.

    Args:
        index: 0-based monitor index (0 = primary, 1 = next, etc.).

    Returns:
        MonitorInfo for the requested index.

    Raises:
        IndexError: if index >= monitor count.
    """
    monitors = enum_monitors()
    if index < 0 or index >= len(monitors):
        raise IndexError(
            f"Monitor index {index} out of range. "
            f"Found {len(monitors)} monitor(s): {[m.name for m in monitors]}"
        )
    return monitors[index]


def get_monitor_at_point(x: int, y: int) -> MonitorInfo:
    """Find which monitor contains the given virtual-screen point.

    Args:
        x: virtual screen X coordinate.
        y: virtual screen Y coordinate.

    Returns:
        MonitorInfo for the monitor containing (x, y).
    """
    _require_windows()
    hmonitor = _user32.MonitorFromPoint(
        ctypes.wintypes.POINT(x, y), 2  # MONITOR_DEFAULTTONEAREST
    )
    if not hmonitor:
        return get_primary_monitor()

    info = _get_monitor_info(hmonitor)
    rect = info["rcMonitor"]
    monitors = enum_monitors()
    for m in monitors:
        if (m.left, m.top, m.right, m.bottom) == rect:
            return m
    return get_primary_monitor()


def get_monitor_origin(index: int) -> tuple[int, int]:
    """Get the virtual-screen origin (left, top) for a monitor index.

    Args:
        index: 0-based monitor index.

    Returns:
        (origin_x, origin_y) in virtual screen coordinates.
    """
    m = get_monitor_by_index(index)
    return m.left, m.top


def virtual_screen_bounds() -> tuple[int, int, int, int]:
    """Return the bounding box of the entire virtual desktop.

    Returns:
        (left, top, right, bottom) spanning all monitors.
    """
    _require_windows()
    return (
        win32api.GetSystemMetrics(76),  # SM_XVIRTUALSCREEN
        win32api.GetSystemMetrics(77),  # SM_YVIRTUALSCREEN
        win32api.GetSystemMetrics(76) + win32api.GetSystemMetrics(78),  # left + virtual width
        win32api.GetSystemMetrics(77) + win32api.GetSystemMetrics(79),  # top + virtual height
    )


def virtual_screen_size() -> tuple[int, int]:
    """Return total virtual screen width and height across all monitors.

    Returns:
        (total_width, total_height) in virtual screen pixels.
    """
    _require_windows()
    return (
        win32api.GetSystemMetrics(78),  # SM_CXVIRTUALSCREEN
        win32api.GetSystemMetrics(79),  # SM_CYVIRTUALSCREEN
    )


def translate_coords(x: int, y: int, monitor_index: int | None = None) -> tuple[int, int]:
    """Translate coordinates to virtual screen coordinates.

    If monitor_index is set, treat (x, y) as relative to that monitor's
    origin and add the monitor origin offset. Otherwise treat as absolute
    virtual screen coordinates (pass-through).

    Args:
        x: X coordinate (relative to monitor if monitor_index is set).
        y: Y coordinate (relative to monitor if monitor_index is set).
        monitor_index: Optional 0-based monitor index.

    Returns:
        (virtual_x, virtual_y) — absolute virtual screen coordinates.
    """
    if monitor_index is not None:
        ox, oy = get_monitor_origin(monitor_index)
        return x + ox, y + oy
    return x, y


# Pre-sort monitor list on import so index 0 is always primary
_ = _dump_monitors()
