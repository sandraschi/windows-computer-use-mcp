import logging
import os
import subprocess
import sys
import time

# Add src to sys.path to allow imports of windows_computer_use_mcp
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse
    from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows
except ImportError as e:
    print(f"Error: Could not import windows_computer_use_mcp tools. Ensure you are running from the project root. {e}")
    sys.exit(1)

# Configure logging to be quiet for the demo
logging.basicConfig(level=logging.WARNING)


def run_paint_demo():
    print("[START] Starting PyWinAuto MCP Paint Demo...")

    # 1. Launch Paint
    print("[INIT] Launching Microsoft Paint...")
    try:
        subprocess.Popen(["mspaint.exe"], shell=True)
    except Exception as e:
        print(f"[ERROR] Failed to launch mspaint.exe: {e}")
        return

    # 2. Wait for window and maximize
    print("[SEARCH] Locating Paint window...")
    time.sleep(3)  # Give it time to load

    result = automation_windows("find", title="Paint", partial=True)
    if not result.get("success") or not result.get("windows"):
        print("❌ Could not find Paint window. It might have a different title format.")
        return

    # Get the handle of the first found window
    handle = result["windows"][0]["handle"]
    print(f"[FOUND] Found window (Handle: {handle}). Maximizing...")

    automation_windows("maximize", handle=handle)
    automation_windows("activate", handle=handle)
    time.sleep(1)

    # 3. Get window dimensions for centering
    rect_result = automation_windows("rect", handle=handle)
    if not rect_result.get("success"):
        print("❌ Could not get window rectangle.")
        return

    rect = rect_result["rect"]
    center_x = rect["left"] + (rect["width"] // 2)
    center_y = rect["top"] + (rect["height"] // 2)

    print(f"[POINT] Drawing area centered at ({center_x}, {center_y})")

    # 4. Draw a SOTA Diamond/Square
    print("[DRAW] Drawing geometric shape...")

    # Size of the diamond
    size = 150

    # Points for a diamond
    points = [
        (center_x, center_y - size),  # Top
        (center_x + size, center_y),  # Right
        (center_x, center_y + size),  # Bottom
        (center_x - size, center_y),  # Left
        (center_x, center_y - size),  # Back to Top
    ]

    # Move to start position
    automation_mouse("move", x=points[0][0], y=points[0][1])
    time.sleep(0.5)

    # Draw the shape
    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]
        print(f"   - Segment {i + 1}: ({p1[0]}, {p1[1]}) -> ({p2[0]}, {p2[1]})")
        automation_mouse("drag", x=p1[0], y=p1[1], target_x=p2[0], target_y=p2[1], duration=0.8)

    print("\n[DONE] Paint Demo Complete! Enjoy the SOTA art.")
    print("   (Note: You can close Paint manually when finished.)")


if __name__ == "__main__":
    run_paint_demo()
