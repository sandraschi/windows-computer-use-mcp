"""Retry helper — wires RETRY_ATTEMPTS / RETRY_DELAY from config."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

from windows_computer_use_mcp.cua_env import cua_getenv

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_attempts() -> int:
    raw = cua_getenv("CUA_MCP_RETRY_ATTEMPTS", "windows_computer_use_mcp_RETRY_ATTEMPTS", "RETRY_ATTEMPTS", default="3")
    return max(1, int(raw or "3"))


def retry_delay() -> float:
    raw = cua_getenv("CUA_MCP_RETRY_DELAY", "windows_computer_use_mcp_RETRY_DELAY", "RETRY_DELAY", default="1.0")
    return max(0.0, float(raw or "1.0"))


def with_retry(
    fn: Callable[[], T],
    *,
    attempts: int | None = None,
    delay: float | None = None,
    label: str = "operation",
) -> T:
    """Execute fn with exponential backoff retries."""
    max_attempts = attempts or retry_attempts()
    base_delay = delay if delay is not None else retry_delay()
    last_exc: Exception | None = None

    for attempt in range(max_attempts):
        try:
            return fn()
        except Exception as exc:
            last_exc = exc
            if attempt >= max_attempts - 1:
                break
            wait = min(base_delay * (2**attempt), 10.0)
            logger.warning("%s failed (attempt %d/%d): %s — retry in %.1fs", label, attempt + 1, max_attempts, exc, wait)
            time.sleep(wait)

    assert last_exc is not None
    raise last_exc


def retry_tool_result(check_success: Callable[[Any], bool], fn: Callable[[], Any], *, label: str = "tool") -> Any:
    """Retry when fn returns a result that fails check_success (e.g. ToolResult status)."""

    def _run():
        result = fn()
        if check_success(result):
            return result
        msg = getattr(result, "message", None) or (result.get("message") if isinstance(result, dict) else str(result))
        raise RuntimeError(msg or f"{label} failed")

    return with_retry(_run, label=label)
