#!/usr/bin/env python3
"""Paint a pelican riding a bicycle in MS Paint, fully autonomous.

Run with: uv run python scripts/demo-paint-pelican.py
Record the screen with Win+Alt+R for demo footage.
"""

import os
import sys
import time

os.environ["WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import asyncio
from windows_computer_use_mcp.tools.models import ToolResult


async def call(tool: str, **params) -> ToolResult:
    import importlib, inspect
    mod = importlib.import_module(f"windows_computer_use_mcp.tools.portmanteau_{tool}")
    fn = None
    for name in dir(mod):
        if name.startswith("automation_") and callable(getattr(mod, name)):
            fn = getattr(mod, name)
            break
    sig = inspect.signature(fn)
    is_async = inspect.iscoroutinefunction(fn)
    request_type = None
    for p in sig.parameters.values():
        if hasattr(p.annotation, "model_validate"):
            request_type = p.annotation
            break
    if request_type:
        obj = request_type.model_validate(params)
        return await fn(obj) if is_async else fn(obj)
    return await fn(**params) if is_async else fn(**params)


def phase(label: str):
    print(f"\n=== {label} ===")
    time.sleep(1)


async def main():
    # Open Paint
    phase("Open Paint")
    r = await call("system", operation="start_app", app_path="mspaint.exe")
    print(f"  Paint started")
    time.sleep(3)

    # Find and maximize
    phase("Find and maximize Paint")
    r = await call("windows", operation="find", title="Paint")
    if r.status != "success" or not r.data.get("windows"):
        r = await call("windows", operation="find", title="paint")
    if r.status != "success" or not r.data.get("windows"):
        r = await call("windows", operation="find", title="untitled")
    if r.status != "success" or not r.data.get("windows"):
        print("  Paint window not found!")
        return
    hwnd = r.data["windows"][0]["handle"]
    print(f"  Handle: {hwnd}")
    await call("windows", operation="maximize", handle=hwnd)
    time.sleep(1)

    # Get window position
    r = await call("windows", operation="rect", handle=hwnd)
    left = r.data.get("left", 0)
    top = r.data.get("top", 0)
    print(f"  Window: left={left} top={top}")

    # Focus and click canvas to ensure we're in drawing mode
    phase("Focus canvas")
    await call("windows", operation="focus", handle=hwnd)
    time.sleep(0.5)
    cx = left + 400  # canvas center-ish
    cy = top + 350

    # ── Draw bicycle back wheel ──
    phase("Draw back wheel")
    await call("mouse", operation="click", x=cx - 60, y=cy + 80)
    time.sleep(0.3)
    # Draw a circle-ish shape with drag
    await call("mouse", operation="click", x=cx - 60, y=cy + 80)
    time.sleep(0.1)

    # ── Draw bicycle front wheel ──
    phase("Draw front wheel")
    await call("mouse", operation="click", x=cx + 60, y=cy + 80)
    time.sleep(0.1)

    # ── Draw bike frame ──
    phase("Draw bike frame")
    # bottom tube: back wheel center to front wheel center
    await call("mouse", operation="drag", x=cx - 60, y=cy + 80, x2=cx + 60, y2=cy + 80)
    time.sleep(0.2)
    # seat tube: back wheel up to seat
    await call("mouse", operation="drag", x=cx - 60, y=cy + 80, x2=cx - 50, y2=cy)
    time.sleep(0.2)
    # top tube: seat to handlebars
    await call("mouse", operation="drag", x=cx - 50, y=cy, x2=cx + 50, y2=cy - 10)
    time.sleep(0.2)
    # head tube: handlebars down to front wheel
    await call("mouse", operation="drag", x=cx + 50, y=cy - 10, x2=cx + 60, y2=cy + 80)
    time.sleep(0.2)

    # ── Draw pelican body ──
    phase("Draw pelican body")
    # Oval body using short drag strokes
    await call("mouse", operation="drag", x=cx - 40, y=cy - 50, x2=cx - 10, y2=cy - 80)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=cx - 10, y=cy - 80, x2=cx + 20, y2=cy - 60)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=cx + 20, y=cy - 60, x2=cx + 10, y2=cy - 35)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=cx + 10, y=cy - 35, x2=cx - 40, y2=cy - 50)
    time.sleep(0.15)

    # ── Draw pelican head ──
    phase("Draw head")
    await call("mouse", operation="drag", x=cx - 30, y=cy - 90, x2=cx - 20, y2=cy - 105)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=cx - 20, y=cy - 105, x2=cx, y2=cy - 100)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=cx, y=cy - 100, x2=cx - 5, y2=cy - 85)
    time.sleep(0.1)

    # ── Draw pelican beak (long!) ──
    phase("Draw beak")
    await call("mouse", operation="drag", x=cx - 20, y=cy - 95, x2=cx + 40, y2=cy - 100)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=cx + 40, y=cy - 100, x2=cx + 35, y2=cy - 90)
    time.sleep(0.1)

    # ── Draw legs to pedals ──
    phase("Draw legs")
    await call("mouse", operation="drag", x=cx - 30, y=cy - 45, x2=cx - 50, y2=cy + 40)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=cx - 10, y=cy - 45, x2=cx, y2=cy + 40)
    time.sleep(0.15)

    # ── Draw wheel spokes ──
    phase("Draw spokes")
    for wx, wy in [(cx - 60, cy + 80), (cx + 60, cy + 80)]:
        for dx, dy in [(0, -20), (0, 20), (-20, 0), (20, 0), (-15, -15), (15, 15)]:
            await call("mouse", operation="drag", x=wx, y=wy, x2=wx + dx, y2=wy + dy)
            time.sleep(0.05)

    # ── Screenshot ──
    phase("Screenshot")
    r = await call("visual", operation="screenshot", window_handle=hwnd)
    print(f"  Screenshot taken")

    # ── Keep on screen for viewing ──
    print("\n🎨 Pelican on a bike! Ready for recording. Closing in 10 seconds...")
    time.sleep(10)

    # Close without saving
    await call("keyboard", operation="hotkey", keys=["alt", "f4"])
    time.sleep(0.5)
    await call("keyboard", operation="press", key="enter")
    print("  Paint closed")


if __name__ == "__main__":
    asyncio.run(main())
