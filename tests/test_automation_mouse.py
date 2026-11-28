"""Tests for the automation_mouse portmanteau tool."""

# Imports moved for mocking integrity

import sys

import pytest


class TestAutomationMouse:
    """Tests for automation_mouse tool operations.

    NOTE: Most mouse tests require mocking win32_mouse functions (click, move_to,
    get_cursor_pos, scroll, drag). These were previously mocked via pyautogui
    but the current implementation uses native win32_mouse. Rewrite when adding
    new mouse tests.
    """

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_position(self, verify_result): ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_move_absolute(self, verify_result): ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_move_relative(self, verify_result): ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_click(self, verify_result): ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_double_click(self, verify_result): ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_right_click(self, verify_result): ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_scroll(self, verify_result): ...

    @pytest.mark.skip(reason="needs win32_mouse mocking (previously used pyautogui)")
    def test_mouse_drag(self, verify_result): ...

    def test_invalid_operation(self, verify_result):
        """Test invalid operation error handling."""
        from pydantic import ValidationError

        from windows_computer_use_mcp.tools.models import MouseOperationRequest

        with pytest.raises(ValidationError):
            MouseOperationRequest(operation="invalid_op")


class TestDoubleClickTime:
    """Double-click threshold resolution used by ``win32_mouse.double_click``.

    Regression test: ``win32api`` never exported ``GetDoubleClickTime`` (checked
    against pywin32 311 and 312), so ``double_click`` raised ``AttributeError``
    on every Windows host instead of clicking twice.
    """

    @pytest.mark.skipif(sys.platform != "win32", reason="needs win32 user32 call")
    def test_threshold_is_positive(self):
        from windows_computer_use_mcp import win32_mouse

        assert win32_mouse._double_click_time_ms() > 0

    @pytest.mark.skipif(sys.platform != "win32", reason="needs win32 user32 call")
    def test_double_click_survives_missing_win32api_attribute(self, monkeypatch):
        """double_click must not depend on win32api.GetDoubleClickTime."""
        from windows_computer_use_mcp import win32_mouse

        seen: list[str] = []

        def _noop(*_a, **_k):
            seen.append("click")

        monkeypatch.setattr(win32_mouse, "move_to", lambda *_a, **_k: None)
        monkeypatch.setattr(win32_mouse, "_down_up", _noop)
        monkeypatch.setattr(win32_mouse, "failsafe_enabled", lambda: False)

        win32_mouse.double_click(1, 1)

        # Two clicks, each a down + up event; no AttributeError.
        assert seen.count("click") == 4
