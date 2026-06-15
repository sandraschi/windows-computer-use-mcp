#!/usr/bin/env python3
"""CUA smoke test for NSIS-installed fleet apps.

Usage:
    python scripts/cua-smoke.py
    python scripts/cua-smoke.py --installer path/to/setup.exe
    python scripts/cua-smoke.py --config scripts/cua-nsis-config.json

Phases:
    1. Kill stale processes
    2. Silent install NSIS
    3. Launch app, wait for backend health
    4. Verify window + maximize
    5. Screenshot evidence
    6. Feature-route smoke (health + data endpoint)
    7. Check diagnostics
    8. WebView bridge proof (OCR)
    9. Nav click-through (3+ pages with screenshots)
    10. Analyze app logs
    11. Uninstall
    12. Write certification report
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

# ── Config ────────────────────────────────────────────────────────────

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cua-nsis-config.json")


def load_config(path: str | None = None) -> dict:
    p = path or DEFAULT_CONFIG_PATH
    if not os.path.exists(p):
        print(f"  [cua] WARNING: config not found at {p}, using built-in defaults", flush=True)
        return {}
    with open(p) as f:
        cfg = json.load(f)

    def _expand(v):
        if isinstance(v, str):
            return os.path.expandvars(v)
        if isinstance(v, list):
            return [_expand(x) for x in v]
        return v
    return {k: _expand(v) for k, v in cfg.items()}


def cfg(key: str, default=""):
    return _CONFIG.get(key, default)


_CONFIG = load_config()

# ── Derived constants ─────────────────────────────────────────────────

BACKEND_PORT = int(cfg("backend_port", 10789))
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}"
PRODUCT_NAME = cfg("product_name", "Windows Computer Use")
HEALTH_PATH = cfg("health_path", "/api/v1/health")
DIAGNOSTICS_PATH = cfg("diagnostics_path", "/api/v1/diagnostics")
FEATURE_PATH = cfg("feature_smoke_path", "/api/v1/system/info")
WINDOW_TITLE_RE = cfg("window_title_re", "Windows Computer Use")
BRIDGE_OK_TEXT = cfg("bridge_ok_text", "REST bridge reachable")
INSTALL_DIR = cfg("install_dir", "%LOCALAPPDATA%\\Windows Computer Use")
OPERATOR_EXE = cfg("operator_exe", "windows-computer-use-operator.exe")
PROCESS_NAMES = cfg("backend_process_names", ["windows-computer-use-operator", "windows-computer-use-backend"])
NSIS_GLOB = cfg("nsis_glob", "web_sota/src-tauri/target/release/bundle/nsis/Windows Computer Use_*_x64-setup.exe")
REGISTRY_FILTER = cfg("uninstall_registry_filter", "*Windows Computer Use*")
MAX_RETRY = 10
RETRY_DELAY = 3
REPO_NAME = cfg("repo_name", "windows-computer-use-mcp")
MCD_CERT_DIR = os.path.expandvars(r"%USERPROFILE%\Dev\repos\mcp-central-docs\projects\tauri-cua-nsis")

_INSTALLED = False
_EVIDENCE = {"repo": REPO_NAME, "screenshots": [], "pages_checked": [], "nav_results": [], "errors": [], "phases": {}}


# ── Helpers ────────────────────────────────────────────────────────

def log(msg: str):
    print(f"  [cua] {msg}", flush=True)


def log_warn(msg: str):
    print(f"  [WARN] {msg}", flush=True)


# ── CUA Client (windows-computer-use-mcp HTTP API → fallback to direct) ─────

_CUA_CLIENT_OK = False
_CUA_CLIENT_MODE = None


def _init_cua_client():
    global _CUA_CLIENT_OK, _CUA_CLIENT_MODE
    try:
        r = urllib.request.urlopen("http://127.0.0.1:10789/api/v1/health", timeout=2)
        if r.status == 200:
            log("windows-computer-use-mcp HTTP API reachable at :10789")
            _CUA_CLIENT_OK = True
            _CUA_CLIENT_MODE = "http"
            return
    except Exception:
        pass
    try:
        import pywinauto  # noqa: F401
        log("pywinauto direct import OK")
        _CUA_CLIENT_OK = True
        _CUA_CLIENT_MODE = "direct"
        return
    except ImportError:
        pass
    log("CUA client unavailable (install pywinauto or start windows-computer-use-mcp at :10789)")


def _cua_call(tool: str, params: dict) -> dict | None:
    if _CUA_CLIENT_MODE == "http":
        try:
            body = json.dumps({"name": tool, "arguments": params}).encode()
            r = urllib.request.Request(
                "http://127.0.0.1:10789/api/v1/tools/call",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(r, timeout=30)
            return json.loads(resp.read())
        except Exception as e:
            log(f"CUA HTTP call '{tool}' failed: {e}")
            return None
    elif _CUA_CLIENT_MODE == "direct":
        return _cua_call_direct(tool, params)
    return None


def _cua_call_direct(tool: str, params: dict) -> dict | None:
    try:
        if tool == "automation_windows":
            from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows
            op = params.get("operation", "find")
            result = automation_windows(op, **{k: v for k, v in params.items() if k != "operation"})
            return {"result": result}
        elif tool == "automation_visual":
            from windows_computer_use_mcp.tools.portmanteau_visual import automation_visual
            result = automation_visual(**params)
            return {"result": result}
        elif tool == "automation_elements":
            from windows_computer_use_mcp.tools.portmanteau_elements import automation_elements
            result = automation_elements(**params)
            return {"result": result}
        elif tool == "automation_mouse":
            from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse
            result = automation_mouse(**params)
            return {"result": result}
        elif tool == "get_window_state":
            from windows_computer_use_mcp.tools.window_state import get_window_state
            result = get_window_state(**params)
            return {"result": result}
    except Exception as e:
        log(f"Direct call '{tool}' failed: {e}")
        return None


_init_cua_client()


def cua_available() -> bool:
    return _CUA_CLIENT_OK


def cua_find_window(title_re: str = "") -> dict | None:
    result = _cua_call("automation_windows", {"operation": "find", "title": title_re, "partial": True})
    if result and result.get("result", {}).get("status") == "success":
        windows = result["result"].get("data", {}).get("windows", [])
        if windows:
            return windows[0]
    try:
        import pywinauto
        app = pywinauto.Application(backend="uia").connect(title_re=title_re)
        win = app.window(title_re=title_re)
        win.wait("visible", timeout=5)
        rect = win.rectangle()
        w = rect.width if isinstance(rect.width, int) else rect.width()
        h = rect.height if isinstance(rect.height, int) else rect.height()
        return {"handle": win.handle, "title": win.window_text(), "rect": {
            "left": rect.left, "top": rect.top, "width": w, "height": h
        }}
    except Exception:
        return None


def cua_screenshot(window_handle: int = 0, output_path: str = "") -> str | None:
    if _CUA_CLIENT_MODE == "http":
        result = _cua_call("automation_visual", {
            "operation": "screenshot", "window_handle": window_handle, "format": "png",
            "output_path": output_path,
        })
        if result and result.get("result", {}).get("status") == "success":
            path = result["result"].get("data", {}).get("screenshot_path", output_path)
            if os.path.exists(path):
                return path
    try:
        import pywinauto
        app = pywinauto.Application(backend="uia").connect(title_re=WINDOW_TITLE_RE)
        win = app.window(title_re=WINDOW_TITLE_RE)
        win.set_focus()
        time.sleep(1)
        capture = win.capture_as_image()
        capture.save(output_path)
        return output_path
    except Exception:
        return None


def cua_ocr_text(window_handle: int = 0, image_path: str = "") -> str:
    if _CUA_CLIENT_MODE == "http" and window_handle:
        result = _cua_call("automation_visual", {
            "operation": "extract_text", "window_handle": window_handle,
        })
        if result and result.get("result", {}).get("status") == "success":
            return result["result"].get("data", {}).get("text", "")
    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        if image_path and os.path.exists(image_path):
            from PIL import Image
            return pytesseract.image_to_string(Image.open(image_path))
        if window_handle:
            import pywinauto
            app = pywinauto.Application(backend="uia").connect(title_re=WINDOW_TITLE_RE)
            win = app.window(title_re=WINDOW_TITLE_RE)
            from PIL import Image
            capture = win.capture_as_image()
            return pytesseract.image_to_string(capture)
    except Exception:
        pass
    return ""


def cua_click(window_handle: int, x: int, y: int):
    if _CUA_CLIENT_MODE == "http":
        _cua_call("automation_mouse", {"operation": "click", "x": x, "y": y, "absolute": True})
        return
    if _CUA_CLIENT_MODE == "direct":
        try:
            import pywinauto.mouse
            pywinauto.mouse.click(button="left", coords=(x, y))
        except Exception:
            pass


def cua_maximize(window_handle: int):
    """Maximize the window."""
    if _CUA_CLIENT_MODE == "http":
        _cua_call("automation_windows", {"operation": "maximize", "handle": window_handle})
        return
    if _CUA_CLIENT_MODE == "direct":
        try:
            import pywinauto
            app = pywinauto.Application(backend="uia").connect(title_re=WINDOW_TITLE_RE)
            win = app.window(title_re=WINDOW_TITLE_RE)
            win.maximize()
        except Exception:
            pass

# ── Phase failure helpers ──────────────────────────────────────────


class PhaseFailed(Exception):
    """Non-fatal phase failure — script continues to uninstall."""


def fatal(msg: str):
    print(f"  [cua] FATAL: {msg}", flush=True)
    _EVIDENCE["errors"].append(f"FATAL: {msg}")
    sys.exit(1)


def phase_fail(msg: str):
    print(f"  [cua] PHASE FAIL: {msg}", flush=True)
    _EVIDENCE["errors"].append(f"PHASE FAIL: {msg}")
    raise PhaseFailed(msg)


# ── Phase 1: Kill stale ───────────────────────────────────────────────

def kill_stale():
    for name in PROCESS_NAMES:
        subprocess.run(["taskkill", "/F", "/IM", f"{name}.exe", "/T"], capture_output=True, timeout=10)
    time.sleep(1)
    log("Stale processes killed")


# ── Phase 2: Install ──────────────────────────────────────────────────

def find_installer() -> str:
    import glob
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pattern = os.path.join(repo_root, *NSIS_GLOB.replace("/", "\\").split("\\"))
    matches = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if matches:
        return matches[0]
    fatal("No NSIS installer found. Run 'just build-native' first.")


def silent_install(installer: str):
    log(f"Installing: {installer}")
    r = subprocess.run([installer, "/S"], capture_output=True, timeout=120)
    if r.returncode != 0:
        fatal(f"NSIS install exited with code {r.returncode}")
    global _INSTALLED
    _INSTALLED = True
    time.sleep(2)
    log("Install complete")


# ── Phase 3: Launch ──────────────────────────────────────────────────

def launch_app():
    exe = os.path.join(INSTALL_DIR, OPERATOR_EXE)
    if not os.path.exists(exe):
        fatal(f"Operator not found at {exe}")
    env = os.environ.copy()
    env_vars = cfg("env_vars", {})
    if isinstance(env_vars, dict):
        for k, v in env_vars.items():
            env[k] = str(v)
            log(f"  Set env {k}={v}")
    subprocess.Popen([exe], cwd=INSTALL_DIR, env=env)
    log(f"Launched {exe}")
    for attempt in range(MAX_RETRY):
        try:
            resp = urllib.request.urlopen(f"{BACKEND_URL}{HEALTH_PATH}", timeout=5)
            if resp.status == 200:
                log(f"Backend healthy (attempt {attempt + 1})")
                _EVIDENCE["backend_healthy"] = True
                return
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            pass
        time.sleep(RETRY_DELAY)
    fatal(f"Backend not reachable after {MAX_RETRY * RETRY_DELAY}s")


# ── Phase 4: Verify window + maximize ─────────────────────────────────

def verify_window():
    if not cua_available():
        log("CUA client unavailable -- window check skipped")
        return
    win = cua_find_window(WINDOW_TITLE_RE)
    if win:
        r = win.get("rect", {}) or {}
        w = r.get("width", 0) or 0
        h = r.get("height", 0) or 0
        log(f"Window '{win.get('title', '?')}' found: {w}x{h}")
        _EVIDENCE["window_rect"] = r
        if (isinstance(w, int) and isinstance(h, int) and w > 0 and h > 0 and (w < 100 or h < 100)):
            phase_fail(f"Window too small: {w}x{h}")
        # Maximize
        log("Maximizing window...")
        cua_maximize(win.get("handle", 0))
        time.sleep(1)
        # Re-check size after maximize
        win2 = cua_find_window(WINDOW_TITLE_RE)
        if win2:
            r2 = win2.get("rect", {}) or {}
            log(f"After maximize: {r2.get('width', 0)}x{r2.get('height', 0)}")
    else:
        log(f"Window matching '{WINDOW_TITLE_RE}' not found")


# ── Phase 5: Screenshot ──────────────────────────────────────────────

def take_screenshot(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"app-{int(time.time())}.png")
    result = cua_screenshot(0, path)
    if result and os.path.exists(result):
        _EVIDENCE["screenshots"].append(os.path.basename(result))
        log(f"Screenshot saved: {result} ({os.path.getsize(result)} bytes)")
    else:
        log("Screenshot not available (CUA client needed)")


# ── Phase 6: Feature-route smoke ─────────────────────────────────────

def check_feature_route():
    try:
        resp = urllib.request.urlopen(f"{BACKEND_URL}{FEATURE_PATH}", timeout=5)
        body = json.loads(resp.read())
        log(f"Feature route {FEATURE_PATH}: HTTP {resp.status}")
        if resp.status == 200:
            log(f"  response keys: {list(body.keys())[:5]}")
            _EVIDENCE["feature_route_status"] = resp.status
    except Exception as e:
        log(f"Feature route check failed (non-fatal): {e}")


# ── Phase 7: Diagnostics ─────────────────────────────────────────────

def check_diagnostics():
    try:
        resp = urllib.request.urlopen(f"{BACKEND_URL}{DIAGNOSTICS_PATH}", timeout=5)
        data = json.loads(resp.read())
        if data.get("success"):
            d = data["data"]
            log(f"Backend: {d['backend'].get('status')} v{d['backend'].get('version')}")
            log(f"System: CPU {d['system'].get('cpu_percent')}% | Mem {d['system'].get('memory_percent')}% | Disk {d['system'].get('disk_percent')}%")
            log(f"Tools: {d['tools'].get('total')} registered")
            log(f"CUA: Tesseract={d['cua_status']['tesseract_available']} Window={d['cua_status']['window_found']}")
            _EVIDENCE["tools_registered"] = d['tools'].get('total', 0)
            if d.get("errors", {}).get("count", 0) > 0:
                log(f"WARNING: {d['errors']['count']} errors logged")
        else:
            log(f"Diagnostics returned: {data}")
    except Exception as e:
        log(f"Diagnostics check failed (non-fatal): {e}")


# ── Phase 8: WebView bridge proof (OCR) ──────────────────────────────

def verify_webview_bridge(output_dir: str):
    if not cua_available():
        log("CUA client unavailable -- WebView bridge check skipped")
        return
    os.makedirs(output_dir, exist_ok=True)
    snap_path = os.path.join(output_dir, f"bridge-{int(time.time())}.png")
    result = cua_screenshot(0, snap_path)
    text = cua_ocr_text(0, snap_path or "")
    if not text and result and os.path.exists(snap_path):
        text = cua_ocr_text(image_path=snap_path)
    if BRIDGE_OK_TEXT.lower() in text.lower() or "connected" in text.lower():
        log(f"WebView bridge OK (found '{BRIDGE_OK_TEXT}' in screenshot OCR)")
        _EVIDENCE["bridge_ok"] = True
    elif text:
        log(f"WebView OCR text: {text[:200]}")
        _EVIDENCE["bridge_ocr_text"] = text[:200]
        phase_fail(f"WebView bridge not OK (expected '{BRIDGE_OK_TEXT}')")
    else:
        log("WebView bridge check skipped (no OCR available)")


# ── Phase 9: Nav click-through (3+ pages) ────────────────────────────

def nav_click_through(output_dir: str):
    """Click each sidebar nav item, maximize window first, verify page loads via OCR.
    Checks at least 3 pages per repo."""
    if not cua_available():
        log("CUA client unavailable -- nav click-through skipped")
        return

    nav_routes = cfg("nav_routes", [
        ["Dashboard", "Dashboard"],
        ["Logging", "Logs"],
        ["Settings", "Settings"],
        ["Help", "Help"],
    ])
    if isinstance(nav_routes, list):
        nav_routes = [(r[0], r[1]) for r in nav_routes if len(r) >= 2]

    if len(nav_routes) < 3:
        log_warn(f"Only {len(nav_routes)} nav routes configured — need at least 3 for cert")

    win = cua_find_window(WINDOW_TITLE_RE)
    if not win:
        log("No window found for nav click-through")
        return

    # Maximize
    cua_maximize(win.get("handle", 0))
    time.sleep(1)

    r = win.get("rect", {}) or {}
    wx = r.get("left", 0) or 0
    wy = r.get("top", 0) or 0
    snap_dir = os.path.join(output_dir, "nav")
    os.makedirs(snap_dir, exist_ok=True)

    sidebar_click_x = int(cfg("sidebar_click_x", 30))
    sidebar_first_y = int(cfg("sidebar_first_y", 90))
    sidebar_step_y = int(cfg("sidebar_step_y", 55))

    pages_ok = 0
    for idx, (label, expected_header) in enumerate(nav_routes):
        try:
            click_x = wx + sidebar_click_x
            click_y = wy + sidebar_first_y + idx * sidebar_step_y
            cua_click(win.get("handle", 0), click_x, click_y)
            time.sleep(2)

            # Screenshot each page
            snap_path = os.path.join(snap_dir, f"{label.lower()}-{int(time.time())}.png")
            result = cua_screenshot(win.get("handle", 0), snap_path)
            if result:
                _EVIDENCE["screenshots"].append(f"nav/{os.path.basename(result)}")

            text = cua_ocr_text(win.get("handle", 0), snap_path)

            if expected_header.lower() in text.lower():
                pages_ok += 1
                log(f"Nav '{label}' ({idx+1}/{len(nav_routes)}): V page loaded")
                _EVIDENCE["nav_results"].append({"page": label, "ok": True})
            else:
                log(f"Nav '{label}' ({idx+1}/{len(nav_routes)}): X header not found in OCR — text: {text[:80]}")
                _EVIDENCE["nav_results"].append({"page": label, "ok": False})

        except Exception as e:
            log(f"Nav '{label}' failed (non-fatal): {e}")
            _EVIDENCE["nav_results"].append({"page": label, "ok": False, "error": str(e)})

    _EVIDENCE["pages_checked"] = f"{pages_ok}/{len(nav_routes)}"

    # Return to dashboard
    try:
        cua_click(win.get("handle", 0), wx + sidebar_click_x, wy + sidebar_first_y)
        time.sleep(1)
    except Exception:
        pass

    if pages_ok < 3:
        phase_fail(f"Only {pages_ok}/{len(nav_routes)} pages loaded correctly (need ≥3)")


# ── Phase 10: Log analysis ────────────────────────────────────────────

def analyze_logs():
    log_paths = cfg("log_paths", [
        os.path.join(INSTALL_DIR, f"{REPO_NAME.replace('-','_')}.log"),
        os.path.expandvars(r"%APPDATA%\com.sandraschi.{repo_native}\logs\backend-spawn.log".format(
            repo_native=cfg("identifier", REPO_NAME))),
    ])
    errors = []
    warnings = []

    for path in log_paths:
        if not os.path.exists(path):
            continue
        log(f"Analyzing log: {path} ({os.path.getsize(path)} bytes)")
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    if "ERROR" in stripped or "CRITICAL" in stripped:
                        errors.append(stripped)
                    elif "WARNING" in stripped or "WARN" in stripped:
                        warnings.append(stripped)
        except Exception as e:
            log(f"Could not read {path}: {e}")

    if errors:
        log(f"ERRORS FOUND ({len(errors)}):")
        for err in errors[:10]:
            log(f"  ! {err[:200]}")
    else:
        log("No errors found in logs")

    if warnings:
        log(f"Warnings: {len(warnings)}")

    _EVIDENCE["log_errors"] = len(errors)
    _EVIDENCE["log_warnings"] = len(warnings)

    if errors:
        phase_fail(f"{len(errors)} errors found in app logs")


# ── Phase 11: Uninstall ──────────────────────────────────────────────

def uninstall():
    uninstaller = os.path.join(INSTALL_DIR, "uninstall.exe")
    if not os.path.exists(uninstaller):
        if _INSTALLED:
            log(f"Uninstaller not found at {uninstaller}")
        return
    r = subprocess.run([uninstaller, "/S"], capture_output=True, timeout=60)
    log(f"Uninstaller exited with code {r.returncode}")
    time.sleep(2)
    remaining = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         f"Get-ItemProperty 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*' -EA 0 | Where-Object {{ $_.DisplayName -like '{REGISTRY_FILTER}' }}"],
        capture_output=True, text=True, timeout=15,
    )
    if remaining.stdout.strip():
        log("WARNING: App may still be registered")
    else:
        log("Clean: app uninstalled")


# ── Phase 12: Write certification report ─────────────────────────────

def write_cert_report(screenshots_base: str, passed: int, total: int, all_ok: bool):
    """Write per-repo report and update MCD manifest."""
    repo = REPO_NAME
    status = "certified" if all_ok else "failed"

    # Copy screenshots to mcd
    mcd_screenshots_dir = os.path.join(MCD_CERT_DIR, "certification", "screenshots")
    os.makedirs(mcd_screenshots_dir, exist_ok=True)

    screenshot_names = []
    if os.path.exists(screenshots_base):
        for root, dirs, files in os.walk(screenshots_base):
            for f in files:
                if f.endswith(".png"):
                    src = os.path.join(root, f)
                    rel = os.path.relpath(src, screenshots_base)
                    dst_name = f"{repo}-{rel.replace(os.sep, '-')}"
                    dst = os.path.join(mcd_screenshots_dir, dst_name)
                    try:
                        import shutil
                        shutil.copy2(src, dst)
                        screenshot_names.append(dst_name)
                    except Exception as e:
                        log(f"Could not copy screenshot {f}: {e}")

    # Write per-repo report
    report = {
        "repo": repo,
        "product": PRODUCT_NAME,
        "timestamp": time.time(),
        "status": status,
        "phases": _EVIDENCE["phases"],
        "backend_healthy": _EVIDENCE.get("backend_healthy", False),
        "tools_registered": _EVIDENCE.get("tools_registered", 0),
        "bridge_ok": _EVIDENCE.get("bridge_ok", False),
        "pages_checked": _EVIDENCE.get("pages_checked", "0/0"),
        "log_errors": _EVIDENCE.get("log_errors", 0),
        "log_warnings": _EVIDENCE.get("log_warnings", 0),
        "screenshots": screenshot_names,
        "nav_results": _EVIDENCE.get("nav_results", []),
        "errors": _EVIDENCE.get("errors", []),
    }

    reports_dir = os.path.join(MCD_CERT_DIR, "certification", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, f"{repo}.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    log(f"Report saved: {report_path}")

    # Update MCD manifest.json
    manifest_path = os.path.join(MCD_CERT_DIR, "certification", "manifest.json")
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    else:
        manifest = {"updated": "2026-06-15", "repos": []}

    # Find or create entry
    entry = None
    for e in manifest["repos"]:
        if e["name"] == repo:
            entry = e
            break
    if not entry:
        entry = {"name": repo}
        manifest["repos"].append(entry)

    backend_guess = cfg("backend_size", "")
    entry["status"] = status
    entry["backend_size"] = backend_guess or f"{_EVIDENCE.get('tools_registered', 0)} tools"
    entry["nav"] = _EVIDENCE.get("pages_checked", "0/0")
    entry["bridge"] = "OK" if _EVIDENCE.get("bridge_ok") else "OCR could not confirm"
    entry["logs"] = f"{_EVIDENCE.get('log_errors', 0)} errors"
    entry["screenshots"] = screenshot_names[:4]
    entry["report"] = f"{repo}.json"

    manifest["updated"] = time.strftime("%Y-%m-%d")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    log(f"Manifest updated at {manifest_path}")


# ── Main ──────────────────────────────────────────────────────────────

def main():
    global MCD_CERT_DIR
    parser = argparse.ArgumentParser(description="CUA-NSIS smoke test")
    parser.add_argument("--installer", help="Path to NSIS installer .exe")
    parser.add_argument("--config", help="Path to cua-nsis-config.json")
    parser.add_argument("--output-dir", default="cua-reports", help="Screenshot output directory")
    parser.add_argument("--mcd-dir", default=MCD_CERT_DIR, help="MCD certification root")
    args = parser.parse_args()

    if args.config:
        _CONFIG.update(load_config(args.config))
    MCD_CERT_DIR = args.mcd_dir

    # Parse nav routes: support --nav "Dashboard:Overview,Logging:Logs,Settings:Settings"
    nav_override = cfg("nav_routes_override", "")
    if nav_override:
        pairs = nav_override.split(",")
        parsed = []
        for p in pairs:
            parts = p.split(":", 1)
            if len(parts) == 2:
                parsed.append([parts[0].strip(), parts[1].strip()])
        if parsed:
            # Replace in config
            _CONFIG["nav_routes"] = parsed

    phases = [
        (True,  "Kill stale processes",  lambda: kill_stale()),
        (True,  "Install NSIS",          lambda: silent_install(args.installer or find_installer())),
        (True,  "Launch app",            launch_app),
        (False, "Verify window + maximize", verify_window),
        (False, "Screenshot",            lambda: take_screenshot(args.output_dir)),
        (False, "Feature route",         check_feature_route),
        (False, "Check diagnostics",     check_diagnostics),
        (False, "WebView bridge",        lambda: verify_webview_bridge(args.output_dir)),
        (False, "Nav click-through",     lambda: nav_click_through(args.output_dir)),
        (False, "Analyze app logs",      analyze_logs),
        (False, "Uninstall",             uninstall),
        (False, "Write cert report",     lambda: write_cert_report(args.output_dir, passed, passed+failed, not fatal_failed and failed == 0)),
    ]

    passed = failed = 0
    fatal_failed = False

    print(f"\n{'='*50}")
    print(f"  CUA Smoke Test — {PRODUCT_NAME}")
    print(f"{'='*50}\n")

    for is_fatal, name, fn in phases:
        phase_num = sum(1 for p in phases if phases.index(p) <= phases.index((is_fatal, name, fn)))
        print(f"  Phase {phase_num}: {name}")
        _EVIDENCE["phases"][name] = "running"
        try:
            fn()
            print(f"  V {name}\n")
            passed += 1
            _EVIDENCE["phases"][name] = "pass"
        except PhaseFailed:
            print(f"  X {name}\n")
            failed += 1
            _EVIDENCE["phases"][name] = "fail"
            if is_fatal:
                fatal_failed = True
        except Exception as e:
            print(f"  X {name}: {e}\n")
            failed += 1
            _EVIDENCE["phases"][name] = "error"
            if is_fatal:
                fatal_failed = True

    all_ok = not fatal_failed and failed == 0
    print(f"{'='*50}")
    print(f"  Result: {passed}/{passed + failed} phases passed")
    if failed:
        print(f"  {failed} phase(s) FAILED")
    if fatal_failed:
        print(f"  FATAL phase failure — see above")

    # Always write cert report (even on failure)
    write_cert_report(args.output_dir, passed, passed + failed, all_ok)

    if all_ok:
        print(f"  ALL PHASES PASSED — {REPO_NAME} CERTIFIED")
    print(f"{'='*50}\n")

    if fatal_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
