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

    # Agentic canvas discovery: list elements, find the canvas by size
    r = await call("elements", operation="list", window_handle=hwnd, max_depth=2)
    canvas_rect = None
    if r.status == "success" and r.data:
        for elem in r.data.get("elements", []):
            rect = elem.get("rect") or {}
            ew = rect.get("width", 0)
            eh = rect.get("height", 0)
            # Canvas is the largest rectangular area (white drawing surface)
            if ew > 400 and eh > 300:
                canvas_rect = rect
                print(f"  Found canvas: ({rect.get('left')},{rect.get('top')}) {ew}x{eh}")
                break

    if not canvas_rect:
        # Fallback: use window center
        print("  Canvas not found via UIA, using window center")
        canvas_rect = {"left": left + 100, "top": top + 200, "width": width - 200, "height": 600}

    cx = canvas_rect["left"] + canvas_rect["width"] // 2
    cy = canvas_rect["top"] + canvas_rect["height"] // 2
    canvas_ox = cx
    canvas_oy = cy
    # Click the canvas to ensure it's active
    phase("Click canvas center")
    await call("mouse", operation="click", x=cx, y=cy)
    print(f"  Canvas center at ({cx}, {cy})")
    time.sleep(0.3)

    import math
    dy = 80
    S = 2

    # ── BICYCLE ──
    phase("Bicycle frame + wheels")
    bw_x, bw_y = cx - 60 * S, cy + 30 * S + dy
    fw_x, fw_y = cx + 60 * S, cy + 30 * S + dy
    seat_x, seat_y = cx - 40 * S, cy - 15 * S + dy
    bar_x, bar_y = cx + 35 * S, cy - 25 * S + dy
    pedal_x, pedal_y = cx, cy + 30 * S + dy

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

    # Wheels (24 segments for smooth circles)
    phase("Wheels")
    for hx, hy in [(bw_x, bw_y), (fw_x, fw_y)]:
        r = 28 * S
        for i in range(24):
            a1 = 2 * math.pi * i / 24
            a2 = 2 * math.pi * (i + 1) / 24
            await call("mouse", operation="drag",
                x=int(hx + r * math.cos(a1)), y=int(hy + r * math.sin(a1)),
                x2=int(hx + r * math.cos(a2)), y2=int(hy + r * math.sin(a2)))
            time.sleep(0.015)
        for i in range(8):
            a = 2 * math.pi * i / 8
            await call("mouse", operation="drag",
                x=int(hx + r * 0.1 * math.cos(a)), y=int(hy + r * 0.1 * math.sin(a)),
                x2=int(hx + r * math.cos(a)), y2=int(hy + r * math.sin(a)))
            time.sleep(0.015)
        # Tire outline (slightly larger)
        tr = r + 3 * S
        for i in range(24):
            a1 = 2 * math.pi * i / 24
            a2 = 2 * math.pi * (i + 1) / 24
            await call("mouse", operation="drag",
                x=int(hx + tr * math.cos(a1)), y=int(hy + tr * math.sin(a1)),
                x2=int(hx + tr * math.cos(a2)), y2=int(hy + tr * math.sin(a2)))
            time.sleep(0.01)

    # Pedals
    phase("Pedals")
    for dx in [-8 * S, 8 * S]:
        pr = 3 * S
        for i in range(10):
            a1 = 2 * math.pi * i / 10
            a2 = 2 * math.pi * (i + 1) / 10
            await call("mouse", operation="drag",
                x=int(pedal_x + dx + pr * math.cos(a1)), y=int(pedal_y + pr * math.sin(a1)),
                x2=int(pedal_x + dx + pr * math.cos(a2)), y2=int(pedal_y + pr * math.sin(a2)))
            time.sleep(0.01)

    # ── PELICAN BODY (smooth oval, tilted) ──
    phase("Pelican body")
    bx, by = cx - 15 * S, cy - 40 * S + dy
    rw, rh = 32 * S, 22 * S
    for i in range(24):
        a1 = 2 * math.pi * i / 24
        a2 = 2 * math.pi * (i + 1) / 24
        await call("mouse", operation="drag",
            x=int(bx + rw * math.cos(a1)), y=int(by + rh * math.sin(a1)),
            x2=int(bx + rw * math.cos(a2)), y2=int(by + rh * math.sin(a2)))
        time.sleep(0.015)

    # Wing
    phase("Wing")
    wx1, wy1 = bx + 5 * S, by - 10 * S
    wx2, wy2 = bx - 20 * S, by - 25 * S
    wx3, wy3 = bx - 25 * S, by
    await call("mouse", operation="drag", x=wx1, y=wy1, x2=wx2, y2=wy2)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=wx2, y=wy2, x2=wx3, y2=wy3)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=wx3, y=wy3, x2=wx1, y2=wy1)
    time.sleep(0.1)

    # Tail feathers
    phase("Tail")
    tx, ty = bx - rw, by + 5 * S
    await call("mouse", operation="drag", x=tx, y=ty, x2=tx - 12 * S, y2=ty - 5 * S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=tx, y=ty, x2=tx - 12 * S, y2=ty + 5 * S)
    time.sleep(0.1)

    # ── HEAD + NECK ──
    phase("Head")
    hx, hy = bx + 25 * S, by - 22 * S
    hr = 11 * S
    # Neck
    await call("mouse", operation="drag", x=bx + 20 * S, y=by - 15 * S, x2=hx - 5 * S, y2=hy + 5 * S)
    time.sleep(0.1)
    # Head circle
    for i in range(16):
        a1 = 2 * math.pi * i / 16
        a2 = 2 * math.pi * (i + 1) / 16
        await call("mouse", operation="drag",
            x=int(hx + hr * math.cos(a1)), y=int(hy + hr * math.sin(a1)),
            x2=int(hx + hr * math.cos(a2)), y2=int(hy + hr * math.sin(a2)))
        time.sleep(0.015)

    # ── BEAK ──
    phase("Beak")
    # Upper beak
    await call("mouse", operation="drag", x=hx + hr, y=hy, x2=hx + 50 * S, y2=hy - 4 * S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=hx + 50 * S, y=hy - 4 * S, x2=hx + 52 * S, y2=hy + 6 * S)
    time.sleep(0.1)
    # Hook at tip
    await call("mouse", operation="drag", x=hx + 52 * S, y=hy + 6 * S, x2=hx + 45 * S, y2=hy + 10 * S)
    time.sleep(0.1)
    # Pouch
    await call("mouse", operation="drag", x=hx + 45 * S, y=hy + 10 * S, x2=hx + 12 * S, y2=hy + 12 * S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=hx + 12 * S, y=hy + 12 * S, x2=hx + 8 * S, y2=hy + 18 * S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=hx + 8 * S, y=hy + 18 * S, x2=hx + hr - 2 * S, y2=hy + 5 * S)
    time.sleep(0.1)

    # Eye
    await call("mouse", operation="click", x=hx + 4 * S, y=hy - 3 * S)
    time.sleep(0.1)

    # ── LEGS (jointed: thigh + calf) ──
    phase("Legs")
    # Front leg
    knee_x = bx + 5 * S
    knee_y = by + rh + 15 * S
    await call("mouse", operation="drag", x=bx + 8 * S, y=by + rh, x2=knee_x, y2=knee_y)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=knee_x, y=knee_y, x2=pedal_x + 8 * S, y2=pedal_y)
    time.sleep(0.1)
    # Back leg
    knee2_x = bx - 10 * S
    knee2_y = by + rh + 15 * S
    await call("mouse", operation="drag", x=bx - 8 * S, y=by + rh, x2=knee2_x, y2=knee2_y)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=knee2_x, y=knee2_y, x2=pedal_x - 8 * S, y2=pedal_y)
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
