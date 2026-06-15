"""Environment-aware test scaffold (aligned with mcp-central-docs).

**Canonical reference:** ``mcp-central-docs/standards/testing-environment-aware.md``

**windows-computer-use-mcp adaptation:** This server depends on a **local Windows session** and sometimes **OpenCV /
USB cameras**, not LAN-only IoT. Therefore ``requires_hardware`` means: **skip in CI**, **allow on any
local developer machine** where ``CI`` is unset — you do **not** need ``local_with_iot`` (router
probe) to run webcam tests.

Signals:
  * ``CI=true`` → ``ci`` (GitHub Actions: no real desktop, mock or HTTP-only tests)
  * Else + LAN probe succeeds → ``local_with_iot`` (optional, for future LAN-dependent tools)
  * Else → ``local_no_iot`` (local PC, hardware may still be off)

Markers:
  * ``requires_hardware`` — real OpenCV / camera / host-only paths; **skipped in CI**
  * ``requires_network`` — skipped in CI
  * ``ci_only`` — only runs when ``CI=true``
  * ``destructive`` — mutating real UI; **skipped in CI** (run locally with care)
  * ``slow`` — opt-in slow tests
"""

from __future__ import annotations

import os
import socket
from typing import Literal

import pytest

EnvType = Literal["ci", "local_no_iot", "local_with_iot"]


def _detect_environment() -> EnvType:
    if os.environ.get("CI", "").lower() in ("true", "1", "yes"):
        return "ci"

    probe_ip = os.environ.get("IOT_PROBE_IP", "192.168.1.1")
    probe_port = int(os.environ.get("IOT_PROBE_PORT", "80"))
    timeout = float(os.environ.get("IOT_PROBE_TIMEOUT", "1.5"))

    try:
        with socket.create_connection((probe_ip, probe_port), timeout=timeout):
            return "local_with_iot"
    except (OSError, TimeoutError):
        return "local_no_iot"


ENV: EnvType = _detect_environment()


def _probe_device(ip: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (OSError, TimeoutError):
        return False


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "requires_hardware: needs local Windows host (OpenCV/camera/desktop) — skipped in CI",
    )
    config.addinivalue_line(
        "markers",
        "requires_network: needs LAN — skipped in CI",
    )
    config.addinivalue_line(
        "markers",
        "ci_only: contract tests meant for CI — skipped on local unless CI=true",
    )
    config.addinivalue_line(
        "markers",
        "slow: opt-in slow tests",
    )
    config.addinivalue_line(
        "markers",
        "destructive: real UI/input — skipped in CI; run locally with operator awareness",
    )


def pytest_runtest_setup(item: pytest.Item) -> None:
    env = ENV

    # Fork from generic "IoT only" rule: hardware here = local machine, not LAN probe.
    if item.get_closest_marker("requires_hardware") and env == "ci":
        pytest.skip(
            "requires_hardware: skipped in CI — run on local Windows with OpenCV/devices. "
            "See mcp-central-docs standards/testing-environment-aware.md"
        )

    if item.get_closest_marker("requires_network") and env == "ci":
        pytest.skip("requires_network: no local network in CI")

    if item.get_closest_marker("ci_only") and env != "ci":
        pytest.skip("ci_only: skipping on local (set CI=true to force)")

    if item.get_closest_marker("destructive") and env == "ci":
        pytest.skip("destructive: skipped in CI — run locally with PYWINAUTO_TEST_REAL_WINDOWS etc.")


@pytest.fixture(scope="session", autouse=True)
def environment_report() -> None:
    env_labels = {
        "ci": "CI — hardware-marked tests skipped; use mocks",
        "local_no_iot": "Local — LAN probe failed; USB/integrated camera may still work",
        "local_with_iot": "Local — LAN probe OK; optional IoT + desktop tests",
    }
    print(f"\n[pytest env] ENV={ENV} — {env_labels[ENV]}")


def skip_if_device_unreachable(ip: str, port: int, label: str) -> None:
    """Skip if a specific LAN device is not reachable (optional fine-grained skip)."""
    if not _probe_device(ip, port):
        pytest.skip(f"Device unreachable: {label} at {ip}:{port}")
