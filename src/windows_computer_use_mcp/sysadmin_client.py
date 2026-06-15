"""Sync HTTP client for system-admin-mcp crossconnect."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)


def default_sysadmin_url() -> str:
    return os.environ.get("SYSTEM_ADMIN_MCP_URL", "http://127.0.0.1:10861")


def call_system_admin_tool(
    tool_name: str,
    arguments: dict[str, Any],
    *,
    base_url: str | None = None,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Call system-admin-mcp POST /api/tools/call."""
    url = (base_url or default_sysadmin_url()).rstrip("/") + "/api/tools/call"
    payload = {"name": tool_name, "arguments": arguments}
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            body = response.json()
    except httpx.HTTPError as exc:
        logger.warning("system-admin-mcp call failed tool=%s error=%s", tool_name, exc)
        return {"success": False, "error": str(exc)}

    if body.get("status") == "error":
        return {"success": False, "error": body.get("message", "tool error")}

    result = body.get("result")
    if isinstance(result, dict) and result.get("status") == "error":
        return {"success": False, "error": result.get("error", "tool error"), "data": result}

    return {"success": True, "result": result, "data": result}


def system_admin_operation(operation: str, *, base_url: str | None = None, **fields: Any) -> dict[str, Any]:
    return call_system_admin_tool("system_admin", {"operation": operation, **fields}, base_url=base_url)
