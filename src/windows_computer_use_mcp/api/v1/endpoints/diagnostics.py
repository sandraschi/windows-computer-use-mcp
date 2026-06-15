"""Diagnostics endpoint for PyWinAutoMCP.

Returns comprehensive server health, system metrics, tool registration,
error state, and CUA readiness.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from fastapi import APIRouter

from windows_computer_use_mcp.app import OCR_AVAILABLE
from windows_computer_use_mcp.app import app as mcp_app

logger = logging.getLogger(__name__)

router = APIRouter(tags=["diagnostics"])

SERVER_START_TIME = time.time()
VERSION = "0.4.2"
PORT = 10789
CATEGORIES = ["automation", "visual", "system"]


@router.get("/diagnostics", response_model=dict[str, Any])
async def get_diagnostics() -> dict[str, Any]:
    """Return comprehensive diagnostics about the server.

    Includes backend health, system resource usage, registered tool count,
    recent errors, and CUA subsystem status.
    """
    uptime = int(time.time() - SERVER_START_TIME)

    # System metrics via psutil (optional dep)
    cpu_percent = None
    memory_percent = None
    disk_percent = None
    try:
        import psutil

        cpu_percent = psutil.cpu_percent(interval=0.5)
        memory_percent = psutil.virtual_memory().percent
        disk_path = os.environ.get("SystemDrive", "C:") + "\\"
        disk_usage = psutil.disk_usage(disk_path)
        disk_percent = disk_usage.percent
    except Exception:
        pass

    # Tool count from FastMCP app
    tool_count = 0
    if mcp_app is not None:
        try:
            registered = await mcp_app.list_tools()
            tool_count = len(registered)
        except Exception:
            try:
                if hasattr(mcp_app, "_tool_manager") and hasattr(mcp_app._tool_manager, "tools"):
                    tool_count = len(mcp_app._tool_manager.tools)
                elif hasattr(mcp_app, "_tools"):
                    tool_count = len(mcp_app._tools)
            except Exception:
                pass

    # Recent errors (extend with ActivityLog when available)
    error_count = 0
    recent_errors: list[str] = []

    # CUA status
    tesseract_available = bool(OCR_AVAILABLE)
    if not tesseract_available:
        try:
            import subprocess
            result = subprocess.run(
                [r"C:\Program Files\Tesseract-OCR\tesseract.exe", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            tesseract_available = result.returncode == 0
        except Exception:
            pass

    window_found = False
    try:
        import pywinauto

        app = pywinauto.Application(backend="uia").connect(title_re="Pywinauto MCP")
        win = app.window(title_re="Pywinauto MCP")
        win.wait("visible", timeout=2)
        window_found = True
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "backend": {
                "status": "ok",
                "version": VERSION,
                "uptime_seconds": uptime,
                "port": PORT,
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
            },
            "tools": {
                "total": tool_count,
                "categories": CATEGORIES,
            },
            "errors": {
                "count": error_count,
                "recent": recent_errors,
            },
            "cua_status": {
                "window_found": window_found,
                "backend_reachable": True,
                "tesseract_available": tesseract_available or OCR_AVAILABLE,
            },
        },
    }
