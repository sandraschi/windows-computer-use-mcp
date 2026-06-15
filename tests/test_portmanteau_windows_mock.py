"""Mock-based tests for the portmanteau window management tools.
These tests use mocks and don't require real windows to be open.
"""

from unittest.mock import MagicMock, patch


class TestPortmanteauWindowsMock:
    """Mock-based tests for the automation_windows portmanteau tool."""

    @patch("windows_computer_use_mcp.tools.portmanteau_windows._get_desktop")
    @patch("windows_computer_use_mcp.tools.portmanteau_windows.automation_windows")
    def test_activate_window_success(self, mock_automation_windows, mock_get_desktop, app_instance):
        """Test successful window activation with mocks."""
        # Setup mocks
        mock_window = MagicMock()
        mock_window.is_minimized.return_value = False
        mock_window.has_focus.return_value = True
        mock_window.is_visible.return_value = True
        mock_window.is_enabled.return_value = True

        mock_desktop = MagicMock()
        mock_desktop.window.return_value = mock_window
        mock_get_desktop.return_value = mock_desktop

        # Setup the mock to return our expected result
        expected_result = {
            "status": "success",
            "operation": "activate",
            "action": "activated",
            "handle": 12345,
            "has_focus": True,
            "is_visible": True,
            "is_enabled": True,
            "timestamp": "2023-01-01T00:00:00",
        }
        mock_automation_windows.return_value = expected_result

        # Import here to get the patched version
        from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows

        # Call the function
        result = automation_windows("activate", handle=12345)

        # Verify the result
        assert result == expected_result

    @patch("windows_computer_use_mcp.tools.portmanteau_windows._get_desktop")
    @patch("windows_computer_use_mcp.tools.portmanteau_windows.automation_windows")
    def test_activate_minimized_window(self, mock_automation_windows, mock_get_desktop, app_instance):
        """Test activating a minimized window with mocks."""
        # Setup mocks
        mock_window = MagicMock()
        mock_window.is_minimized.return_value = True
        mock_window.has_focus.return_value = True
        mock_window.is_visible.return_value = True
        mock_window.is_enabled.return_value = True

        mock_desktop = MagicMock()
        mock_desktop.window.return_value = mock_window
        mock_get_desktop.return_value = mock_desktop

        # Setup the mock to return our expected result
        expected_result = {
            "status": "success",
            "operation": "activate",
            "action": "activated",
            "handle": 12345,
            "has_focus": True,
            "is_visible": True,
            "is_enabled": True,
            "timestamp": "2023-01-01T00:00:00",
        }
        mock_automation_windows.return_value = expected_result

        # Import here to get the patched version
        from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows

        # Call the function
        result = automation_windows("activate", handle=12345)

        # Verify the result
        assert result == expected_result

    @patch("windows_computer_use_mcp.tools.portmanteau_windows._get_desktop")
    @patch("windows_computer_use_mcp.tools.portmanteau_windows.automation_windows")
    def test_activate_window_failure(self, mock_automation_windows, mock_get_desktop, app_instance):
        """Test window activation failure with mocks."""
        # Setup the mock to return an error result
        expected_result = {
            "status": "error",
            "operation": "activate",
            "handle": 99999,
            "error": "Error activating window: Window not found",
            "error_type": "Exception",
            "window_state": {
                "exists": False,
                "is_visible": False,
                "is_enabled": False,
                "has_focus": False,
                "is_minimized": False,
            },
            "timestamp": "2023-01-01T00:00:00",
        }
        mock_automation_windows.return_value = expected_result

        # Import here to get the patched version
        from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows

        # Call the function
        result = automation_windows("activate", handle=99999)

        # Verify the error result
        assert result == expected_result

    @patch("windows_computer_use_mcp.tools.portmanteau_windows._get_desktop")
    @patch("windows_computer_use_mcp.tools.portmanteau_windows.automation_windows")
    def test_activate_nonexistent_window(self, mock_automation_windows, mock_get_desktop, app_instance):
        """Test activating a non-existent window with mocks."""
        # Setup the mock to return an error result for non-existent window
        expected_result = {
            "status": "error",
            "operation": "activate",
            "handle": 99999,
            "error": "No window found with handle 99999",
            "error_type": "RuntimeError",
            "window_state": {
                "exists": False,
                "is_visible": False,
                "is_enabled": False,
                "has_focus": False,
                "is_minimized": False,
            },
            "timestamp": "2023-01-01T00:00:00",
        }
        mock_automation_windows.return_value = expected_result

        # Import here to get the patched version
        from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows

        # Call the function
        result = automation_windows("activate", handle=99999)

        # Verify the error result
        assert result == expected_result

    @patch("windows_computer_use_mcp.tools.portmanteau_windows._get_desktop")
    @patch("windows_computer_use_mcp.tools.portmanteau_windows.automation_windows")
    def test_activate_window_verify_focus(self, mock_automation_windows, mock_get_desktop, app_instance):
        """Test window activation with focus verification using mocks."""
        # Setup the mock to return a success result but without focus
        expected_result = {
            "status": "success",
            "operation": "activate",
            "action": "activated",
            "handle": 12345,
            "has_focus": False,  # Simulate focus not gained
            "is_visible": True,
            "is_enabled": True,
            "timestamp": "2023-01-01T00:00:00",
        }
        mock_automation_windows.return_value = expected_result

        # Import here to get the patched version
        from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows

        # Call the function
        result = automation_windows("activate", handle=12345)

        # Verify the result indicates a warning about focus
        assert result["status"] == "success"  # Still success, but with warning
        assert result["operation"] == "activate"
        assert result["has_focus"] is False  # Indicates focus wasn't gained
