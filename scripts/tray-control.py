#!/usr/bin/env python3
"""System tray controller for windows-computer-use-mcp.

Run alongside the MCP server for quick access to:
- Toggle automation block on/off (HITL bypass)
- Open web operator UI
- Quick approve (5 min)
- Server status

Requires: pip install pystray pillow
"""

import io
import os
import subprocess
import sys
import threading
import time
import urllib.request

import pystray
from PIL import Image, ImageDraw

BACKEND_URL = "http://127.0.0.1:10789"
WEB_URL = "http://127.0.0.1:10788"

automation_enabled = False


def create_icon(color: tuple[int, int, int, int]) -> Image.Image:
    """Create a 64x64 tray icon — simple circle with 'C' (Computer Use)."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    draw.text((18, 16), "C", fill=(255, 255, 255, 255), font=None)
    return img


def health_check() -> bool:
    try:
        r = urllib.request.urlopen(f"{BACKEND_URL}/api/v1/health", timeout=2)
        return r.status == 200
    except Exception:
        return False


def approve_automation():
    try:
        req = urllib.request.Request(
            f"{BACKEND_URL}/api/v1/safety/approve",
            data=b'{"duration_minutes": 5}',
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
        show_notification("Approved", "Automation approved for 5 minutes.")
    except Exception as e:
        show_notification("Error", f"Failed to approve: {e}")


def set_bypass(enabled: bool):
    global automation_enabled
    automation_enabled = enabled
    os.environ["WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL"] = "1" if enabled else "0"
    show_notification(
        "Automation " + ("Enabled" if enabled else "Disabled"),
        "HITL bypass is now " + ("ON" if enabled else "OFF"),
    )


def show_notification(title: str, message: str):
    try:
        from plyer import notification
        notification.notify(title=title, message=message, timeout=3)
    except ImportError:
        print(f"[tray] {title}: {message}")


def open_webui(_icon=None, _item=None):
    subprocess.Popen(["start", WEB_URL], shell=True)


def open_settings(_icon=None, _item=None):
    subprocess.Popen(["start", f"{WEB_URL}/settings"], shell=True)


def toggle_automation(icon: pystray.Icon, _item=None):
    global automation_enabled
    automation_enabled = not automation_enabled
    set_bypass(automation_enabled)
    update_menu(icon)


def quick_approve(icon: pystray.Icon, _item=None):
    approve_automation()
    update_menu(icon)


def exit_app(icon: pystray.Icon, _item=None):
    icon.stop()


def update_menu(icon: pystray.Icon):
    health = health_check()
    status_color = "green" if health else "red"
    status_text = "Server: OK" if health else "Server: DOWN"
    auto_text = "Disable Automation" if automation_enabled else "Enable Automation"
    auto_checked = automation_enabled

    menu = pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.MenuItem(f"Port: 10789 (back) / 10788 (web)", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(auto_text, toggle_automation, checked=lambda: auto_checked),
        pystray.MenuItem("Approve 5 min", quick_approve),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Web UI", open_webui),
        pystray.MenuItem("Settings", open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", exit_app),
    )
    icon.menu = menu


def main():
    icon_color = (34, 197, 94, 255) if health_check() else (239, 68, 68, 255)
    icon_image = create_icon(icon_color)

    icon = pystray.Icon("windows-computer-use", icon_image, "Windows Computer Use", menu=pystray.Menu())
    update_menu(icon)

    def health_poller():
        last_color = None
        while True:
            ok = health_check()
            new_color = (34, 197, 94, 255) if ok else (239, 68, 68, 255)
            if new_color != last_color:
                last_color = new_color
                icon.icon = create_icon(new_color)
                update_menu(icon)
            time.sleep(10)

    threading.Thread(target=health_poller, daemon=True).start()
    icon.run()


if __name__ == "__main__":
    main()
