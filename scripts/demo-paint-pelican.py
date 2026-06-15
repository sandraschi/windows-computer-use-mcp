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
    try:
        import importlib, inspect
        mod = importlib.import_module(f"windows_computer_use_mcp.tools.portmanteau_{tool}")
        fn = None
        for name in dir(mod):
            if name.startswith("automation_") and callable(getattr(mod, name)):
                fn = getattr(mod, name)
                break
        if fn is None:
            return ToolResult(status="error", message=f"Tool not found: {tool}")
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
    except Exception as e:
        import traceback
        print(f"  [call error] {tool}({params}): {e}")
        traceback.print_exc()
        return ToolResult(status="error", message=f"call({tool}) failed: {e}")


def phase(label: str):
    print(f"\n=== {label} ===")
    time.sleep(1)


async def main():
    # Open Paint
    phase("Open Paint")
    import subprocess
    try:
        subprocess.Popen("start mspaint", shell=True)
        print(f"  Paint launched")
    except Exception as e:
        print(f"  Paint launch failed: {e}")
        return
    time.sleep(4)

    # Find and maximize
    phase("Find and maximize Paint")
    r = await call("windows", operation="find", title="Paint")
    if r.status != "success" or not r.data.get("windows"):
        r = await call("windows", operation="find", title="untitled")
    if r.status != "success" or not r.data.get("windows"):
        print("  Paint window not found!")
        print(f"  Last error: {r.message}")
        return
    hwnd = r.data["windows"][0]["handle"]
    print(f"  Handle: {hwnd}")
    await call("windows", operation="maximize", handle=hwnd)
    time.sleep(1)

    # Get window position
    r = await call("windows", operation="rect", handle=hwnd)
    left = r.data.get("left", 0)
    top = r.data.get("top", 0)
    width = r.data.get("width", 1920)
    print(f"  Window: left={left} top={top} width={width}")

    # Focus the window
    phase("Find canvas via UIA")
    await call("windows", operation="focus", handle=hwnd)
    time.sleep(0.5)

    # Use safe absolute coordinates for the white canvas area
    # Default Paint canvas is ~800x600 centered in the maximized window
    cx = 960    # screen center X  
    cy = 500    # below ribbon, within white canvas
    canvas_ox = cx
    canvas_oy = cy
    phase("Click canvas center")
    await call("mouse", operation="click", x=cx, y=cy)
    print(f"  Drawing center at ({cx}, {cy})")
    time.sleep(0.3)

    import math
    S = 3

    # ── BICYCLE ──
    phase("Bicycle frame + wheels")
    bw_x, bw_y = cx - 60 * S, cy + 30 * S 
    fw_x, fw_y = cx + 60 * S, cy + 30 * S 
    seat_x, seat_y = cx - 40 * S, cy - 15 * S 
    bar_x, bar_y = cx + 35 * S, cy - 25 * S 
    pedal_x, pedal_y = cx, cy + 30 * S 

    # Frame
    await call("mouse", operation="drag", x=seat_x, y=seat_y, x2=pedal_x, y2=pedal_y)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=pedal_x, y=pedal_y, x2=bar_x, y2=bar_y)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=bar_x, y=bar_y, x2=seat_x, y2=seat_y)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=pedal_x, y=pedal_y, x2=bw_x, y2=bw_y)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=pedal_x, y=pedal_y, x2=fw_x, y2=fw_y)
    time.sleep(0.15)
    # Seat post
    await call("mouse", operation="drag", x=seat_x, y=seat_y, x2=seat_x, y2=seat_y + 10 * S)
    time.sleep(0.1)

    # Wheels (circle: 4 long arcs instead of 24 tiny segments)
    phase("Wheels")
    for hx, hy in [(bw_x, bw_y), (fw_x, fw_y)]:
        r = 28 * S
        for i in range(4):  # 4 big arcs
            a1 = 2 * math.pi * i / 4
            a2 = 2 * math.pi * (i + 1) / 4
            await call("mouse", operation="drag",
                x=int(hx + r * math.cos(a1)), y=int(hy + r * math.sin(a1)),
                x2=int(hx + r * math.cos(a2)), y2=int(hy + r * math.sin(a2)))
            time.sleep(0.05)

    # ── PELICAN (simple recognizable shape, bold strokes) ──
    phase("Pelican")
    bx, by = cx - 20 * S, cy - 50 * S  # body center

    # Body outline (oval, 8 segments)
    for i in range(8):
        a1 = 2 * math.pi * i / 8
        a2 = 2 * math.pi * (i + 1) / 8
        await call("mouse", operation="drag",
            x=int(bx + 30 * S * math.cos(a1)), y=int(by + 20 * S * math.sin(a1)),
            x2=int(bx + 30 * S * math.cos(a2)), y2=int(by + 20 * S * math.sin(a2)))
        time.sleep(0.05)

    # Neck + head
    hx, hy = bx + 28 * S, by - 25 * S  # head center
    await call("mouse", operation="drag", x=bx + 20 * S, y=by - 15 * S, x2=hx, y2=hy)
    time.sleep(0.1)
    # Head (circle, 6 segments)
    for i in range(6):
        a1 = 2 * math.pi * i / 6
        a2 = 2 * math.pi * (i + 1) / 6
        await call("mouse", operation="drag",
            x=int(hx + 10 * S * math.cos(a1)), y=int(hy + 10 * S * math.sin(a1)),
            x2=int(hx + 10 * S * math.cos(a2)), y2=int(hy + 10 * S * math.sin(a2)))
        time.sleep(0.05)

    # Beak (long, recognizable)
    await call("mouse", operation="drag", x=hx + 10 * S, y=hy, x2=hx + 50 * S, y2=hy - 5 * S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=hx + 50 * S, y=hy - 5 * S, x2=hx + 50 * S, y2=hy + 10 * S)
    time.sleep(0.1)
    # Pouch
    await call("mouse", operation="drag", x=hx + 50 * S, y=hy + 10 * S, x2=hx + 5 * S, y2=hy + 10 * S)
    time.sleep(0.1)

    # Legs (simple, straight)
    await call("mouse", operation="drag", x=bx - 10 * S, y=by + 20 * S, x2=pedal_x - 10 * S, y2=pedal_y)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=bx + 10 * S, y=by + 20 * S, x2=pedal_x + 10 * S, y2=pedal_y)
    time.sleep(0.1)

    # Wing (simple triangle)
    await call("mouse", operation="drag", x=bx + 5 * S, y=by - 10 * S, x2=bx - 25 * S, y2=by - 15 * S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=bx - 25 * S, y=by - 15 * S, x2=bx - 20 * S, y2=by + 5 * S)
    time.sleep(0.1)
    time.sleep(0.1)

    # ── HANDLEBARS ──
    phase("Handlebars")
    await call("mouse", operation="drag", x=bar_x - 12 * S, y=bar_y, x2=bar_x + 12 * S, y2=bar_y)
    time.sleep(0.1)
    # Grips
    await call("mouse", operation="drag", x=bar_x - 14 * S, y=bar_y - 2 * S, x2=bar_x - 12 * S, y2=bar_y + 2 * S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=bar_x + 12 * S, y=bar_y - 2 * S, x2=bar_x + 14 * S, y2=bar_y + 2 * S)
    time.sleep(0.1)

    # ── Screenshot ──
    phase("Screenshot")
    r = await call("visual", operation="screenshot", window_handle=hwnd)
    print(f"  Screenshot taken")

    # ── Keep on screen for viewing ──
    print("\n*** Pelican on a bike! Ready for recording. Closing in 10 seconds... ***")
    time.sleep(10)

    # Close without saving
    await call("keyboard", operation="hotkey", keys=["alt", "f4"])
    time.sleep(0.5)
    await call("keyboard", operation="press", key="enter")
    print("  Paint closed")


if __name__ == "__main__":
    asyncio.run(main())
