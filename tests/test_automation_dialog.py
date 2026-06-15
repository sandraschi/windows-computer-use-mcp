"""Tests for automation_dialog and dialog_engine."""

from unittest.mock import MagicMock, patch

import pytest

from windows_computer_use_mcp import dialog_engine
from windows_computer_use_mcp.tools.models import DialogOperationRequest, ToolResult
from windows_computer_use_mcp.tools.portmanteau_dialog import automation_dialog


class TestDialogEngine:
    @patch("windows_computer_use_mcp.dialog_engine.pyautogui")
    @patch("windows_computer_use_mcp.dialog_engine.pyperclip")
    def test_submit_path_clipboard(self, mock_clip, mock_gui):
        dialog_engine.CLIPBOARD_AVAILABLE = True
        result = dialog_engine.submit_path(r"D:\exports\model.vrm", use_clipboard=True)
        mock_clip.copy.assert_called_once_with(r"D:\exports\model.vrm")
        mock_gui.hotkey.assert_any_call("ctrl", "v")
        mock_gui.press.assert_called_with("enter")
        assert result["submitted"] is True
        assert result["method"] == "clipboard"

    @patch("windows_computer_use_mcp.dialog_engine.pyautogui")
    def test_set_path_type_fallback(self, mock_gui):
        dialog_engine.CLIPBOARD_AVAILABLE = False
        result = dialog_engine.set_path_field("short.vrm", use_clipboard=True)
        mock_gui.write.assert_called_once()
        assert result["method"] == "type"


class TestAutomationDialogTool:
    @patch("windows_computer_use_mcp.tools.portmanteau_dialog.dialog_engine.submit_path")
    def test_submit_path_operation(self, mock_submit):
        mock_submit.return_value = {"method": "clipboard", "submitted": True, "confirm_key": "enter", "pause_s": 0.3}
        req = DialogOperationRequest(operation="submit_path", path=r"C:\out\a.vrm")
        result = automation_dialog(req)
        assert isinstance(result, ToolResult)
        assert result.status == "success"
        mock_submit.assert_called_once()

    def test_submit_path_requires_path(self):
        req = DialogOperationRequest(operation="submit_path")
        result = automation_dialog(req)
        assert result.status == "error"
