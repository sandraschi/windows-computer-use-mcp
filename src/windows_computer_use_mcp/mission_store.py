"""In-memory mission step recording for replay."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from windows_computer_use_mcp.cua_env import cua_getenv

_STORE: dict[str, list[dict[str, Any]]] = {}


def _persist_dir() -> Path:
    base = cua_getenv(
        "CUA_MCP_MISSION_DIR",
        "windows_computer_use_mcp_MISSION_DIR",
        default=None,
    )
    if base:
        path = Path(base)
    else:
        path = Path.home() / ".cua-mcp" / "missions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def record_step(mission_id: str, step: dict[str, Any]) -> None:
    steps = _STORE.setdefault(mission_id, [])
    steps.append({**step, "ts": time.time()})
    file_path = _persist_dir() / f"{mission_id}.jsonl"
    with file_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(step) + "\n")


def get_steps(mission_id: str) -> list[dict[str, Any]]:
    if mission_id in _STORE:
        return list(_STORE[mission_id])
    file_path = _persist_dir() / f"{mission_id}.jsonl"
    if not file_path.is_file():
        return []
    steps = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            steps.append(json.loads(line))
    _STORE[mission_id] = steps
    return list(steps)


def clear_mission(mission_id: str) -> None:
    _STORE.pop(mission_id, None)
    file_path = _persist_dir() / f"{mission_id}.jsonl"
    if file_path.is_file():
        file_path.unlink()
