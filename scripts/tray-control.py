#!/usr/bin/env python3
"""System tray controller for windows-computer-use-mcp.

Run alongside the MCP server with: just tray
"""

import io
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

import pystray
from PIL import Image, ImageDraw, ImageFont

BACKEND_URL = "http://127.0.0.1:10789"
WEB_URL = "http://127.0.0.1:10788"
LOG_FILE = os.path.expandvars(r"%USERPROFILE%\.windows-computer-use-mcp\server.log")
RECORDING = False
MACRO_DIR = Path.home() / ".windows-computer-use-mcp" / "macros"


def create_icon(text: str, color: tuple[int, int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, 60, 60], fill=color)
    try:
        font = ImageFont.truetype("segoeui.ttf", 28)
    except Exception:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((64 - tw) // 2, (64 - th) // 2 - 2), text, fill="white", font=font)
    return img


def api_get(path: str) -> dict | None:
    try:
        r = urllib.request.urlopen(f"{BACKEND_URL}{path}", timeout=3)
        return json.loads(r.read())
    except Exception:
        return None


def api_post(path: str, data: dict | None = None) -> dict | None:
    try:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(
            f"{BACKEND_URL}{path}", data=body,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        r = urllib.request.urlopen(req, timeout=5)
        return json.loads(r.read())
    except Exception:
        return None


def health_check() -> bool:
    d = api_get("/api/v1/health")
    return d is not None and d.get("status") == "ok"


def toggle_bypass(icon: pystray.Icon, _item=None):
    global automation_enabled
    automation_enabled = not automation_enabled
    os.environ["WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL"] = "1" if automation_enabled else "0"
    notify("Automation " + ("Enabled" if automation_enabled else "Disabled"))
    _rebuild(icon)


def quick_approve(icon: pystray.Icon, _item=None):
    r = api_post("/api/v1/safety/approve", {"duration_minutes": 5})
    if r:
        notify("Approved for 5 minutes")
    else:
        notify("Approve failed — is the server running?")
    _rebuild(icon)


def notify(text: str):
    try:
        from plyer import notification
        notification.notify(title="Windows Computer Use", message=text, timeout=3)
    except Exception:
        print(f"[tray] {text}")


def open_url(url: str):
    subprocess.Popen(["start", url], shell=True)


def view_log(icon: pystray.Icon, _item=None):
    log_paths = [LOG_FILE, "windows-computer-use-mcp.log", "server.log"]
    content = ""
    for p in log_paths:
        fp = Path(p)
        if fp.exists():
            lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
            content = "\n".join(lines[-50:])
            break
    if not content:
        content = "(no log file found)"
    show_message("Server Log (last 50 lines)", content, 500, 400)


def show_server_status(icon: pystray.Icon, _item=None):
    info = api_get("/api/v1/system/info")
    diag = api_get("/api/v1/diagnostics")
    lines = []
    if info:
        lines.append(f"CPU: {info.get('cpu_percent', '?')}%")
        lines.append(f"Mem: {info.get('memory_percent', '?')}%")
        lines.append(f"Disk: {info.get('disk_percent', '?')}%")
        lines.append(f"Windows: {info.get('window_count', '?')}")
    if diag:
        tools = diag.get("tools", {})
        if isinstance(tools, dict):
            lines.append(f"Tools: {tools.get('count', '?')}")
        lines.append(f"Tesseract: {diag.get('tesseract_available', '?')}")
    if not lines:
        lines.append("(server unreachable)")
    show_message("Server Status", "\n".join(lines), 300, 200)


def show_telemetry(icon: pystray.Icon, _item=None):
    d = api_get("/api/v1/system/info")
    if d is None:
        show_message("Telemetry", "(server unreachable)", 300, 100)
        return
    show_message("Telemetry", "See the Web UI for detailed stats.\nOpen: Settings → Telemetry", 300, 100)


def run_macro(name: str, icon: pystray.Icon, _item=None):
    actions = {
        "notepad": lambda: api_post("/api/v1/tools/call", {
            "tool": "automation_system", "params": {"operation": "start_app", "app_path": "notepad.exe"}
        }),
        "screenshot": lambda: api_post("/api/v1/tools/call", {
            "tool": "automation_visual", "params": {"operation": "screenshot"}
        }),
        "demo": lambda: subprocess.Popen(
            [sys.executable, "-m", "windows_computer_use_mcp.main", "--demo"]
        ),
    }
    fn = actions.get(name)
    if fn:
        fn()
        notify(f"Macro: {name}")


def toggle_recording(icon: pystray.Icon, _item=None):
    global RECORDING
    RECORDING = not RECORDING
    if RECORDING:
        api_post("/api/v1/tools/call", {
            "tool": "automation_macro",
            "params": {"operation": "record"},
        })
        notify("Recording started — use Ctrl+Shift+R to stop")
    else:
        r = api_post("/api/v1/tools/call", {
            "tool": "automation_macro",
            "params": {"operation": "stop"},
        })
        notify("Recording stopped")
    _rebuild(icon)


def restart_backend(icon: pystray.Icon, _item=None):
    import psutil
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmd = " ".join(proc.info.get("cmdline") or [])
            if "windows_computer_use_mcp" in cmd or "uvicorn" in cmd:
                proc.kill()
                notify("Backend killed — restart manually")
                return
        except Exception:
            pass
    notify("No backend process found")


def exit_app(icon: pystray.Icon, _item=None):
    icon.stop()


def show_message(title: str, body: str, w: int = 400, h: int = 300):
    try:
        import tkinter as tk
        root = tk.Tk()
        root.title(title)
        root.geometry(f"{w}x{h}")
        txt = tk.Text(root, wrap="word", font=("Consolas", 10), bg="#1e1e2e", fg="#cdd6f4")
        txt.insert("1.0", body)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)
        root.mainloop()
    except Exception as e:
        notify(f"Can't show window: {e}")


def _rebuild(icon: pystray.Icon):
    icon.menu = build_menu()
    icon.icon = create_icon("C", (34, 197, 94, 255) if health_check() else (239, 68, 68, 255))


def build_menu():
    global RECORDING, automation_enabled
    health = health_check()
    status_color = "● OK" if health else "○ DOWN"
    record_label = "■ Stop Recording" if RECORDING else "● Record Macros"

    return pystray.Menu(
        pystray.MenuItem(f"Server {status_color}", None, enabled=False),
        pystray.MenuItem(f"Ports: 10789 (API) / 10788 (Web)", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            "Disable Automation" if automation_enabled else "Enable Automation",
            toggle_bypass,
            checked=lambda: automation_enabled,
        ),
        pystray.MenuItem("Approve 5 min", quick_approve),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quick Macros", pystray.Menu(
            pystray.MenuItem("Open Notepad", lambda i, _: run_macro("notepad", i)),
            pystray.MenuItem("Take Screenshot", lambda i, _: run_macro("screenshot", i)),
            pystray.MenuItem("Run Demo", lambda i, _: run_macro("demo", i)),
        )),
        pystray.MenuItem(
            record_label,
            toggle_recording,
        ),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("View Log", view_log),
        pystray.MenuItem("Server Status", show_server_status),
        pystray.MenuItem("Telemetry", show_telemetry),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open Web UI", lambda i, _: open_url(WEB_URL)),
        pystray.MenuItem("Settings", lambda i, _: open_url(f"{WEB_URL}/settings")),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Restart Backend", restart_backend),
        pystray.MenuItem("Exit", exit_app),
    )


