"""In-memory window snapshots for Cua-style element_index addressing."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class WindowSnapshot:
    """UI state captured for one top-level window."""

    snapshot_id: str
    window_handle: int
    capture_mode: str
    elements: list[dict[str, Any]]
    created_at: float = field(default_factory=time.time)
    screenshot_base64: str | None = None


class SnapshotStore:
    """Process-local snapshot cache (MCP session lifetime)."""

    def __init__(self, max_snapshots: int = 32) -> None:
        self._max = max_snapshots
        self._by_id: dict[str, WindowSnapshot] = {}
        self._hwnd_hash: dict[int, str] = {}

    def invalidate_for_handle(self, window_handle: int, ui_hash: str | None = None) -> int:
        """Drop snapshots for HWND when UI hash changes (T1.7)."""
        if ui_hash and self._hwnd_hash.get(window_handle) == ui_hash:
            return 0
        if ui_hash:
            self._hwnd_hash[window_handle] = ui_hash
        stale = [sid for sid, s in self._by_id.items() if s.window_handle == window_handle]
        for sid in stale:
            del self._by_id[sid]
        return len(stale)

    def put(
        self,
        *,
        window_handle: int,
        capture_mode: str,
        elements: list[dict[str, Any]],
        screenshot_base64: str | None = None,
    ) -> str:
        snapshot_id = str(uuid.uuid4())
        while len(self._by_id) >= self._max:
            oldest = min(self._by_id.values(), key=lambda s: s.created_at)
            del self._by_id[oldest.snapshot_id]
        self._by_id[snapshot_id] = WindowSnapshot(
            snapshot_id=snapshot_id,
            window_handle=window_handle,
            capture_mode=capture_mode,
            elements=elements,
            screenshot_base64=screenshot_base64,
        )
        return snapshot_id

    def get(self, snapshot_id: str) -> WindowSnapshot | None:
        return self._by_id.get(snapshot_id)

    def resolve_element(self, snapshot_id: str, element_index: int) -> dict[str, Any] | None:
        snap = self.get(snapshot_id)
        if snap is None:
            return None
        for elem in snap.elements:
            if elem.get("element_index") == element_index:
                return elem
        return None


_store = SnapshotStore()


def get_snapshot_store() -> SnapshotStore:
    return _store
