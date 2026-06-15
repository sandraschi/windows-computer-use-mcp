"""Serve evidence PNGs for the Targets page (basename lookup in allowed dirs)."""

from __future__ import annotations

import os
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["evidence"])

_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.png$", re.IGNORECASE)


def _evidence_roots() -> list[Path]:
    roots: list[Path] = []
    env_dirs = os.getenv("windows_computer_use_mcp_EVIDENCE_DIRS", "")
    if env_dirs.strip():
        for part in env_dirs.split(";"):
            p = part.strip()
            if p:
                roots.append(Path(p))
    local = os.getenv("LOCALAPPDATA")
    if local:
        roots.append(Path(local) / "cua-mcp" / "evidence")
    docs = Path.home() / "Documents"
    roots.append(docs / "vroid_exports")
    roots.append(docs)
    # Task sessions may write to arbitrary output_dir — scan recent evidence paths
    try:
        from windows_computer_use_mcp import task_engine

        for session in task_engine._TASKS.values():
            for ev in session.evidence:
                for key in ("before_screenshot", "after_screenshot"):
                    raw = ev.get(key)
                    if raw:
                        roots.append(Path(str(raw)).parent)
    except Exception:
        pass
    seen: set[str] = set()
    out: list[Path] = []
    for r in roots:
        key = str(r.resolve()) if r.exists() else str(r)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _resolve_evidence_file(filename: str) -> Path | None:
    if not _SAFE_NAME.match(filename):
        return None
    for root in _evidence_roots():
        if not root.exists():
            continue
        direct = root / filename
        if direct.is_file():
            return direct.resolve()
        try:
            for hit in root.rglob(filename):
                if hit.is_file():
                    return hit.resolve()
        except OSError:
            continue
    return None


@router.get("/download/{filename}")
async def download_evidence(filename: str) -> FileResponse:
    """Return a PNG from known evidence directories by basename only."""
    path = _resolve_evidence_file(filename)
    if not path:
        raise HTTPException(status_code=404, detail=f"Evidence file not found: {filename}")
    return FileResponse(path, media_type="image/png", filename=filename)
