"""WinApp analysis tool — auto-crawl UI tree, screenshot portfolio, element maps.

PORTMANTEAU RATIONALE:
Instead of manually calling get_window_state + automation_windows + automation_visual
+ automation_keyboard in sequence to map an unknown app, this tool does it all in one
shot: crawl the UI tree, take annotated screenshots, try shortcut discovery, and
produce a structured markdown report + image portfolio.

OPERATIONS:
- crawl: Walk UI tree, screenshot, return element map + report
- portfolio: Capture multiple app states (main, dialogs, menus) via shortcuts
- discover: Probe common keyboard shortcuts and capture results

HUD:
Shows a "CUA at work" blinking red overlay + e-stop button during operations.
Target window is auto-refocused before each action to prevent focus stealers
(Discord, Slack, etc.) from breaking the crawl.
"""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

try:
    from windows_computer_use_mcp.app import app
except ImportError:
    app = None


def _with_hud(window_handle: int | None, window_title: str | None, fn):
    """Wrap an operation with CUA HUD + ensure_focus."""
    from windows_computer_use_mcp.cua_hud import CuaHUD

    hud = CuaHUD()
    hud.start()

    try:
        # Resolve HWND
        hwnd = window_handle
        if hwnd is None and window_title:
            try:
                import pygetwindow as gw
                wins = gw.getWindowsWithTitle(window_title)
                if wins:
                    hwnd = wins[0]._hWnd
            except Exception as exc:
                logger.warning("Window lookup failed: %s", exc)

        if hwnd is None:
            hud.stop()
            return {"success": False, "error": "No window specified or found"}

        hud.ensure_focus(hwnd)
        result = fn(hwnd, hud)
        return result
    finally:
        hud.stop()


def _ensure_focus(hwnd: int):
    """Refocus target window to combat focus stealers."""
    try:
        import win32gui

        current = win32gui.GetForegroundWindow()
        if current != hwnd:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.05)
    except Exception as exc:
        logger.debug("ensure_focus: %s", exc)


def _screenshot_to_path(
    window_handle: int, output_dir: Path, label: str
) -> str | None:
    """Capture a window screenshot to a file, return path or None."""
    try:
        from PIL import ImageGrab

        from windows_computer_use_mcp.win32_window import get_window_bbox

        left, top, right, bottom = get_window_bbox(window_handle)
        img = ImageGrab.grab(bbox=(left, top, right, bottom))
        path = output_dir / f"{label}.png"
        img.save(path)
        return str(path)
    except Exception as exc:
        logger.warning("Screenshot failed for %s: %s", label, exc)
        return None


def _crawl_operation(
    hwnd: int, hud
) -> dict[str, Any]:
    """Crawl UI tree and produce element map + screenshots."""
    from windows_computer_use_mcp.desktop_state.capture import DesktopStateCapture
    from windows_computer_use_mcp.win32_window import get_window_bbox

    out = Path.cwd() / "winapp_analysis"
    out.mkdir(exist_ok=True)

    if hud.estopped():
        return {"success": False, "error": "Crawl cancelled by user"}

    # AX element tree
    _ensure_focus(hwnd)
    capture = DesktopStateCapture(max_depth=5)
    ax_result = capture.capture(capture_mode="ax", window_handle=hwnd)
    elements = ax_result.get("elements", [])

    if hud.estopped():
        return {"success": False, "error": "Crawl cancelled by user"}

    # SOM annotated screenshot
    _ensure_focus(hwnd)
    som_result = capture.capture(capture_mode="som", window_handle=hwnd)
    som_screenshot_base64 = som_result.get("screenshot_base64")

    # Raw screenshot
    _ensure_focus(hwnd)
    raw_path = _screenshot_to_path(hwnd, out, "screenshot_raw")

    # Generate element map
    element_map = []
    for elem in elements:
        element_map.append(
            {
                "id": elem.get("id"),
                "type": elem.get("type"),
                "name": elem.get("name", ""),
                "bounds": elem.get("bounds"),
                "enabled": elem.get("enabled", True),
                "visible": elem.get("visible", True),
            }
        )

    # Markdown report
    window_rect = None
    try:
        window_rect = get_window_bbox(hwnd)
    except Exception:
        pass

    report_lines = [
        "# WinApp Analysis Report",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Window handle:** {hwnd}",
        f"**Window rect:** {window_rect}",
        f"**Elements found:** {len(elements)}",
        "",
        "## Element Map",
        "",
        "| # | Type | Name | x | y | w | h | Enabled | Visible |",
        "|---|------|------|---|--|--|--|---------|---------|",
    ]
    for i, e in enumerate(element_map):
        b = e.get("bounds", {})
        report_lines.append(
            f"| {i} | {e['type']} | {e['name'][:60]} | "
            f"{b.get('x','')} | {b.get('y','')} | {b.get('width','')} | "
            f"{b.get('height','')} | {e['enabled']} | {e['visible']} |"
        )

    report_text = "\n".join(report_lines)

    report_path = out / "analysis_report.md"
    report_path.write_text(report_text)

    return {
        "success": True,
        "window_handle": hwnd,
        "element_count": len(elements),
        "elements": element_map[:500],
        "screenshot_base64": som_screenshot_base64,
        "screenshot_path": raw_path,
        "report_path": str(report_path),
        "report_text": report_text,
        "output_dir": str(out),
    }


