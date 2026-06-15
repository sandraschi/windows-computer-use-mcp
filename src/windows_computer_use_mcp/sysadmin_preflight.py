"""Resource and process preflight via system-admin-mcp."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any

from windows_computer_use_mcp.sysadmin_client import system_admin_operation

logger = logging.getLogger(__name__)


def run_sync_preflight(
    *,
    output_dir: str | None = None,
    min_memory_mb: float = 2048.0,
    min_disk_mb: float = 500.0,
    max_cpu_percent: float = 95.0,
    filter_process: str | None = None,
    sysadmin_url: str | None = None,
) -> dict[str, Any]:
    """Check disk, memory, CPU, and optional process before automation."""
    checks: list[dict[str, Any]] = []
    warnings: list[str] = []

    out = Path(output_dir) if output_dir else Path.cwd()
    disk = shutil.disk_usage(out)
    free_mb = disk.free / (1024 * 1024)
    disk_ok = free_mb >= min_disk_mb
    checks.append(
        {
            "name": "disk_free",
            "path": str(out),
            "free_mb": round(free_mb, 1),
            "min_mb": min_disk_mb,
            "passed": disk_ok,
        }
    )
    if not disk_ok:
        return {
            "ok": False,
            "checks": checks,
            "warnings": warnings,
            "error": f"Insufficient disk on {out}: {free_mb:.0f}MB < {min_disk_mb}MB",
        }

    perf = system_admin_operation("get_performance_metrics", base_url=sysadmin_url)
    if not perf.get("success"):
        warnings.append(f"system-admin unavailable: {perf.get('error')}")
        checks.append({"name": "memory", "skipped": True})
    else:
        data = perf.get("data") or {}
        mem = data.get("memory") or {}
        avail_mb = float(mem.get("available_bytes") or 0) / (1024 * 1024)
        mem_ok = avail_mb >= min_memory_mb
        checks.append(
            {
                "name": "memory_available",
                "available_mb": round(avail_mb, 1),
                "min_mb": min_memory_mb,
                "passed": mem_ok,
            }
        )
        if not mem_ok:
            return {
                "ok": False,
                "checks": checks,
                "warnings": warnings,
                "error": f"Low memory: {avail_mb:.0f}MB < {min_memory_mb}MB",
            }

        cpu_total = float((data.get("cpu") or {}).get("total_percent") or 0)
        checks.append(
            {
                "name": "cpu_load",
                "total_percent": cpu_total,
                "max_percent": max_cpu_percent,
                "passed": cpu_total <= max_cpu_percent,
            }
        )
        if cpu_total > max_cpu_percent:
            warnings.append(f"High CPU ({cpu_total:.0f}%)")

    if filter_process:
        proc = system_admin_operation(
            "list_processes",
            filter_name=filter_process,
            page_size=5,
            base_url=sysadmin_url,
        )
        count = 0
        if proc.get("success"):
            data = proc.get("data") or {}
            count = int(data.get("total") or 0)
        checks.append({"name": "process", "filter": filter_process, "count": count, "passed": count > 0})
        if count == 0:
            return {
                "ok": False,
                "checks": checks,
                "warnings": warnings,
                "error": f"Process not found: {filter_process}",
            }

    return {"ok": True, "checks": checks, "warnings": warnings}
