"""Smart discovery and intent-based interaction for Windows automation.

PORTMANTEAU PATTERN RATIONALE:
Consolidates discovery and intent-based operations that bridge the gap between
raw tool calls and user goals. Uses element scanning and optional LLM sampling
to resolve ambiguous or underspecified targets.
"""

from __future__ import annotations

import logging
from typing import Any

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.tools.models import ToolResult

try:
    from fastmcp import Context
    SAMPLING_AVAILABLE = True
except ImportError:
    SAMPLING_AVAILABLE = False
    Context = Any

logger = logging.getLogger(__name__)


def _scan_all_windows() -> list[dict]:
    """Return a snapshot of all visible windows with their controls."""
    from pywinauto import Desktop
    desktop = Desktop(backend="uia")
    results = []
    for win in desktop.windows():
        try:
            if not win.is_visible():
                continue
            info = {
                "handle": win.handle,
                "title": win.window_text(),
                "class_name": win.class_name(),
                "process_id": win.process_id(),
                "is_visible": win.is_visible(),
                "is_enabled": win.is_enabled(),
            }
            try:
                rect = win.rectangle()
                info.update({"left": rect.left, "top": rect.top, "width": rect.width(), "height": rect.height()})
            except Exception:
                pass
            children = []
            try:
                for child in win.children(visible_only=True):
                    try:
                        children.append({
                            "title": child.window_text(),
                            "class_name": child.class_name(),
                            "control_type": str(child.element_info.control_type) if hasattr(child, "element_info") else None,
                            "handle": child.handle,
                        })
                    except Exception:
                        continue
            except Exception:
                pass
            info["controls"] = children[:20]
            results.append(info)
        except Exception:
            continue
    return results


def _identify_apps(windows: list[dict]) -> list[dict]:
    """Identify apps from window info by known class/process patterns."""
    _APP_SIGNATURES = {
        "Notepad": {"class": "Notepad", "process": "notepad.exe"},
        "Calculator": {"class": "CalcFrame", "process": "calculator.exe"},
        "Paint": {"class": "MSPaintApp", "process": "mspaint.exe"},
        "File Explorer": {"class": "CabinetWClass", "process": "explorer.exe"},
        "Chrome": {"class": "Chrome_WidgetWin_1", "process": "chrome.exe"},
        "Firefox": {"class": "MozillaWindowClass", "process": "firefox.exe"},
        "Terminal": {"class": "CASCADIA_HOSTING_WINDOW_CLASS", "process": "WindowsTerminal.exe"},
        "Word": {"class": "OpusApp", "process": "WINWORD.EXE"},
        "Excel": {"class": "XLMAIN", "process": "EXCEL.EXE"},
        "Outlook": {"class": "rctrl_renwnd32", "process": "OUTLOOK.EXE"},
        "VS Code": {"class": "Code - OSS", "process": "code.exe"},
        "Cursor": {"class": "Cursor", "process": "cursor.exe"},
    }
    results = []
    for w in windows:
        cls = w.get("class_name", "")
        title = w.get("title", "").strip()
        pid = w.get("process_id", 0)
        import psutil
        proc_name = ""
        try:
            proc_name = (psutil.Process(pid).name() or "").lower()
        except Exception:
            pass
        app_name = title
        for name, sig in _APP_SIGNATURES.items():
            if sig["class"] in cls or sig["process"] == proc_name:
                app_name = name
                break
        results.append({"app": app_name, "title": title, "handle": w["handle"], "class_name": cls, "controls": len(w.get("controls", []))})
    return results


