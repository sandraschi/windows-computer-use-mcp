"""Tests for Cua Driver parity helpers."""

from windows_computer_use_mcp.desktop_state.capture import _legacy_capture_mode, normalize_elements_for_snapshot
from windows_computer_use_mcp.dispatch import (
    BACKGROUND_UNAVAILABLE,
    background_unavailable_result,
    default_dispatch_mode,
    resolve_dispatch,
)
from windows_computer_use_mcp.snapshot_store import SnapshotStore


def test_legacy_capture_mode():
    assert _legacy_capture_mode(False, False) == "ax"
    assert _legacy_capture_mode(True, False) == "som"
    assert _legacy_capture_mode(False, True) == "som"


def test_normalize_elements_for_snapshot():
    raw = [{"type": "Button", "id": 0}, {"type": "Edit", "id": 1}]
    out = normalize_elements_for_snapshot(raw)
    assert out[0]["element_index"] == 0
    assert out[1]["element_index"] == 1
    assert "id" not in out[0]


def test_snapshot_store_roundtrip():
    store = SnapshotStore(max_snapshots=2)
    sid = store.put(
        window_handle=100,
        capture_mode="ax",
        elements=[{"element_index": 0, "type": "Button"}],
    )
    snap = store.get(sid)
    assert snap is not None
    assert snap.window_handle == 100
    elem = store.resolve_element(sid, 0)
    assert elem is not None
    assert elem["type"] == "Button"


def test_resolve_dispatch_explicit():
    assert resolve_dispatch("background") == "background"
    assert resolve_dispatch("foreground") == "foreground"
    assert default_dispatch_mode() == "foreground"


def test_background_unavailable_shape():
    meta = background_unavailable_result("test reason", attempted=["invoke"])
    assert meta["code"] == BACKGROUND_UNAVAILABLE
    assert meta["background_unavailable"] is True
