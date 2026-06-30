"""Tests for the automation_mouse portmanteau tool."""

# Imports moved for mocking integrity


import pytest


class TestAutomationMouse:
    """Tests for automation_mouse tool operations.

    NOTE: Most mouse tests require mocking win32_mouse functions (click, move_to,
    get_cursor_pos, scroll, drag). These were previously mocked via pyautogui
    but the current implementation uses native win32_mouse. Rewrite when adding
    new mouse tests.
    """

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_position(self, verify_result):
        ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_move_absolute(self, verify_result):
        ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_move_relative(self, verify_result):
        ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_click(self, verify_result):
        ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_double_click(self, verify_result):
        ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_right_click(self, verify_result):
        ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_scroll(self, verify_result):
        ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_drag(self, verify_result):
        ...

    def test_invalid_operation(self, verify_result):
        """Test invalid operation error handling."""
        from pydantic import ValidationError

        from windows_computer_use_mcp.tools.models import MouseOperationRequest

        with pytest.raises(ValidationError):
            MouseOperationRequest(operation="invalid_op")
