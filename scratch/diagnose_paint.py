import os
import sys

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from windows_computer_use_mcp.tools.portmanteau_elements import automation_elements
from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse
from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows


def research():
    print(f"DEBUG: windows_computer_use_mcp_BYPASS_HITL={os.getenv('windows_computer_use_mcp_BYPASS_HITL')}")

    # 1. VISUAL MOUSE TEST: Move in a square
    print("DEBUG: Starting visual mouse square test (100,100 -> 300,100 -> 300,300 -> 100,300)...")
    path = [(100, 100), (300, 100), (300, 300), (100, 300), (100, 100)]
    for x, y in path:
        res = automation_mouse("move", x=x, y=y, duration=0.5)
        print(f"DEBUG: Moved to {x},{y}: {res.get('success')}")

    # 2. SCREENSHOT
    try:
        from windows_computer_use_mcp.desktop_state.capture import DesktopStateCapture

        print("DEBUG: Capturing screenshot...")
        capturer = DesktopStateCapture()
        shot = capturer.capture(use_vision=True)
        print(f"DEBUG: Screenshot saved to: {shot.get('image_path') or 'NO_IMAGE_PATH'}")
    except Exception as e:
        print(f"DEBUG: Screenshot failed: {e}")

    # 3. PAINT DEEP DIVE
    print("DEBUG: Searching for all windows related to Paint...")
    win_res = automation_windows("list")
    paint_windows = []
    if win_res.get("success"):
        for w in win_res["windows"]:
            title = w.get("title", "")
            cname = w.get("class_name", "")
            if "Paint" in title or "Paint" in cname or "mspaint" in title.lower():
                paint_windows.append(w)
                print(f"DEBUG: Found Paint window candidate: Title='{title}', Class='{cname}', Handle={w['handle']}")

    if not paint_windows:
        print("DEBUG: No Paint windows found.")
        return

    for win in paint_windows:
        handle = win["handle"]
        print(f"\n--- WINDOW HANDLE: {handle} ('{win['title']}') ---")
        res = automation_elements("list", window_handle=handle, max_depth=15)

        buttons = []

        def find_buttons(elements):
            for e in elements:
                ctype = e.get("control_type", "")
                name = e.get("name", "")
                aid = e.get("automation_id", "")
                if "Button" in ctype or "ListItem" in ctype or "Button" in aid:
                    buttons.append(f"Name='{name}', ID='{aid}', Type='{ctype}'")
                if e.get("children"):
                    find_buttons(e["children"])

        if res.get("success"):
            find_buttons(res["elements"])
            print(f"DEBUG: Found {len(buttons)} interactive items.")
            # Filter for colors or brushes
            keywords = ["Green", "Blue", "Red", "Brush", "Oil", "palette", "Color"]
            for b in buttons:
                if any(k.lower() in b.lower() for k in keywords):
                    print(f"MATCH: {b}")
        else:
            print(f"DEBUG: Failed to list elements for handle {handle}")


if __name__ == "__main__":
    research()
