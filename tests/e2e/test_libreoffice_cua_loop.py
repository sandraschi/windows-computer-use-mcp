"""E2E: Cua-shaped loop against live LibreOffice Calc (pairs with libreoffice-mcp fleet)."""

from __future__ import annotations

import pytest

from windows_computer_use_mcp.desktop_state.capture import DesktopStateCapture, normalize_elements_for_snapshot
from windows_computer_use_mcp.snapshot_store import SnapshotStore
from windows_computer_use_mcp.tools.models import ElementOperationRequest, WindowStateRequest
from windows_computer_use_mcp.tools.portmanteau_elements import automation_elements
from windows_computer_use_mcp.tools.window_state import get_window_state

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.libreoffice,
    pytest.mark.windows_only,
    pytest.mark.requires_gui,
]


def test_calc_get_window_state_ax(libreoffice_calc):
    handle = libreoffice_calc["handle"]
    req = WindowStateRequest(window_handle=handle, capture_mode="ax", max_depth=6)
    result = get_window_state(req)
    assert result.status == "success", result.message
    assert result.data["element_count"] >= 1, result.data.get("text", result.message)
    assert result.data["snapshot_id"]
    assert result.data["elements"][0]["element_index"] == 0


def test_calc_capture_modes(libreoffice_calc):
    handle = libreoffice_calc["handle"]
    capturer = DesktopStateCapture(max_depth=5, element_timeout=0.3)
    ax = capturer.capture(capture_mode="ax", window_handle=handle)
    assert ax["capture_mode"] == "ax"
    assert ax["element_count"] >= 1
    vision = capturer.capture(capture_mode="vision", window_handle=handle)
    assert vision["capture_mode"] == "vision"
    assert vision.get("screenshot_base64"), "vision mode should return a window screenshot"


def test_calc_snapshot_store_roundtrip(libreoffice_calc):
    handle = libreoffice_calc["handle"]
    capturer = DesktopStateCapture(max_depth=4, element_timeout=0.3)
    raw = capturer.capture(capture_mode="ax", window_handle=handle)
    elements = normalize_elements_for_snapshot(raw.get("interactive_elements") or [])
    store = SnapshotStore()
    sid = store.put(window_handle=handle, capture_mode="ax", elements=elements)
    assert store.resolve_element(sid, 0) is not None


@pytest.mark.slow
def test_calc_background_click_reports_blocked_or_success(libreoffice_calc):
    """Background click may succeed (invoke) or return background_unavailable — both are valid signals."""
    handle = libreoffice_calc["handle"]
    state = get_window_state(WindowStateRequest(window_handle=handle, capture_mode="ax", max_depth=8))
    assert state.status == "success"
    if not state.data["elements"]:
        pytest.skip("No interactive elements in Calc snapshot (UIA tree empty on this host)")
    sid = state.data["snapshot_id"]
    idx = state.data["elements"][0]["element_index"]
    click_req = ElementOperationRequest(
        window_handle=handle,
        operation="click",
        snapshot_id=sid,
        element_index=idx,
        dispatch="background",
    )
    click_result = automation_elements(click_req)
    assert click_result.status in ("success", "blocked")
    if click_result.status == "blocked":
        assert click_result.data.get("code") == "background_unavailable"