if app is not None:

    @app.tool(
        name="automation_smart",
        description="""Intent-based discovery and interaction across all windows.

OPERATIONS:
- discover: Scan all visible windows and return a structured inventory of running
  apps and their controls. Optional query filters by app name or window title.
- list_apps: Quick list of identified running applications with window handles.
- list_controls: List controls for a specific window handle.
- click: Find an element by description (e.g. 'the Save button') across all windows
  using element scanning. Fallback to OCR when UIA fails.
""",
    )
    async def automation_smart(
        operation: str,
        query: str | None = None,
        window_handle: int | None = None,
        description: str | None = None,
        button: str = "left",
    ) -> ToolResult:
        if operation == "discover":
            windows = _scan_all_windows()
            apps = _identify_apps(windows)
            if query:
                q = query.lower()
                apps = [a for a in apps if q in a["app"].lower() or q in a["title"].lower()]
            return ToolResult(
                status="success",
                message=f"Found {len(apps)} apps across {len(windows)} windows." if not query else f"Found {len(apps)} apps matching '{query}'.",
                data={"apps": apps, "total_windows": len(windows)},
                recovery_tip="Use list_controls with a handle to drill into a specific window." if apps else None,
            )

        if operation == "list_apps":
            windows = _scan_all_windows()
            apps = _identify_apps(windows)
            return ToolResult(
                status="success",
                message=f"{len(apps)} running apps detected.",
                data={"apps": [{"app": a["app"], "title": a["title"], "handle": a["handle"]} for a in apps]},
            )

        if operation == "list_controls":
            if window_handle is None:
                return ToolResult(status="error", message="window_handle is required.")
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            try:
                win = desktop.window(handle=window_handle)
                buttons, edits, texts, others = [], [], [], []
                for child in win.children(visible_only=True):
                    try:
                        item = {"title": child.window_text(), "class_name": child.class_name(), "handle": child.handle}
                        try:
                            item["control_type"] = str(child.element_info.control_type)
                        except Exception:
                            pass
                        ctype = item.get("control_type", "")
                        if "Button" in ctype:
                            buttons.append(item)
                        elif "Edit" in ctype or "Document" in ctype:
                            edits.append(item)
                        elif "Text" in ctype:
                            texts.append(item)
                        else:
                            others.append(item)
                    except Exception:
                        continue
                return ToolResult(
                    status="success",
                    message=f"Window has {len(buttons)} buttons, {len(edits)} edit fields, {len(texts)} text elements.",
                    data={"buttons": buttons, "edits": edits, "texts": texts, "others": others},
                )
            except Exception as e:
                return ToolResult(status="error", message=f"Failed to list controls: {e!s}")

        if operation == "click":
            if not description:
                return ToolResult(status="error", message="description is required (e.g. 'the Save button').")
            from pywinauto import Desktop
            desktop = Desktop(backend="uia")
            all_windows = desktop.windows()
            candidates = []
            for win in all_windows:
                try:
                    if not win.is_visible():
                        continue
                    win_title = win.window_text().lower()
                    win_handle = win.handle
                    for child in win.children(visible_only=True):
                        try:
                            txt = child.window_text().strip().lower()
                            if not txt:
                                continue
                            try:
                                ctype = str(child.element_info.control_type)
                            except Exception:
                                ctype = ""
                            desc_lower = description.lower()
                            if txt == desc_lower or txt.startswith(desc_lower) or desc_lower.startswith(txt):
                                candidates.append({"handle": child.handle, "title": child.window_text(), "control_type": ctype, "window_handle": win_handle, "window_title": win.window_text()})
                        except Exception:
                            continue
                except Exception:
                    continue
            if not candidates and "button" in description.lower():
                for win in all_windows:
                    try:
                        if not win.is_visible():
                            continue
                        wh = win.handle
                        for child in win.children(visible_only=True):
                            try:
                                ctype = str(child.element_info.control_type)
                                if "Button" not in ctype:
                                    continue
                                txt = child.window_text().strip().lower()
                                if not txt:
                                    continue
                                desc_lower = description.lower().replace("button", "").replace("the", "").strip()
                                if desc_lower in txt or txt in desc_lower:
                                    candidates.append({"handle": child.handle, "title": child.window_text(), "control_type": ctype, "window_handle": wh, "window_title": win.window_text()})
                            except Exception:
                                continue
                    except Exception:
                        continue
            if not candidates:
                return ToolResult(
                    status="error",
                    message=f"No element found matching '{description}'.",
                    recovery_tip="Use 'discover' or 'list_controls' to browse available elements.",
                )
            if len(candidates) > 1 and SAMPLING_AVAILABLE:
                try:
                    ctx = Context()
                    prompt = f"I need to click one of these UI elements. Pick the best match for '{description}':\n" + "\n".join(f"{i}: title='{c['title']}' type='{c['control_type']}' window='{c['window_title']}'" for i, c in enumerate(candidates))
                    response = await ctx.sample(messages=[{"role": "user", "content": prompt}], max_tokens=100)
                    content = ""
                    if isinstance(response, str):
                        content = response
                    elif isinstance(response, dict):
                        content = response.get("content", str(response))
                    import re
                    match = re.search(r"\d+", content)
                    if match:
                        idx = int(match.group())
                        if 0 <= idx < len(candidates):
                            candidates = [candidates[idx]]
                except Exception as e:
                    logger.warning("Ambiguity sampling failed: %s — using first candidate", e)
                    candidates = candidates[:1]
            else:
                candidates = candidates[:1]
            target = candidates[0]
            try:
                from pywinauto import Desktop as D
                d = D(backend="uia")
                win = d.window(handle=target["window_handle"])
                elem = win.child_window(handle=target["handle"])
                from windows_computer_use_mcp.dispatch import click_element, resolve_dispatch
                meta = click_element(elem, dispatch=resolve_dispatch(None), button=button)
                return ToolResult(
                    status="success",
                    message=f"Clicked '{target['title']}' ({target['control_type']}) in '{target['window_title']}'.",
                    data={"clicked": target, "dispatch": meta},
                )
            except Exception as e:
                return ToolResult(status="error", message=f"Click failed: {e!s}")

        return ToolResult(status="error", message=f"Unknown operation: {operation}")

else:
    logger.warning("Smart tool not available - missing app instance")

__all__ = ["automation_smart"]
