"""Tests for background (PostMessage) input ops and gate allowlist wiring."""

from unittest.mock import MagicMock

import pytest

from windows_computer_use_mcp import win32_keyboard, win32_window
from windows_computer_use_mcp.safety import ENV_ALLOWED_APPS, ENV_DRY_RUN, ENV_KILL_SWITCH, before_mutation


@pytest.fixture
def clean_gate_env(monkeypatch):
    monkeypatch.delenv(ENV_KILL_SWITCH, raising=False)
    monkeypatch.delenv(ENV_DRY_RUN, raising=False)
    monkeypatch.delenv(ENV_ALLOWED_APPS, raising=False)


class TestModels:
    def test_mouse_background_click_model(self):
        from windows_computer_use_mcp.tools.models import MouseOperationRequest

        req = MouseOperationRequest(operation="background_click", window_handle=123, x=10, y=20)
        assert req.window_handle == 123

    def test_keyboard_background_ops_model(self):
        from windows_computer_use_mcp.tools.models import KeyboardOperationRequest

        assert KeyboardOperationRequest(operation="background_type", window_handle=1, text="hi").text == "hi"
        assert KeyboardOperationRequest(operation="background_key", window_handle=1, key="enter").key == "enter"

    def test_invalid_ops_rejected(self):
        from pydantic import ValidationError

        from windows_computer_use_mcp.tools.models import KeyboardOperationRequest, MouseOperationRequest

        with pytest.raises(ValidationError):
            MouseOperationRequest(operation="teleport")
        with pytest.raises(ValidationError):
            KeyboardOperationRequest(operation="teleport")


class TestPostmessageKeyboard:
    def test_type_sends_wm_char_per_char(self, monkeypatch):
        mock_gui = MagicMock()
        monkeypatch.setattr(win32_keyboard, "win32gui", mock_gui)
        meta = win32_keyboard.postmessage_type(123, "Hi!")
        assert meta["characters_sent"] == 3
        assert meta["dispatch"] == "background"
        assert mock_gui.PostMessage.call_count == 3
        for call, ch in zip(mock_gui.PostMessage.call_args_list, "Hi!", strict=True):
            args = call.args if hasattr(call, "args") else call[0]
            assert args[1] == 0x0102  # WM_CHAR
            assert args[2] == ord(ch)

    def test_type_empty_text_sends_nothing(self, monkeypatch):
        mock_gui = MagicMock()
        monkeypatch.setattr(win32_keyboard, "win32gui", mock_gui)
        meta = win32_keyboard.postmessage_type(123, "")
        assert meta["characters_sent"] == 0
        mock_gui.PostMessage.assert_not_called()

    def test_key_sends_keydown_keyup(self, monkeypatch):
        mock_gui = MagicMock()
        monkeypatch.setattr(win32_keyboard, "win32gui", mock_gui)
        meta = win32_keyboard.postmessage_key(123, "enter")
        assert meta["dispatch"] == "background"
        assert mock_gui.PostMessage.call_count == 2
        calls = mock_gui.PostMessage.call_args_list
        first = calls[0].args if hasattr(calls[0], "args") else calls[0][0]
        second = calls[1].args if hasattr(calls[1], "args") else calls[1][0]
        assert first[1] == 0x0100  # WM_KEYDOWN
        assert second[1] == 0x0101  # WM_KEYUP
        assert first[2] == 0x0D

    def test_key_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown background key"):
            win32_keyboard.postmessage_key(123, "hyper")


class TestPostmessageClick:
    def test_single_click_posts_down_up(self, monkeypatch):
        mock_gui = MagicMock()
        mock_gui.ScreenToClient.side_effect = lambda _hwnd, pt: pt
        monkeypatch.setattr(win32_window, "win32gui", mock_gui)
        meta = win32_window.postmessage_click_at(99, 500, 300)
        assert meta["dispatch"] == "background"
        assert mock_gui.PostMessage.call_count == 2

    def test_double_click_posts_twice(self, monkeypatch):
        mock_gui = MagicMock()
        mock_gui.ScreenToClient.side_effect = lambda _hwnd, pt: pt
        monkeypatch.setattr(win32_window, "win32gui", mock_gui)
        win32_window.postmessage_click_at(99, 500, 300, double=True)
        assert mock_gui.PostMessage.call_count == 4


class TestGateAllowlistWiring:
    def test_unrestricted_without_env(self, clean_gate_env):
        assert before_mutation(read_only=False)["allow"] is True

    def test_blocked_target(self, clean_gate_env, monkeypatch):
        monkeypatch.setenv(ENV_ALLOWED_APPS, "notepad.exe")
        verdict = before_mutation(read_only=False, target_process="mspaint.exe")
        assert verdict["allow"] is False
        assert verdict["code"] == "app_blocked"

    def test_allowed_target_passes(self, clean_gate_env, monkeypatch):
        monkeypatch.setenv(ENV_ALLOWED_APPS, "notepad.exe")
        verdict = before_mutation(read_only=False, target_process="notepad.exe")
        assert verdict["allow"] is True

    def test_read_only_skips_allowlist(self, clean_gate_env, monkeypatch):
        monkeypatch.setenv(ENV_ALLOWED_APPS, "notepad.exe")
        assert before_mutation(read_only=True, target_process="evil.exe")["allow"] is True
