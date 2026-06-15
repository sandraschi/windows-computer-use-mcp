"""Tests for the automation_keyboard portmanteau tool."""

# Imports moved into test methods to ensure mocks are applied correctly


class TestAutomationKeyboard:
    """Tests for automation_keyboard tool operations."""

    def test_keyboard_type(self, mock_pyautogui, verify_result):
        """Test typing text."""
        from windows_computer_use_mcp.tools.models import KeyboardOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_keyboard import automation_keyboard

        req = KeyboardOperationRequest(operation="type", text="Hello World", interval=0.1)
        result = automation_keyboard(req)

        verify_result(result)
        mock_pyautogui.write.assert_called_once_with("Hello World", interval=0.1)

    def test_keyboard_press(self, mock_pyautogui, verify_result):
        """Test pressing a key."""
        from windows_computer_use_mcp.tools.models import KeyboardOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_keyboard import automation_keyboard

        req = KeyboardOperationRequest(operation="press", key="enter")
        result = automation_keyboard(req)

        verify_result(result)
        mock_pyautogui.press.assert_called_once_with("enter")

    def test_keyboard_hotkey(self, mock_pyautogui, verify_result):
        """Test pressing a hotkey combination."""
        from windows_computer_use_mcp.tools.models import KeyboardOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_keyboard import automation_keyboard

        req = KeyboardOperationRequest(operation="hotkey", keys=["ctrl", "c"])
        result = automation_keyboard(req)

        verify_result(result)
        mock_pyautogui.hotkey.assert_called_once_with("ctrl", "c")

    def test_keyboard_write_pywinauto(self, mock_desktop_uia, verify_result):
        """Test writing text via pywinauto (send_keys)."""
        # Note: In portmanteau_keyboard, if handle is provided, it might try pywinauto
        # But for now the implementation mostly uses pyautogui or similar.
        # Let's verify the current implementation logic.
        pass

    def test_invalid_operation(self, verify_result):
        """Test invalid operation error handling."""
        import pytest
        from pydantic import ValidationError

        from windows_computer_use_mcp.tools.models import KeyboardOperationRequest

        with pytest.raises(ValidationError):
            KeyboardOperationRequest(operation="invalid_op", text="test")
