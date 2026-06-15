"""Painterly Landscape Demo for PyWinAuto MCP (SOTA 2026).
Industrialized for high-fidelity automation in Windows 11 MS Paint.
"""

import os
import sys
import time

# Add src to sys.path to ensure we can import the tools locally
sys.path.append(os.path.join(os.getcwd(), "src"))

from windows_computer_use_mcp.tools.portmanteau_elements import automation_elements
from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse
from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows


def run_painterly_demo():
    print("[START] Starting PyWinAuto MCP Painterly Demo...")

    # 1. Launch/Locate Paint
    print("[INIT] Launching Microsoft Paint...")
    # SOTA: Try various ways to launch
    paint_path = r"C:\Users\sandr\AppData\Local\Microsoft\WindowsApps\mspaint.exe"
    if not os.path.exists(paint_path):
        paint_path = "mspaint.exe"

    os.startfile(paint_path)
    time.sleep(3)  # Wait for splash screen

    # 2. Maximize and Focus
    print("[SEARCH] Locating Paint window...")
    win_res = automation_windows("find", class_name="MSPaintApp")
    if not win_res.get("success") or not win_res["windows"]:
        print("[ERROR] Microsoft Paint window not found.")
        return

    handle = win_res["windows"][0]["handle"]
    automation_windows("maximize", window_handle=handle)
    automation_windows("activate", window_handle=handle)
    time.sleep(1)

    # 3. Canvas Discovery
    print("[INIT] Searching for primary Canvas element...")
    canvas_rect = None
    # SOTA 2026: In Windows 11 Paint, the drawing area has automation_id="image"
    res = automation_elements("rect", window_handle=handle, auto_id="image")
    if res.get("success"):
        canvas_rect = res
        print(f"[FOUND] Found Canvas (image) at {canvas_rect['left']}, {canvas_rect['top']}")
    else:
        # Fallback: look for generic Image control
        print("[WARN] Canvas element not found by ID, searching by control type...")
        res = automation_elements("rect", window_handle=handle, control_type="Image", max_depth=10)
        if res.get("success"):
            canvas_rect = res
            print(f"[FOUND] Found Canvas (type:Image) at {canvas_rect['left']}, {canvas_rect['top']}")

    if not canvas_rect:
        print("[ERROR] Could not find canvas. Defaulting to center-of-window relative coordinates.")
        canvas_rect = {"left": 400, "top": 400, "width": 800, "height": 600}

    # 4. Calibration Move
    print("[INIT] Calibrating mouse movement...")
    automation_mouse("move", x=0, y=0, duration=0.2)
    automation_mouse("move", x=200, y=200, duration=0.2)

    # 5. Focus Canvas
    print("[INIT] Focusing canvas...")
    automation_mouse("click", x=canvas_rect["left"] + 50, y=canvas_rect["top"] + 50)
    time.sleep(1)

    # 6. Interaction Helpers
    def select_color(name):
        print(f"[COLOR] Selecting color: {name}...")
        res = automation_elements("click", window_handle=handle, title=name, exact_match=False, timeout=2.0)
        if not res.get("success"):
            print(f"[WARN] Failed to select color {name}")
        return res.get("success")

    def select_brush(name):
        print(f"[BRUSH] Selecting brush: {name}...")
        # First, ensure brush dropdown is open if possible, but modern Paint has it as a list
        res = automation_elements("click", window_handle=handle, title=name, exact_match=False, timeout=2.0)
        if not res.get("success"):
            print(f"[WARN] Failed to select brush {name}")
        return res.get("success")

    # 7. DRAWING PHASE

    # DRAW: Meadow (Green)
    select_color("Green")
    select_brush("Oil")
    print("[DRAW] Drawing the meadow...")
    # Drag from bottom-left to bottom-right (relative to canvas)
    base_x = canvas_rect["left"]
    base_y = canvas_rect["top"] + canvas_rect["height"] - 150
    automation_mouse("drag", x=base_x + 50, y=base_y, x2=base_x + canvas_rect["width"] - 50, y2=base_y, duration=1.5)

    # DRAW: Sky (Blue)
    select_color("Blue")
    select_brush("Watercolor")
    print("[DRAW] Drawing the sky...")
    sky_y = canvas_rect["top"] + 80
    automation_mouse("drag", x=base_x + 50, y=sky_y, x2=base_x + canvas_rect["width"] - 50, y2=sky_y, duration=1.5)

    # DRAW: Sun (Red/Yellow)
    select_color("Red")
    print("[DRAW] Drawing the sun...")
    cx = canvas_rect["left"] + canvas_rect["width"] - 150
    cy = canvas_rect["top"] + 120
    # Small circular motion
    automation_mouse("drag", x=cx, y=cy, x2=cx + 40, y2=cy + 40, duration=0.4)
    automation_mouse("drag", x=cx + 40, y=cy + 40, x2=cx, y2=cy + 80, duration=0.4)
    automation_mouse("drag", x=cx, y=cy + 80, x2=cx - 40, y2=cy + 40, duration=0.4)
    automation_mouse("drag", x=cx - 40, y=cy + 40, x2=cx, y2=cy, duration=0.4)

    print("[DONE] Painting complete!")


if __name__ == "__main__":
    run_painterly_demo()
