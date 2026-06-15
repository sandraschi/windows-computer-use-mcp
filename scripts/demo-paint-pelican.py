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
    import subprocess
    subprocess.Popen("start mspaint", shell=True)
    print(f"  Paint launched")
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

    S = 3  # scale factor — everything 3x bigger

    # ── Select thicker brush: click Size button in ribbon, then size 3 ──
    # In Paint, brush size can be changed via Home tab > Size > 5px
    # Click the Size dropdown area (roughly at ribbon position)
    await call("mouse", operation="click", x=canvas_ox - 300, y=canvas_oy - 200)
    time.sleep(0.3)
    await call("mouse", operation="click", x=canvas_ox - 300, y=canvas_oy - 180)
    time.sleep(0.3)

    # ── Draw bicycle frame (triangle) ──
    phase("Draw bike frame")
    bw_x, bw_y = cx - 80 * S, cy + 40 * S  # back wheel hub
    fw_x, fw_y = cx + 80 * S, cy + 40 * S  # front wheel hub
    seat_x, seat_y = cx - 60 * S, cy - 20 * S  # seat
    bar_x, bar_y = cx + 50 * S, cy - 30 * S  # handlebars
    pedal_x, pedal_y = cx, cy + 40 * S  # bottom bracket

    await call("mouse", operation="drag", x=seat_x, y=seat_y, x2=pedal_x, y2=pedal_y)
    time.sleep(0.2)
    await call("mouse", operation="drag", x=pedal_x, y=pedal_y, x2=bar_x, y2=bar_y)
    time.sleep(0.2)
    await call("mouse", operation="drag", x=bar_x, y=bar_y, x2=seat_x, y2=seat_y)
    time.sleep(0.2)
    await call("mouse", operation="drag", x=pedal_x, y=pedal_y, x2=bw_x, y2=bw_y)
    time.sleep(0.2)
    await call("mouse", operation="drag", x=pedal_x, y=pedal_y, x2=fw_x, y2=fw_y)
    time.sleep(0.2)

    # ── Draw wheels (many short strokes in a circle) ──
    phase("Draw wheels")
    import math
    for label, hx, hy in [("Back", bw_x, bw_y), ("Front", fw_x, fw_y)]:
        r = 40 * S  # wheel radius
        pts = 24  # points for a smooth circle
        for i in range(pts):
            a1 = 2 * math.pi * i / pts
            a2 = 2 * math.pi * (i + 1) / pts
            x1 = int(hx + r * math.cos(a1))
            y1 = int(hy + r * math.sin(a1))
            x2 = int(hx + r * math.cos(a2))
            y2 = int(hy + r * math.sin(a2))
            await call("mouse", operation="drag", x=x1, y=y1, x2=x2, y2=y2)
            time.sleep(0.02)
        # Spokes
        for i in range(8):
            a = 2 * math.pi * i / 8
            sx = int(hx + r * 0.1 * math.cos(a))
            sy = int(hy + r * 0.1 * math.sin(a))
            ex = int(hx + r * math.cos(a))
            ey = int(hy + r * math.sin(a))
            await call("mouse", operation="drag", x=sx, y=sy, x2=ex, y2=ey)
            time.sleep(0.02)

    # ── Draw pelican body (big oval) ──
    phase("Draw pelican body")
    bx, by = cx - 30 * S, cy - 60 * S  # body center (behind handlebars, above frame)
    pts = 20
    rw, rh = 45 * S, 30 * S  # body ellipse radii
    for i in range(pts):
        a1 = 2 * math.pi * i / pts
        a2 = 2 * math.pi * (i + 1) / pts
        x1 = int(bx + rw * math.cos(a1))
        y1 = int(by + rh * math.sin(a1))
        x2 = int(bx + rw * math.cos(a2))
        y2 = int(by + rh * math.sin(a2))
        await call("mouse", operation="drag", x=x1, y=y1, x2=x2, y2=y2)
        time.sleep(0.02)

    # ── Draw pelican head ──
    phase("Draw head")
    hx, hy = bx + 40 * S, by - 25 * S  # head center (forward of body)
    hr = 15 * S
    for i in range(16):
        a1 = 2 * math.pi * i / 16
        a2 = 2 * math.pi * (i + 1) / 16
        x1 = int(hx + hr * math.cos(a1))
        y1 = int(hy + hr * math.sin(a1))
        x2 = int(hx + hr * math.cos(a2))
        y2 = int(hy + hr * math.sin(a2))
        await call("mouse", operation="drag", x=x1, y=y1, x2=x2, y2=y2)
        time.sleep(0.02)

    # ── Draw pelican beak (long and distinctive!) ──
    phase("Draw beak")
    # Upper beak from head extending forward
    await call("mouse", operation="drag", x=hx + hr, y=hy, x2=hx + 70 * S, y2=hy - 5 * S)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=hx + 70 * S, y=hy - 5 * S, x2=hx + 70 * S, y2=hy + 10 * S)
    time.sleep(0.15)
    # Lower beak (pouch)
    await call("mouse", operation="drag", x=hx + 70 * S, y=hy + 10 * S, x2=hx + 20 * S, y2=hy + 15 * S)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=hx + 20 * S, y=hy + 15 * S, x2=hx + hr, y2=hy + 5 * S)
    time.sleep(0.15)

    # ── Draw eye ──
    phase("Draw eye")
    await call("mouse", operation="click", x=hx + 5 * S, y=hy - 5 * S)
    time.sleep(0.1)

    # ── Draw legs to pedals ──
    phase("Draw legs")
    await call("mouse", operation="drag", x=bx - 10 * S, y=by + rh, x2=pedal_x - 10 * S, y2=pedal_y)
    time.sleep(0.15)
    await call("mouse", operation="drag", x=bx + 10 * S, y=by + rh, x2=pedal_x + 10 * S, y2=pedal_y)
    time.sleep(0.15)

    # ── Draw handlebars ──
    phase("Draw handlebars")
    await call("mouse", operation="drag", x=bar_x - 15 * S, y=bar_y, x2=bar_x + 15 * S, y2=bar_y)
    time.sleep(0.15)

    # ── Draw wheel spokes ──
    phase("Draw spokes")
    for wx, wy in [(canvas_ox + 60, canvas_oy + 80), (canvas_ox + 60, canvas_oy + 80)]:
        for dx, dy in [(0, -20), (0, 20), (-20, 0), (20, 0), (-15, -15), (15, 15)]:
            await call("mouse", operation="drag", x=wx, y=wy, x2=wx + dx, y2=wy + dy)
            time.sleep(0.05)

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
