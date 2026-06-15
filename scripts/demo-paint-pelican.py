#!/usr/bin/env python3
"""Paint a pelican riding a bicycle in MS Paint, fully autonomous."""
import os, sys, time, asyncio, subprocess, math, importlib, inspect, traceback

os.environ["WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL"] = "1"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from windows_computer_use_mcp.tools.models import ToolResult


async def call(tool: str, **params) -> ToolResult:
    try:
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
        print(f"  call error {tool}: {e}")
        return ToolResult(status="error", message=str(e))

def phase(label: str):
    print(f"\n=== {label} ===")
    time.sleep(0.5)


async def main():
    phase("Open Paint")
    try:
        subprocess.Popen("start mspaint", shell=True)
    except Exception as e:
        print(f"  Launch failed: {e}")
        return
    print("  Paint launched")
    time.sleep(4)

    phase("Find Paint window")
    r = await call("windows", operation="find", title="untitled")
    if r.status != "success" or not r.data.get("windows"):
        print(f"  Window not found: {r.message}")
        return
    hwnd = r.data["windows"][0]["handle"]
    print(f"  Handle: {hwnd}")
    await call("windows", operation="maximize", handle=hwnd)
    time.sleep(1)

    r = await call("windows", operation="rect", handle=hwnd)
    left = r.data.get("left", 0)
    top = r.data.get("top", 0)
    print(f"  Window: {left},{top}")

    await call("windows", operation="focus", handle=hwnd)
    time.sleep(0.5)

    # Ctrl+E to open canvas resize dialog, set to default
    await call("keyboard", operation="hotkey", keys=["ctrl", "e"])
    time.sleep(1)
    await call("keyboard", operation="hotkey", keys=["alt", "d"])  # Default button
    time.sleep(0.5)
    await call("keyboard", operation="press", key="enter")  # OK
    time.sleep(0.5)

    cx, cy = 960, 520  # canvas center
    await call("mouse", operation="click", x=cx, y=cy)
    print(f"  Center: {cx},{cy}")
    time.sleep(0.3)

    S = 3
    half = 60 * S  # half the bike width

    # ── BICYCLE ──
    phase("Bicycle")
    bw_x, bw_y = cx - half, cy + half
    fw_x, fw_y = cx + half, cy + half
    seat_x, seat_y = cx - 40 * S, cy
    bar_x, bar_y = cx + 30 * S, cy - 10 * S
    pedal_x, pedal_y = cx, cy + half

    for x1,y1,x2,y2 in [
        (seat_x, seat_y, pedal_x, pedal_y),
        (pedal_x, pedal_y, bar_x, bar_y),
        (bar_x, bar_y, seat_x, seat_y),
        (pedal_x, pedal_y, bw_x, bw_y),
        (pedal_x, pedal_y, fw_x, fw_y),
    ]:
        await call("mouse", operation="drag", x=x1, y=y1, x2=x2, y2=y2)
        time.sleep(0.2)

    # Wheels (24 segments each)
    phase("Wheels")
    for wx, wy in [(bw_x, bw_y), (fw_x, fw_y)]:
        r = 25 * S
        for i in range(24):
            a1, a2 = 2*math.pi*i/24, 2*math.pi*(i+1)/24
            await call("mouse", operation="drag",
                x=int(wx+r*math.cos(a1)), y=int(wy+r*math.sin(a1)),
                x2=int(wx+r*math.cos(a2)), y2=int(wy+r*math.sin(a2)))
            time.sleep(0.03)

    # ── PELICAN ──
    phase("Pelican")
    bx, by = cx - 20*S, cy - 50*S  # body center

    # Body oval
    for i in range(16):
        a1, a2 = 2*math.pi*i/16, 2*math.pi*(i+1)/16
        await call("mouse", operation="drag",
            x=int(bx+32*S*math.cos(a1)), y=int(by+22*S*math.sin(a1)),
            x2=int(bx+32*S*math.cos(a2)), y2=int(by+22*S*math.sin(a2)))
        time.sleep(0.03)

    # Neck + head
    hx, hy = bx+30*S, by-28*S
    await call("mouse", operation="drag", x=bx+20*S, y=by-15*S, x2=hx, y2=hy)
    time.sleep(0.1)
    for i in range(12):
        a1, a2 = 2*math.pi*i/12, 2*math.pi*(i+1)/12
        await call("mouse", operation="drag",
            x=int(hx+12*S*math.cos(a1)), y=int(hy+12*S*math.sin(a1)),
            x2=int(hx+12*S*math.cos(a2)), y2=int(hy+12*S*math.sin(a2)))
        time.sleep(0.03)

    # Beak
    await call("mouse", operation="drag", x=hx+12*S, y=hy, x2=hx+55*S, y2=hy-5*S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=hx+55*S, y=hy-5*S, x2=hx+55*S, y2=hy+10*S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=hx+55*S, y=hy+10*S, x2=hx+10*S, y2=hy+12*S)
    time.sleep(0.1)

    # Wing
    await call("mouse", operation="drag", x=bx+5*S, y=by-10*S, x2=bx-25*S, y2=by-20*S)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=bx-25*S, y=by-20*S, x2=bx-22*S, y2=by+5*S)
    time.sleep(0.1)

    # Legs
    await call("mouse", operation="drag", x=bx-10*S, y=by+22*S, x2=pedal_x-10*S, y2=pedal_y)
    time.sleep(0.1)
    await call("mouse", operation="drag", x=bx+10*S, y=by+22*S, x2=pedal_x+10*S, y2=pedal_y)
    time.sleep(0.1)

    # Handlebars
    await call("mouse", operation="drag", x=bar_x-15*S, y=bar_y, x2=bar_x+15*S, y2=bar_y)
    time.sleep(0.1)

    phase("Screenshot")
    await call("visual", operation="screenshot", window_handle=hwnd)
    print("  Screenshot taken")
    print("\n*** Pelican on a bike! Ready for recording. Closing in 10s... ***")
    time.sleep(10)

    await call("keyboard", operation="hotkey", keys=["alt", "f4"])
    time.sleep(0.5)
    await call("keyboard", operation="press", key="enter")
    print("  Paint closed")

if __name__ == "__main__":
    asyncio.run(main())
