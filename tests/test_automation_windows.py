"""Tests for the automation_windows portmanteau tool."""

from unittest.mock import MagicMock

from windows_computer_use_mcp.tools.models import WindowOperationRequest
from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows


class TestAutomationWindows:
    """Tests for automation_windows tool operations."""

    def test_window_list(self, mock_desktop_uia, verify_result):
        """Test listing all visible windows."""
        mock_window = MagicMock()
        mock_window.window_text.return_value = "Test Window"
        mock_window.handle = 12345
        mock_window.class_name.return_value = "TestClass"
        mock_window.process_id.return_value = 1000

        mock_desktop_uia.windows.return_value = [mock_window]

        req = WindowOperationRequest(operation="list")
        result = automation_windows(req)

        verify_result(result, expected_keys=["count", "windows"])
        assert len(result.data["windows"]) == 1
        assert result.data["windows"][0]["title"] == "Test Window"

    def test_window_find(self, mock_desktop_uia, verify_result):
        """Test finding a window by title."""
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.handle = 12345
        mock_window.window_text.return_value = "Notepad"

        mock_desktop_uia.windows.return_value = [mock_window]

        req = WindowOperationRequest(operation="find", title="Notepad")
        result = automation_windows(req)

        verify_result(result, expected_keys=["count", "windows"])
        assert result.data["count"] >= 1
        assert result.data["windows"][0]["handle"] == 12345
        mock_desktop_uia.windows.assert_called()

    def test_window_maximize(self, mock_desktop_uia, verify_result):
        """Test maximizing a window."""
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_desktop_uia.window.return_value = mock_window

        req = WindowOperationRequest(operation="maximize", handle=12345)
        result = automation_windows(req)

        verify_result(result)
        mock_window.maximize.assert_called_once()

    def test_window_minimize(self, mock_desktop_uia, verify_result):
        """Test minimizing a window."""
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_desktop_uia.window.return_value = mock_window

        req = WindowOperationRequest(operation="minimize", handle=12345)
        result = automation_windows(req)

        verify_result(result)
        mock_window.minimize.assert_called_once()

    def test_window_close(self, mock_desktop_uia, verify_result):
        """Test closing a window."""
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_desktop_uia.window.return_value = mock_window

        req = WindowOperationRequest(operation="close", handle=12345)
        result = automation_windows(req)

        verify_result(result)
        mock_window.close.assert_called_once()

    def test_window_position(self, mock_desktop_uia, verify_result):
        """Test moving and resizing a window."""
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_desktop_uia.window.return_value = mock_window

        req = WindowOperationRequest(operation="position", handle=12345, x=100, y=100, width=800, height=600)
        result = automation_windows(req)

        verify_result(result)
        mock_window.move_window.assert_called_once_with(x=100, y=100, width=800, height=600)

    def test_window_title(self, mock_desktop_uia, verify_result):
        """Test getting window title."""
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.window_text.return_value = "Test Window Title"
        mock_desktop_uia.window.return_value = mock_window

        req = WindowOperationRequest(operation="title", handle=12345)
        result = automation_windows(req)

        verify_result(result, expected_keys=["title"])
        assert result.data["title"] == "Test Window Title"
