"""Append-only JSONL trajectory log for agent replay (Cua parity Phase 3)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

ENV_TRAJECTORY_LOG = "windows_computer_use_mcp_TRAJECTORY_LOG"


def _trajectory_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or os.getenv("USERPROFILE") or str(Path.home())
    return Path(base) / "windows-computer-use-mcp" / "trajectories"


def trajectory_enabled() -> bool:
    val = os.getenv(ENV_TRAJECTORY_LOG, "").strip().lower()
    return val in ("1", "true", "yes", "on")


def trajectory_path() -> Path:
    day = time.strftime("%Y%m%d")
    d = _trajectory_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / f"session-{day}.jsonl"


def log_trajectory(event: str, **fields: Any) -> None:
    """Append one JSON line when trajectory logging is enabled."""
    if not trajectory_enabled():
        return
    row = {"ts": time.time(), "event": event, **fields}
    try:
        with trajectory_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")
    except OSError:
        pass
