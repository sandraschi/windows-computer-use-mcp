"""Unified retry policy with strategy selection (refocus, wait_stable, fallback, escalate)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from windows_computer_use_mcp.retry import retry_attempts, retry_delay

logger = logging.getLogger(__name__)


class RetryStrategy(StrEnum):
    refocus = "refocus"
    wait_stable = "wait_stable"
    fallback_selector = "fallback_selector"
    escalate = "escalate"


@dataclass
class RetryResult:
    success: bool
    message: str
    data: dict[str, Any] | None = None
    strategy_used: RetryStrategy | None = None
    attempts: int = 0


class RetryPolicy:
    """Unified retry with pluggable strategy chain.

    Strategies run in priority order. Each strategy is tried `max_attempts`
    times before the next strategy is attempted.
    """

    def __init__(
        self,
        *,
        max_attempts: int | None = None,
        base_delay: float | None = None,
        strategies: list[RetryStrategy] | None = None,
    ):
        self.max_attempts = max_attempts or retry_attempts()
        self.base_delay = base_delay if base_delay is not None else retry_delay()
        self.strategies = strategies or [
            RetryStrategy.refocus,
            RetryStrategy.wait_stable,
            RetryStrategy.fallback_selector,
            RetryStrategy.escalate,
        ]

    def execute(
        self,
        action_fn: Callable[[], Any],
        *,
        verify_fn: Callable[[Any], bool] | None = None,
        refocus_fn: Callable[[], None] | None = None,
        label: str = "action",
    ) -> RetryResult:
        """Execute action_fn with retry, optionally verifying each attempt.

        If verify_fn is provided, the result is checked after each attempt.
        If verify_fn fails, the strategy chain kicks in:
          1. refocus — re-activate the target window, retry
          2. wait_stable — wait for UI to stabilize, retry
          3. fallback_selector — if available, the caller handles this
          4. escalate — return partial success with recovery_tip
        """
        last_result: Any = None
        last_error: str | None = None
        total_attempts = 0

        for strategy in self.strategies:
            for attempt in range(self.max_attempts):
                total_attempts += 1
                try:
                    if strategy == RetryStrategy.refocus and refocus_fn and attempt > 0:
                        refocus_fn()
                        time.sleep(self.base_delay)

                    if strategy == RetryStrategy.wait_stable and attempt > 0:
                        self._wait_stable()

                    result = action_fn()
                    last_result = result

                    if verify_fn is None or verify_fn(result):
                        return RetryResult(
                            success=True,
                            message=f"{label} succeeded on strategy={strategy.value} attempt={attempt + 1}",
                            data={"result": result} if not isinstance(result, dict) else result,
                            strategy_used=strategy,
                            attempts=total_attempts,
                        )

                    msg = self._extract_message(result)
                    last_error = f"verify failed: {msg}"

                except Exception as e:
                    last_error = f"exception: {e!s}"
                    logger.warning(
                        "%s failed (strategy=%s attempt=%d/%d): %s",
                        label, strategy.value, attempt + 1, self.max_attempts, last_error,
                    )

                if attempt < self.max_attempts - 1:
                    wait = min(self.base_delay * (2**attempt), 10.0)
                    time.sleep(wait)

        return RetryResult(
            success=False,
            message=f"{label} failed after {total_attempts} attempts. Last error: {last_error or 'unknown'}",
            data={"last_result": last_result, "error": last_error},
            strategy_used=RetryStrategy.escalate,
            attempts=total_attempts,
        )

    def _wait_stable(self, timeout: float = 5.0) -> None:
        """Simple poll: sleep a bit to let the UI settle."""
        time.sleep(min(timeout, 3.0))

    def _extract_message(self, result: Any) -> str:
        if isinstance(result, dict):
            return result.get("message") or result.get("error") or str(result)
        return getattr(result, "message", None) or str(result)


def retry_with_policy(
    action_fn: Callable[[], Any],
    *,
    verify_fn: Callable[[Any], bool] | None = None,
    refocus_fn: Callable[[], None] | None = None,
    label: str = "action",
) -> RetryResult:
    """Convenience: run a single action through the default retry policy."""
    policy = RetryPolicy()
    return policy.execute(action_fn, verify_fn=verify_fn, refocus_fn=refocus_fn, label=label)
