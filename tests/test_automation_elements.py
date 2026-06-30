"""Tests for the automation_elements portmanteau tool."""

from unittest.mock import MagicMock

from windows_computer_use_mcp.tools.models import ElementOperationRequest
from windows_computer_use_mcp.tools.portmanteau_elements import automation_elements


class TestAutomationElements:
    """Tests for automation_elements tool operations."""

    def test_element_info(self, mock_desktop_uia, verify_result):
        """Test getting detailed information about a UI element."""
        mock_element = MagicMock()
        mock_element.class_name.return_value = "Button"
        mock_element.window_text.return_value = "OK"
        mock_element.process_id.return_value = 1234
        mock_element.handle = 12345
        mock_element.is_visible.return_value = True
        mock_element.is_enabled.return_value = True

        mock_rect = MagicMock()
        mock_rect.left = 100
        mock_rect.top = 200
        mock_rect.right = 150
        mock_rect.bottom = 230
        mock_rect.width.return_value = 50
        mock_rect.height.return_value = 30
        mock_element.rectangle.return_value = mock_rect

        # Mocking the Desktop -> Window -> Child Element chain
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.child_window.return_value = mock_element
        mock_desktop_uia.window.return_value = mock_window

        req = ElementOperationRequest(operation="info", window_handle=123, control_id="btnOK")
        result = automation_elements(req)

        verify_result(result, expected_keys=["class_name", "text", "rect"])
        assert result.data["class_name"] == "Button"
        assert result.data["text"] == "OK"

    def test_element_click(self, mock_desktop_uia, verify_result):
        """Test clicking a UI element by control_id."""
        mock_element = MagicMock()
        mock_element.exists.return_value = True

        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.child_window.return_value = mock_element
        mock_desktop_uia.window.return_value = mock_window

        req = ElementOperationRequest(operation="click", window_handle=123, control_id="btnOK")
        result = automation_elements(req)

        verify_result(result)
        mock_element.click.assert_called_once()

    def test_element_set_text(self, mock_desktop_uia, verify_result):
        """Test setting text on a UI element."""
        mock_element = MagicMock()
        mock_element.exists.return_value = True

        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.child_window.return_value = mock_element
        mock_desktop_uia.window.return_value = mock_window

        req = ElementOperationRequest(operation="set_text", window_handle=123, control_id="Edit1", text="Hello World")
        result = automation_elements(req)

        verify_result(result)
        mock_element.set_text.assert_called_once_with("Hello World")

    def test_element_list(self, mock_desktop_uia, verify_result):
        """Test listing child elements of a window."""
        mock_child = MagicMock()
        mock_child.class_name.return_value = "Button"
        mock_child.window_text.return_value = "Child"
        mock_child.process_id.return_value = 1234
        mock_child.handle = 54321
        mock_child.is_visible.return_value = True
        mock_child.is_enabled.return_value = True
        mock_child.children.return_value = []  # Terminate recursion

        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.children.return_value = [mock_child]
        mock_desktop_uia.window.return_value = mock_window

        req = ElementOperationRequest(operation="list", window_handle=123, max_depth=1)
        result = automation_elements(req)

        verify_result(result, expected_keys=["elements"])
        assert len(result.data["elements"]) == 1
        assert result.data["elements"][0]["text"] == "Child"

    def test_element_exists_positive(self, mock_desktop_uia, verify_result):
        """Test exists operation when element is found."""
        mock_element = MagicMock()
        mock_element.exists.return_value = True

        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.child_window.return_value = mock_element
        mock_desktop_uia.window.return_value = mock_window

        req = ElementOperationRequest(operation="exists", window_handle=123, control_id="btnOK", timeout=0.1)
        result = automation_elements(req)

        verify_result(result, expected_keys=["exists"])
        assert result.data["exists"] is True

    def test_element_wait_failure(self, mock_desktop_uia, verify_result):
        """Test wait operation timeout."""
        mock_element = MagicMock()
        mock_element.exists.return_value = False

        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_window.child_window.return_value = mock_element
        mock_desktop_uia.window.return_value = mock_window

        # Use a very short timeout for tests
        req = ElementOperationRequest(operation="wait", window_handle=123, control_id="NonExistent", timeout=0.1)
        result = automation_elements(req)

        verify_result(result, expected_status="error")
        assert "not found" in result.message.lower()

    def test_coordinate_click_absolute(self, mock_desktop_uia, verify_result):
        """Test clicking at absolute coordinates via automation_elements."""
        # Note: automation_elements uses win32_mouse.click, not pyautogui.click
        req = ElementOperationRequest(operation="click", window_handle=123, x=500, y=500, absolute=True)
        result = automation_elements(req)

        verify_result(result)