automation_enabled = os.environ.get("WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL", "").lower() in ("1", "true", "yes")


def hotkey_listener():
    try:
        import keyboard as kb
        kb.add_hotkey("ctrl+shift+r", lambda: (
            setattr(sys.modules[__name__], "RECORDING", not RECORDING),
            api_post("/api/v1/tools/call", {
                "tool": "automation_macro",
                "params": {"operation": "stop" if RECORDING else "record"},
            }),
            notify("Recording stopped" if not RECORDING else "Recording started"),
        ))
        kb.wait()
    except Exception:
        pass


def main():
    MACRO_DIR.mkdir(parents=True, exist_ok=True)

    icon = pystray.Icon(
        "windows-computer-use",
        create_icon("C", (34, 197, 94, 255) if health_check() else (239, 68, 68, 255)),
        "Windows Computer Use",
        menu=build_menu(),
    )

    threading.Thread(target=hotkey_listener, daemon=True).start()

    def health_poller():
        last_ok = None
        while True:
            ok = health_check()
            if ok != last_ok:
                last_ok = ok
                icon.icon = create_icon("C", (34, 197, 94, 255) if ok else (239, 68, 68, 255))
                icon.menu = build_menu()
            time.sleep(10)

    threading.Thread(target=health_poller, daemon=True).start()
    icon.run()


if __name__ == "__main__":
    main()
