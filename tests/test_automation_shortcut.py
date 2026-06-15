"""Tests for automation_shortcut and shortcut_engine."""

from unittest.mock import patch

from windows_computer_use_mcp import shortcut_engine
from windows_computer_use_mcp.app_shortcuts.registry import get_shortcut, list_apps
from windows_computer_use_mcp.tools.models import ShortcutOperationRequest, ToolResult
from windows_computer_use_mcp.tools.portmanteau_shortcut import automation_shortcut


def test_vroid_registry_export():
    spec = get_shortcut("vroidstudio", "export_vrm")
    assert spec.keys == "f8"


def test_list_apps():
    assert "vroidstudio" in list_apps()


@patch("windows_computer_use_mcp.shortcut_engine._send_keys")
@patch("windows_computer_use_mcp.shortcut_engine._wait_stable_after")
def test_send_shortcut(mock_stable, mock_send):
    mock_send.return_value = {"method": "pyautogui", "keys": ["f8"]}
    mock_stable.return_value = {"stable": True}
    result = shortcut_engine.send_shortcut("vroidstudio", "export_vrm", window_handle=12345, verify_stable=True)
    assert result["action"] == "export_vrm"
    mock_send.assert_called_once()


def test_automation_shortcut_list():
    req = ShortcutOperationRequest(operation="list", app="vroidstudio")
    result = automation_shortcut(req)
    assert isinstance(result, ToolResult)
    assert result.status == "success"
    assert len(result.data["shortcuts"]) > 10


def test_automation_shortcut_unknown_action():
    req = ShortcutOperationRequest(operation="send", app="vroidstudio", action="not_a_real_action")
    result = automation_shortcut(req)
    assert result.status == "error"
