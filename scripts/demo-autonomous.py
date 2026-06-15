#!/usr/bin/env python3
"""Autonomous demo: uses the repo itself to showcase its own capabilities.

Run with: uv run python scripts/demo-autonomous.py
Record the screen with OBS / Windows Game Bar for a shareable video.
"""

import asyncio
import time
from typing import Any

from windows_computer_use_mcp.tools.models import ToolResult


async def _call(tool: str, **params) -> ToolResult:
    """Call an MCP tool by name, handling both sync and async tools."""
    import importlib
    import inspect
    mod = importlib.import_module(f"windows_computer_use_mcp.tools.portmanteau_{tool}")
    fn = None
    for name in dir(mod):
        if name.startswith("automation_") and callable(getattr(mod, name)):
            fn = getattr(mod, name)
            break
    if fn is None:
        raise RuntimeError(f"No tool found in portmanteau_{tool}")
    sig = inspect.signature(fn)
    is_async_fn = inspect.iscoroutinefunction(fn)
    request_type = None
    for p in sig.parameters.values():
        if hasattr(p.annotation, "model_validate"):
            request_type = p.annotation
            break
    if request_type:
        obj = request_type.model_validate(params)
        if is_async_fn:
            return await fn(obj)
        return await asyncio.to_thread(fn, obj)
    if is_async_fn:
        return await fn(**params)
    return await asyncio.to_thread(lambda: fn(**params))


def demo_phase(label: str):
    print("")
    print("=" * 60)
    print(f"  {label}")
    print("=" * 60)
    time.sleep(1)


