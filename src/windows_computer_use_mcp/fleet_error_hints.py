"""Fleet error hints - depot-backed self-healing for mission retries (W5).

The depot (depot-mcp, port 10727) aggregates fleet_error/v1 records pushed by
every fleet server. When a mission step fails, the runner records the failure
locally (ring buffer via fleet_error_telemetry.py) and pulls recovery hints
from the depot for the same tool + error_type pattern, so the next attempt -
or the agent reviewing the result - can prefer recorded hints over blind retry.

Everything here fails soft: a dead depot or a write error never breaks the
mission loop. See mcp-central-docs patterns/FLEET_ERROR_TELEMETRY.md.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import httpx

from windows_computer_use_mcp.fleet_error_telemetry import (
    record_fleet_error,
)

logger = logging.getLogger(__name__)

_DEPOT_URL = (
    os.environ.get("windows_computer_use_mcp_DEPOT_URL") or os.environ.get("DEPOT_URL") or "http://127.0.0.1:10727"
).rstrip("/")

_DB_PATH = Path(__file__).resolve().parent / "data" / "fleet_errors.sqlite3"

_ERROR_TYPE_HINTS = (
    ("timeout", "timeout"),
    ("timed out", "timeout"),
    ("not found", "element_not_found"),
    ("elementnotfound", "element_not_found"),
    ("no element", "element_not_found"),
    ("access denied", "access_denied"),
    ("permission", "access_denied"),
    ("not implemented", "not_implemented"),
    ("connection refused", "connection_error"),
    ("failed to connect", "connection_error"),
    ("invalid parameter", "validation"),
    ("unexpected keyword", "validation"),
)


def fleet_error_type_for(message: str | None) -> str:
    """Map an error message or exception name to a categorical fleet error type."""
    text = (message or "").lower()
    for needle, error_type in _ERROR_TYPE_HINTS:
        if needle in text:
            return error_type
    return "mission_step_error"


def record_fleet_failure(
    *,
    tool: str,
    operation: str | None,
    error_type: str,
    message: str,
    params: dict | None = None,
) -> None:
    """Record a mission step failure into the local fleet_error ring buffer."""
    try:
        record_fleet_error(
            server="windows-computer-use-mcp",
            tool=tool,
            operation=operation,
            error_type=error_type,
            message=message,
            params=params,
            db_path=str(_DB_PATH),
        )
    except Exception:
        logger.debug("fleet failure record skipped", exc_info=True)


def fetch_depot_hints(*, tool: str, error_type: str, limit: int = 3) -> list[str]:
    """Pull recovery hints for tool + error_type from the depot. Fail-soft."""
    try:
        response = httpx.get(
            f"{_DEPOT_URL}/api/v1/fleet/errors/query",
            params={"tool": tool, "error_type": error_type, "limit": limit},
            timeout=2.0,
        )
        if response.status_code != 200:
            return []
        results = response.json().get("results", [])
    except Exception:
        logger.debug("depot hint query failed (offline?)", exc_info=True)
        return []

    hints: list[str] = []
    seen: set[str] = set()
    for record in results:
        recovery = record.get("recovery")
        if isinstance(recovery, list):
            for hint in recovery:
                if hint and hint not in seen:
                    seen.add(hint)
                    hints.append(hint)
    return hints


def fetch_or_local_hints(*, tool: str, error_type: str, limit: int = 3) -> list[str]:
    """Depot hints first, local ring buffer as offline fallback."""
    hints = fetch_depot_hints(tool=tool, error_type=error_type, limit=limit)
    if hints:
        return hints
    try:
        from windows_computer_use_mcp.fleet_error_telemetry import query_fleet_errors

        for record in query_fleet_errors(tool=tool, error_type=error_type, last_n=limit, db_path=str(_DB_PATH)):
            recovery = record.get("recovery")
            if isinstance(recovery, list):
                hints.extend(h for h in recovery if h)
    except Exception:
        logger.debug("local hint fallback failed", exc_info=True)
    return hints
