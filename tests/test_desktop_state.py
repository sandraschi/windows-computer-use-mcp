"""Tests for desktop state capture tools."""

from unittest.mock import MagicMock, patch

from windows_computer_use_mcp.tools.desktop_state import get_desktop_state
from windows_computer_use_mcp.tools.models import DesktopStateRequest


class TestGetDesktopState:
    """Tests for get_desktop_state tool."""

    @patch("windows_computer_use_mcp.tools.desktop_state.DesktopStateCapture")
    def test_get_desktop_state_basic(self, mock_capture_class, verify_result):
        """Test basic desktop state capture."""
        mock_capturer = MagicMock()
        mock_capturer.capture.return_value = {
            "text": "Desktop state report",
            "interactive_elements": [{"name": "Button1", "type": "Button"}],
            "informative_elements": [{"name": "Label1", "type": "Text"}],
            "element_count": 2,
        }
        mock_capture_class.return_value = mock_capturer

        req = DesktopStateRequest()
        result = get_desktop_state(req)

        verify_result(result, expected_keys=["element_count", "interactive_elements", "informative_elements"])
        assert result.data["element_count"] == 2
        assert len(result.data["interactive_elements"]) == 1

    @patch("windows_computer_use_mcp.tools.desktop_state.DesktopStateCapture")
    def test_get_desktop_state_with_vision(self, mock_capture_class, verify_result):
        """Test desktop state capture with vision enabled."""
        mock_capturer = MagicMock()
        mock_capturer.capture.return_value = {
            "text": "Desktop state report",
            "interactive_elements": [],
            "informative_elements": [],
            "element_count": 0,
            "screenshot_base64": "base64encodedimage",
        }
        mock_capture_class.return_value = mock_capturer

        req = DesktopStateRequest(use_vision=True)
        result = get_desktop_state(req)

        verify_result(result)
        mock_capturer.capture.assert_called_once_with(use_vision=True, use_ocr=False, capture_mode=None)

    @patch("windows_computer_use_mcp.tools.desktop_state.DesktopStateCapture")
    def test_get_desktop_state_with_ocr(self, mock_capture_class, verify_result):
        """Test desktop state capture with OCR enabled."""
        mock_capturer = MagicMock()
        mock_capturer.capture.return_value = {
            "text": "Desktop state report",
            "interactive_elements": [],
            "informative_elements": [],
            "element_count": 0,
        }
        mock_capture_class.return_value = mock_capturer

        req = DesktopStateRequest(use_ocr=True)
        result = get_desktop_state(req)

        verify_result(result)
        mock_capturer.capture.assert_called_once_with(use_vision=False, use_ocr=True, capture_mode=None)

    @patch("windows_computer_use_mcp.tools.desktop_state.DesktopStateCapture")
    def test_get_desktop_state_with_custom_depth(self, mock_capture_class, verify_result):
        """Test desktop state capture with custom max_depth."""
        mock_capturer = MagicMock()
        mock_capturer.capture.return_value = {
            "text": "Desktop state report",
            "interactive_elements": [],
            "informative_elements": [],
            "element_count": 0,
        }
        mock_capture_class.return_value = mock_capturer

        req = DesktopStateRequest(max_depth=15)
        result = get_desktop_state(req)

        verify_result(result)
        mock_capture_class.assert_called_once_with(max_depth=15, element_timeout=0.5)

    @patch("windows_computer_use_mcp.tools.desktop_state.DesktopStateCapture")
    def test_get_desktop_state_error_handling(self, mock_capture_class, verify_result):
        """Test desktop state capture error handling."""
        mock_capturer = MagicMock()
        mock_capturer.capture.side_effect = Exception("Capture failed")
        mock_capture_class.return_value = mock_capturer

        req = DesktopStateRequest()
        result = get_desktop_state(req)

        # In current industrialized version, it returns a ToolResult with status="error"
        verify_result(result, expected_status="error")
        # Ensure data is either None or handled safely on error
        assert result.data is None or "handle" not in result.data
