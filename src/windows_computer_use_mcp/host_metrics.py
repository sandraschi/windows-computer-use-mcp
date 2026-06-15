"""Host metrics shared by `automation_system('info')` and the REST API."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import psutil


def _system_disk_path() -> str:
    """Best-effort root volume for disk usage (Windows: system drive)."""
    if os.name == "nt":
        return os.environ.get("SystemDrive", "C:") + "\\"
    return "/"


def collect_host_metrics() -> dict[str, Any]:
    """CPU, memory, disk, network, and OS fields (matches MCP `info` operation)."""
    cpu_percent = psutil.cpu_percent(interval=1)
    virtual_memory = psutil.virtual_memory()
    disk_path = _system_disk_path()
    disk_usage = psutil.disk_usage(disk_path)
    net_io = psutil.net_io_counters()

    window_count: int | None = None
    try:
        import pygetwindow as gw

        window_count = len(gw.getAllWindows())
    except Exception:
        pass

    return {
        "cpu_percent": cpu_percent,
        "memory_total_gb": round(virtual_memory.total / (1024**3), 2),
        "memory_available_gb": round(virtual_memory.available / (1024**3), 2),
        "memory_percent": virtual_memory.percent,
        "disk_path": disk_path,
        "disk_total_gb": round(disk_usage.total / (1024**3), 2),
        "disk_used_gb": round(disk_usage.used / (1024**3), 2),
        "disk_percent": disk_usage.percent,
        "network_bytes_sent_mb": round(net_io.bytes_sent / (1024**2), 2),
        "network_bytes_recv_mb": round(net_io.bytes_recv / (1024**2), 2),
        "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        "os_name": os.name,
        "os_platform": os.sys.platform,
        "window_count": window_count,
    }
