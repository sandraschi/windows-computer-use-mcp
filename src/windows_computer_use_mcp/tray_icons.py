"""Windows notification-area (system tray) icon listing + clicking.

The tray is not a normal UIA window - its icons live in a ToolbarWindow32
control owned by explorer.exe, so pywinauto/UIA cannot enumerate them. This
module drives the toolbar directly with TB_* messages and reads button text
via cross-process memory (the standard recipe - SendMessage executes in
explorer's thread, so text buffers must live in explorer's address space).

Limitations (honest, by design):
- Same-arch only: a 64-bit Python cannot reliably read a 32-bit explorer's
  TBBUTTON structs and vice versa. Struct packing assumes matching bitness.
- The overflow ("Show hidden icons") toolbar only exists while the overflow
  flyout is open. Point users at the taskbar chevron first.
- Clicks go through with PostMessage (no cursor move) and are not verifiable;
  callers should confirm with a screenshot.

All entry points fail soft: {"success": False, "error": ...} - never raises.
"""

from __future__ import annotations

import ctypes
import logging
import struct
from ctypes import wintypes
from typing import Any

logger = logging.getLogger(__name__)

WIN32_AVAILABLE = True
try:
    import win32con
    import win32gui
except ImportError:  # pragma: no cover - non-Windows / missing pywin32
    WIN32_AVAILABLE = False
    win32con = None  # type: ignore[assignment]
    win32gui = None  # type: ignore[assignment]

# Toolbar messages (commctrl.h)
TB_BUTTONCOUNT = 0x0418
TB_GETBUTTON = 0x0417
TB_GETBUTTONTEXTW = 0x044B
TB_GETRECT = 0x0433

# Process access + memory flags
_PROCESS_VM_OPERATION = 0x0008
_PROCESS_VM_READ = 0x0010
_PROCESS_VM_WRITE = 0x0020
_PROCESS_QUERY_INFORMATION = 0x0400
_MEM_COMMIT = 0x1000
_MEM_RELEASE = 0x8000
_PAGE_READWRITE = 0x04

# TBBUTTON is 32 bytes on 64-bit and 20 bytes on 32-bit. We pack for the
# *local* interpreter bitness and require explorer to match (same-arch rule).
_PTR = "Q" if struct.calcsize("P") == 8 else "I"
_TBBUTTON_FMT = f"iiBB6s{_PTR}{_PTR}"
_TBBUTTON_SIZE = struct.calcsize(_TBBUTTON_FMT)


def _find_tray_toolbar(*, overflow: bool) -> int | None:
    """HWND of the tray ToolbarWindow32 (main or overflow flyout)."""
    if not WIN32_AVAILABLE:
        return None
    try:
        if overflow:
            flyout = win32gui.FindWindow("NotifyIconOverflowWindow", None)
            if not flyout:
                return None
            return win32gui.FindWindowEx(flyout, 0, "ToolbarWindow32", None) or None
        tray = win32gui.FindWindow("Shell_TrayWnd", None)
        if not tray:
            return None
        notify = win32gui.FindWindowEx(tray, 0, "TrayNotifyWnd", None)
        if not notify:
            return None
        pager = win32gui.FindWindowEx(notify, 0, "SysPager", None)
        parent = pager or notify
        return win32gui.FindWindowEx(parent, 0, "ToolbarWindow32", None) or None
    except Exception as exc:
        logger.debug("tray toolbar lookup failed: %s", exc)
        return None


def _open_process(pid: int) -> int:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = kernel32.OpenProcess(
        _PROCESS_VM_OPERATION | _PROCESS_VM_READ | _PROCESS_VM_WRITE | _PROCESS_QUERY_INFORMATION,
        False,
        pid,
    )
    if not handle:
        raise OSError(f"OpenProcess({pid}) failed")
    return handle


def _remote_alloc(proc_handle: int, size: int) -> int:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    addr = kernel32.VirtualAllocEx(proc_handle, None, size, _MEM_COMMIT, _PAGE_READWRITE)
    if not addr:
        raise OSError("VirtualAllocEx failed")
    return addr


