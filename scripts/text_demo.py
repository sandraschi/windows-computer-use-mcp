import logging
import os
import subprocess
import sys
import time

# Add src to sys.path to allow imports of windows_computer_use_mcp
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    from windows_computer_use_mcp.tools.portmanteau_keyboard import automation_keyboard
    from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows
except ImportError as e:
    print(f"Error: Could not import windows_computer_use_mcp tools. {e}")
    sys.exit(1)

# Configure logging to be quiet
logging.basicConfig(level=logging.WARNING)


def run_text_demo():
    print("[START] Starting PyWinAuto MCP Notepad ASCII Demo...")

    # 1. Launch Notepad
    print("[INIT] Launching Microsoft Notepad...")
    # Windows 11 uses Execution Aliases in %LOCALAPPDATA%\Microsoft\WindowsApps
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    notepad_alias = os.path.join(local_app_data, "Microsoft", "WindowsApps", "notepad.exe")

    if os.path.exists(notepad_alias):
        print(f"[INIT] Using Notepad alias: {notepad_alias}")
        subprocess.Popen([notepad_alias], shell=True)
    else:
        print("[INIT] Using 'notepad' command...")
        subprocess.Popen(["notepad"], shell=True)

    time.sleep(3)

    # 2. Find Window
    print("[SEARCH] Locating Notepad window...")
    for _ in range(5):
        # Use class_name="Notepad" for reliable discovery
        win_result = automation_windows("find", class_name="Notepad", partial=True)
        if win_result.get("success") and win_result.get("windows"):
            break
        print("[SEARCH] Waiting for Notepad window...")
        time.sleep(2)

    if not win_result.get("success") or not win_result.get("windows"):
        print("[ERROR] Could not find Notepad window.")
        return

    handle = win_result["windows"][0]["handle"]
    print(f"[FOUND] Found Notepad window (HWND: {handle})")

    automation_windows("maximize", handle=handle)
    automation_windows("activate", handle=handle)
    time.sleep(1)

    # 3. Type ASCII Art
    print("[TYPE] Rendering SOTA MISSION ASCII Art...")

    ascii_art = r"""
============================================================
   ____   ___ _____  _      __  __ ___ ____ ____ ___ ___  _   _
  / ___| / _ \_   _|/ \     |  \/  |_ _/ ___/ ___|_ _/ _ \| \ | |
  \___ \| | | || | / _ \    | |\/| || | \___ \___ \| | | | |  \| |
   ___) | |_| || |/ ___ \   | |  | || |  ___) |__) | | |_| | |\  |
  |____/ \___/ |_/_/   \_\  |_|  |_|___|____/____/___\___/|_| \_|

============================================================
INDUSTRIAL MCP FLEETS // VIENNA MARCH 2026 // SOTA 14.2.0
============================================================
"""

    # Type with a decent interval for visual effect
    res = automation_keyboard("type", text=ascii_art, interval=0.01)

    if res.get("success"):
        print("[DONE] ASCII Art successfully rendered in Notepad.")
    else:
        print(f"[ERROR] Failed to type ASCII art. Result: {res}")

    print("\n[FINISH] Text Demo Complete! The industrial fleet is operational.")


if __name__ == "__main__":
    run_text_demo()