async def main():
    print("")
    print("  WINDOWS COMPUTER USE - AUTONOMOUS DEMO")
    print("  The repo showcasing itself.")
    print("")

    # ── Phase 0: HITL approval ─────────────────────────────────────────
    demo_phase("Phase 0: Approve automation")
    print("  A HITL approval dialog should appear. Click 'Approve' to continue.")
    from windows_computer_use_mcp.app import approve_automation
    r = approve_automation(duration_minutes=5)
    print(f"  HITL approval: {r.get('status', '?')}")
    time.sleep(1)

    # ── Phase 1: Kill stale Notepad ────────────────────────────────────
    demo_phase("Phase 1: Kill stale Notepad instances")
    import psutil
    killed = 0
    for proc in psutil.process_iter(["name"]):
        try:
            if proc.info["name"] and proc.info["name"].lower() == "notepad.exe":
                proc.kill()
                killed += 1
        except Exception:
            pass
    print(f"  Killed {killed} stale Notepad(s)" if killed else "  No stale Notepad found")
    time.sleep(1)

    # ── Phase 2: Discover the desktop ──────────────────────────────────
    demo_phase("Phase 2: Discover running apps")
    r = await _call("smart", operation="list_apps")
    print(f"  Found {len(r.data.get('apps', []))} running apps:")
    for app in r.data.get("apps", [])[:5]:
        print(f"    - {app['app']} (handle={app['handle']})")
    time.sleep(1)

    # ── Phase 3: Open Notepad ──────────────────────────────────────────
    demo_phase("Phase 3: Open Notepad")
    r = await _call("system", operation="start_app", app_path="notepad.exe")
    print(f"  Notepad started (PID: {r.data.get('process_id', '?')})")
    time.sleep(2)

    # ── Phase 4: Find, maximize, and create new blank document ──────────
    demo_phase("Phase 4: Find and maximize Notepad window")
    r = await _call("windows", operation="find", title="Notepad")
    if r.status == "success":
        hwnd = r.data["windows"][0]["handle"]
        print(f"  Found Notepad (handle={hwnd})")
        await _call("windows", operation="maximize", handle=hwnd)
        print("  Maximized")
        # File > New to ensure a fresh blank document
        await _call("keyboard", operation="hotkey", keys=["alt", "f"])
        time.sleep(0.8)
        await _call("keyboard", operation="press", key="n")
        time.sleep(1.0)
        print("  New blank document created")
    else:
        print(f"  Window find: {r.message}")
        hwnd = None
    time.sleep(1)

    # ── Phase 5: Type text into Notepad ────────────────────────────────
    demo_phase("Phase 5: Type ASCII art cow herd")
    COWS = """         (__)              (__)              (__)
         (oo)              (oo)              (oo)
   /------\\/        /------\\/        /------\\/
  / |    ||        / |    ||        / |    ||
 *  /\\---/\\       *  /\\---/\\       *  /\\---/\\
    ~~   ~~            ~~   ~~            ~~   ~~
"A herd of cows,    "Automated by AI."  "100 installers,
 automated by AI."                        $2 in costs."
"""
    # Focus Notepad, click center of edit area via coordinates, paste clipboard
    await _call("windows", operation="focus", handle=hwnd)
    time.sleep(0.5)
    r = await _call("windows", operation="rect", handle=hwnd)
    if r.status == "success" and r.data:
        edit_x = r.data.get("left", 100) + 80
        edit_y = r.data.get("top", 100) + 100
        await _call("mouse", operation="click", x=edit_x, y=edit_y)
        time.sleep(0.3)
    await _call("system", operation="clipboard_set", text=COWS)
    time.sleep(0.2)
    await _call("keyboard", operation="hotkey", keys=["ctrl", "v"])
    print("  Cow herd pasted into Notepad")
    time.sleep(3)

    # ── Phase 6: Screenshot ────────────────────────────────────────────
    demo_phase("Phase 6: Screenshot")
    r = await _call("visual", operation="screenshot", window_handle=hwnd)
    print(f"  Screenshot taken")
    time.sleep(1)

    # ── Phase 7: OCR the Notepad edit area (crop out window chrome) ──
    demo_phase("Phase 7: OCR readback")
    r = await _call("visual", operation="extract_text", window_handle=hwnd,
        region_left=10, region_top=120, region_right=1900, region_bottom=1050)
    text = (r.data or {}).get("text", "") if r.data else ""
    ocr_preview = ""
    if text:
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        ocr_preview = "\n".join(lines[:5])
        print(f"  OCR read {len(lines)} lines")
    # Paste OCR result into Notepad so the viewer sees it
    ocr_output = f"\n--- OCR readback ---\n{ocr_preview if ocr_preview else '(no text detected)'}"
    await _call("system", operation="clipboard_set", text=ocr_output)
    time.sleep(0.2)
    await _call("keyboard", operation="hotkey", keys=["ctrl", "v"])
    time.sleep(1)
    # Final screenshot with OCR result visible
    await _call("visual", operation="screenshot", window_handle=hwnd)
    print("  Final screenshot with OCR result")
    time.sleep(2)

    # ── Phase 8: Close Notepad (don't save) ───────────────────────────
    demo_phase("Phase 8: Close Notepad")
    await _call("keyboard", operation="hotkey", keys=["alt", "f4"])
    time.sleep(1)
    # Don't Save via keyboard (Alt+N works on Win10/11, N is underlined in Don't Save)
    await _call("keyboard", operation="hotkey", keys=["alt", "n"])
    print("  Notepad closed")
    time.sleep(1)

    # ── Phase 9: Telemetry summary ─────────────────────────────────────
    demo_phase("Phase 9: Telemetry stats")
    r = await _call("system", operation="telemetry")
    stats = r.data.get("stats", {})
    print(f"  Total actions logged: {stats.get('total_actions', 0)}")
    by_tool = stats.get("by_tool", {})
    for key, val in list(by_tool.items())[:5]:
        print(f"    {key}: {val['total']} calls, {val['success']} OK")
    time.sleep(1)

    print("")
    print("=" * 60)
    print("  DEMO COMPLETE")
    print("  This entire sequence was driven by windows-computer-use-mcp")
    print("  using the same tools it exposes to AI agents.")
    print("=" * 60)
    print("")


if __name__ == "__main__":
    asyncio.run(main())