def _discover_operation(
    hwnd: int, hud
) -> dict[str, Any]:
    """Probe common keyboard shortcuts, capture state before/after each."""
    import pywinauto.keyboard as kb

    from windows_computer_use_mcp.desktop_state.capture import DesktopStateCapture

    out = Path.cwd() / "winapp_analysis"
    out.mkdir(exist_ok=True)

    shortcuts_to_try = [
        ("f1", "F1"),
        ("f5", "F5"),
        ("alt", "Alt (opens menu)"),
        ("ctrl+o", "Ctrl+O (open file)"),
        ("ctrl+s", "Ctrl+S (save)"),
        ("ctrl+p", "Ctrl+P (print)"),
        ("escape", "Escape"),
    ]

    capture = DesktopStateCapture()
    results = []

    # Baseline
    _ensure_focus(hwnd)
    if hud.estopped():
        return {"success": False, "error": "Discovery cancelled by user"}
    base_path = _screenshot_to_path(hwnd, out, "discover_baseline")
    results.append({"shortcut": "baseline", "screenshot": base_path})

    for key, label in shortcuts_to_try:
        if hud.estopped():
            return {"success": False, "error": "Discovery cancelled by user"}
        try:
            _ensure_focus(hwnd)
            kb.send_keys(key)
            time.sleep(0.5)
            _ensure_focus(hwnd)
            path = _screenshot_to_path(hwnd, out, f"discover_{key.replace('+','_')}")
            results.append({"shortcut": label, "key": key, "screenshot": path})

            if key == "alt":
                kb.send_keys("{ESCAPE}")
                time.sleep(0.3)
        except Exception as exc:
            logger.warning("Shortcut %s failed: %s", key, exc)

    _ensure_focus(hwnd)
    ax_result = capture.capture(capture_mode="ax", window_handle=hwnd)
    elements = ax_result.get("elements", [])

    report_lines = [
        "# WinApp Shortcut Discovery",
        "",
        f"**Generated:** {datetime.now().isoformat()}",
        f"**Window handle:** {hwnd}",
        f"**Shortcuts tested:** {len(results)}",
        f"**Elements found:** {len(elements)}",
        "",
        "## Shortcut Results",
        "",
        "| # | Shortcut | Screenshot |",
        "|---|----------|------------|",
    ]
    for i, r in enumerate(results):
        report_lines.append(
            f"| {i} | {r['shortcut']} | {r.get('screenshot', 'N/A')} |"
        )

    report_text = "\n".join(report_lines)
    report_path = out / "discovery_report.md"
    report_path.write_text(report_text)

    return {
        "success": True,
        "shortcuts_tested": len(results),
        "results": results,
        "element_count": len(elements),
        "report_path": str(report_path),
        "output_dir": str(out),
    }


def _portfolio_operation(
    hwnd: int, hud
) -> dict[str, Any]:
    """Capture multiple app states by name (uses hud for focus + estop)."""
    out = Path.cwd() / "winapp_analysis"
    out.mkdir(exist_ok=True)

    captures = []
    for state in (hud.states or ["main"]):
        if hud.estopped():
            return {"success": False, "error": "Portfolio cancelled by user"}
        _ensure_focus(hwnd)
        path = _screenshot_to_path(hwnd, out, f"state_{state}")
        captures.append({"state": state, "screenshot": path})

    return {
        "success": True,
        "window_handle": hwnd,
        "captures": captures,
        "output_dir": str(out),
    }


@app.tool()
def analyze_winapp(
    operation: Literal["crawl", "discover", "portfolio"] = "crawl",
    window_handle: int | None = None,
    window_title: str | None = None,
    output_dir: str | None = None,
    max_depth: int = 5,
    states: list[str] | None = None,
) -> dict[str, Any]:
    """Crawl a Windows app and produce UI element map + screenshot portfolio.

    Shows a "CUA at work" HUD overlay (blinking red) with an e-stop button
    during the operation. The target window is auto-refocused before each
    action to prevent focus stealers (Discord, Slack, etc.) from disrupting
    the crawl.

    Operations:
    - crawl: Walk the full UI tree, take SOM screenshot, generate element map + report.
    - discover: Probe common keyboard shortcuts (F1, F5, Ctrl+O, etc.) and
      capture the window state before/after each.
    - portfolio: Capture named states (e.g. ["main","dialog","settings"]).

    Args:
        operation: Which analysis operation to perform.
        window_handle: Target HWND (optional if window_title is set).
        window_title: Find window by title substring.
        output_dir: Directory for screenshot files + markdown report.
                    Defaults to ./winapp_analysis/
        max_depth: Max UI tree depth for crawl (default 5).
        states: State names for portfolio mode.

    Returns:
        {"success": bool, "element_count": int, "screenshot_path": str,
         "report_path": str, "report_text": str, ...}
    """
    from windows_computer_use_mcp.cua_hud import CuaHUD

    hud = CuaHUD()
    if states:
        hud.states = states
    hud.start()

    try:
        hwnd = window_handle
        if hwnd is None and window_title:
            try:
                import pygetwindow as gw
                wins = gw.getWindowsWithTitle(window_title)
                if wins:
                    hwnd = wins[0]._hWnd
            except Exception as exc:
                logger.warning("Window lookup failed: %s", exc)

        if hwnd is None:
            return {"success": False, "error": "No window specified or found"}

        hud.ensure_focus(hwnd)

        if operation == "crawl":
            return _crawl_operation(hwnd, hud)
        elif operation == "discover":
            return _discover_operation(hwnd, hud)
        elif operation == "portfolio":
            return _portfolio_operation(hwnd, hud)
        return {"success": False, "error": f"Unknown operation: {operation}"}
    finally:
        hud.stop()