def _read_button_text(toolbar_hwnd: int, proc_handle: int, command_id: int) -> str:
    """Read one button's tooltip text via a remote buffer. Empty string on failure."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    buf_size = 512 * 2  # WCHARs
    remote_buf = 0
    try:
        remote_buf = _remote_alloc(proc_handle, buf_size)
        # SendMessage executes in the toolbar's thread - the buffer must be remote.
        import win32gui as _gui

        length = _gui.SendMessage(toolbar_hwnd, TB_GETBUTTONTEXTW, command_id, remote_buf)
        if length <= 0:
            return ""
        local = ctypes.create_unicode_buffer(length + 1)
        bytes_read = wintypes.DWORD(0)
        ok = kernel32.ReadProcessMemory(proc_handle, remote_buf, local, (length + 1) * 2, ctypes.byref(bytes_read))
        if not ok:
            return ""
        return local.value or ""
    except Exception as exc:
        logger.debug("tray text read failed: %s", exc)
        return ""
    finally:
        if remote_buf:
            try:
                kernel32.VirtualFreeEx(proc_handle, remote_buf, 0, _MEM_RELEASE)
            except Exception as exc:
                logger.debug("tray buffer free failed: %s", exc)


def _read_button_rect(toolbar_hwnd: int, index: int) -> dict[str, int] | None:
    """Client-area rect of button index. RECT lives in our process - no remote alloc needed."""
    try:
        import win32gui as _gui

        rect = _gui.SendMessage(toolbar_hwnd, TB_GETRECT, index, None)
        # pywin32 returns a tuple for TB_GETRECT.
        if not rect or len(rect) < 4:
            return None
        left, top, right, bottom = (int(v) for v in rect[:4])
        return {"left": left, "top": top, "right": right, "bottom": bottom}
    except Exception as exc:
        logger.debug("tray rect read failed: %s", exc)
        return None


def list_tray_icons(*, overflow: bool = False) -> dict[str, Any]:
    """List notification-area icons: [{index, id_command, text, rect}]."""
    if not WIN32_AVAILABLE:
        return {"success": False, "error": "Tray access requires Windows with pywin32."}
    toolbar = _find_tray_toolbar(overflow=overflow)
    if not toolbar:
        if overflow:
            return {
                "success": False,
                "error": "Overflow flyout is not open.",
                "recovery_tip": "Click the taskbar 'Show hidden icons' chevron first "
                "(automation_elements click on button 'Show hidden icons'), then retry with overflow=True.",
            }
        return {"success": False, "error": "Tray toolbar not found."}
    try:
        import win32gui as _gui

        _, pid = _gui.GetWindowThreadProcessId(toolbar)
    except Exception as exc:
        return {"success": False, "error": f"Toolbar owner lookup failed: {exc}"}

    proc_handle = 0
    remote_struct = 0
    icons: list[dict[str, Any]] = []
    try:
        import win32gui as _gui

        count = _gui.SendMessage(toolbar, TB_BUTTONCOUNT, 0, 0)
        proc_handle = _open_process(pid)
        remote_struct = _remote_alloc(proc_handle, _TBBUTTON_SIZE)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        for index in range(int(count or 0)):
            try:
                _gui.SendMessage(toolbar, TB_GETBUTTON, index, remote_struct)
                raw = ctypes.create_string_buffer(_TBBUTTON_SIZE)
                bytes_read = wintypes.DWORD(0)
                ok = kernel32.ReadProcessMemory(
                    proc_handle, remote_struct, raw, _TBBUTTON_SIZE, ctypes.byref(bytes_read)
                )
                if not ok:
                    continue
                _bitmap, command_id, _state, _style, _reserved, _data, _string = struct.unpack(_TBBUTTON_FMT, raw.raw)
                icons.append(
                    {
                        "index": index,
                        "id_command": int(command_id),
                        "text": _read_button_text(toolbar, proc_handle, int(command_id)),
                        "rect": _read_button_rect(toolbar, index),
                    }
                )
            except Exception as exc:
                logger.debug("tray button %d skipped: %s", index, exc)
        return {"success": True, "toolbar_hwnd": int(toolbar), "count": len(icons), "icons": icons}
    except Exception as exc:
        return {"success": False, "error": f"Tray enumeration failed: {exc}"}
    finally:
        if WIN32_AVAILABLE:
            try:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                if remote_struct:
                    kernel32.VirtualFreeEx(proc_handle, remote_struct, 0, _MEM_RELEASE)
                if proc_handle:
                    kernel32.CloseHandle(proc_handle)
            except Exception as exc:
                logger.debug("tray cleanup failed: %s", exc)


def click_tray_icon(*, index: int | None = None, text: str | None = None, overflow: bool = False) -> dict[str, Any]:
    """Click a tray icon by index or tooltip-text substring (PostMessage, no cursor move)."""
    if index is None and not text:
        return {
            "success": False,
            "error": "Provide index or text to pick the tray icon.",
            "recovery_tip": "Call tray_list first (overflow=True for hidden icons).",
        }
    listed = list_tray_icons(overflow=overflow)
    if not listed.get("success"):
        return listed
    icons = listed.get("icons", [])
    pick: dict[str, Any] | None = None
    if index is not None:
        matches = [b for b in icons if b.get("index") == index]
        pick = matches[0] if matches else None
    else:
        needle = (text or "").lower()
        matches = [b for b in icons if needle in (b.get("text") or "").lower()]
        pick = matches[0] if matches else None
    if pick is None:
        return {
            "success": False,
            "error": f"No tray icon matches index={index} text={text!r} ({len(icons)} icons).",
            "recovery_tip": "Call tray_list and use an exact index or a tooltip substring.",
        }
    rect = pick.get("rect")
    if not rect:
        return {"success": False, "error": "Icon rect unavailable - cannot click."}
    try:
        from windows_computer_use_mcp.win32_window import postmessage_click_at

        cx = (rect["left"] + rect["right"]) // 2
        cy = (rect["top"] + rect["bottom"]) // 2
        # ClientToScreen: postmessage_click_at takes screen coords.
        screen = win32gui.ClientToScreen(listed["toolbar_hwnd"], (cx, cy))
        meta = postmessage_click_at(int(listed["toolbar_hwnd"]), int(screen[0]), int(screen[1]))
        return {
            "success": True,
            "icon": pick,
            "delivery_note": "PostMessage click - not verifiable; confirm with screenshot.",
            **meta,
        }
    except Exception as exc:
        return {"success": False, "error": f"Tray click failed: {exc}"}


__all__ = ["click_tray_icon", "list_tray_icons"]
