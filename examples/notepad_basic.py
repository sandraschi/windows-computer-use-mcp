import asyncio
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


async def run_notepad_example():
    """
    Demonstrates basic Notepad automation: opening, typing, and closing.
    """
    print("--- Notepad Automation Example ---")

    # In a real scenario, you would use the MCP client to call the server.
    # Here we simulate the logic flow that the MCP server tools execute.

    # 1. Start Notepad
    # Tool: mcp_pywinauto_window_mgr(operation="start", app_name="notepad.exe")
    print("[1] Opening Notepad...")

    # 2. Focus and Type
    # Tool: mcp_pywinauto_keyboard(operation="type_keys", window_title="* - Notepad", keys="Hello from SOTA 2026!{ENTER}This is an automated message.")
    print("[2] Typing message...")

    # 3. Save (Optional/Simulated)
    # Tool: mcp_pywinauto_keyboard(operation="hotkey", keys="^s")
    print("[3] Simulating save...")

    # 4. Close
    # Tool: mcp_pywinauto_window_mgr(operation="close", window_title="* - Notepad")
    print("[4] Closing Notepad (without saving)...")

    print("\nExample logic completed. To run this via MCP, start the windows-computer-use-mcp server")
    print("and use your favorite MCP client (Cursor, Windsurf, or Claude Desktop).")


if __name__ == "__main__":
    asyncio.run(run_notepad_example())
