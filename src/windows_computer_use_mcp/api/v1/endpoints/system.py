"""REST surface for host metrics (same data as MCP `automation_system('info')`)."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter

from windows_computer_use_mcp.host_metrics import collect_host_metrics

router = APIRouter(tags=["system"])


@router.get("/info", response_model=dict[str, Any])
async def get_host_info() -> dict[str, Any]:
    """Return live CPU, memory, disk, and network stats from the host process."""
    info = await asyncio.to_thread(collect_host_metrics)
    return {
        "status": "success",
        "operation": "info",
        "info": info,
        "timestamp": datetime.now(UTC).isoformat(),
    }
