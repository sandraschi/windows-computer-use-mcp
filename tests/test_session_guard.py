"""Tests for session_guard: desktop detection, UAC, preflight (all mocked)."""

import pytest

from windows_computer_use_mcp import session_guard


class TestInteractiveDesktop:
    def test_default_is_interactive(self):
        assert session_guard.is_interactive_desktop("Default") is True

    def test_winlogon_is_not_interactive(self):
        assert session_guard.is_interactive_desktop("Winlogon") is False

    def test_unknown_desktop_is_none(self, monkeypatch):
        monkeypatch.setattr(session_guard, "_input_desktop_name", lambda: None)
        assert session_guard.is_interactive_desktop() is None


class TestDetectUac:
    def test_interactive_no_uac(self, monkeypatch):
        monkeypatch.setattr(session_guard, "_input_desktop_name", lambda: "Default")
        monkeypatch.setattr(session_guard, "_consent_running", lambda: False)
        result = session_guard.detect_uac()
        assert result["interactive"] is True
        assert result["secure_desktop"] is False
        assert result["uac_prompt"] is False

    def test_secure_desktop_with_consent_is_uac(self, monkeypatch):
        monkeypatch.setattr(session_guard, "_input_desktop_name", lambda: "Winlogon")
        monkeypatch.setattr(session_guard, "_consent_running", lambda: True)
        result = session_guard.detect_uac()
        assert result["interactive"] is False
        assert result["secure_desktop"] is True
        assert result["uac_prompt"] is True

    def test_secure_desktop_without_consent_is_lock(self, monkeypatch):
        monkeypatch.setattr(session_guard, "_input_desktop_name", lambda: "Winlogon")
        monkeypatch.setattr(session_guard, "_consent_running", lambda: False)
        result = session_guard.detect_uac()
        assert result["interactive"] is False
        assert result["uac_prompt"] is False

    def test_unknown_desktop_is_unknown(self, monkeypatch):
        monkeypatch.setattr(session_guard, "_input_desktop_name", lambda: None)
        monkeypatch.setattr(session_guard, "_consent_running", lambda: False)
        result = session_guard.detect_uac()
        assert result["interactive"] is None
        assert result["uac_prompt"] is False
        assert result["unknown"] is True


class TestSessionPreflight:
    def test_preflight_passes_on_healthy_session(self, monkeypatch):
        monkeypatch.setattr(
            session_guard,
            "detect_uac",
            lambda: {
                "interactive": True,
                "secure_desktop": False,
                "uac_prompt": False,
                "desktop_name": "Default",
                "consent_running": False,
            },
        )
        result = session_guard.session_preflight(min_disk_mb=1.0, min_memory_mb=1.0)
        assert result["ok"] is True
        names = {c["name"] for c in result["checks"]}
        assert {"interactive_session", "uac_prompt", "disk_free", "memory_available"} <= names

    def test_preflight_blocks_on_uac(self, monkeypatch):
        monkeypatch.setattr(
            session_guard,
            "detect_uac",
            lambda: {
                "interactive": False,
                "secure_desktop": True,
                "uac_prompt": True,
                "desktop_name": "Winlogon",
                "consent_running": True,
            },
        )
        result = session_guard.session_preflight()
        assert result["ok"] is False
        uac_check = next(c for c in result["checks"] if c["name"] == "uac_prompt")
        assert uac_check["passed"] is False

    def test_preflight_blocks_on_locked_session(self, monkeypatch):
        monkeypatch.setattr(
            session_guard,
            "detect_uac",
            lambda: {
                "interactive": False,
                "secure_desktop": True,
                "uac_prompt": False,
                "desktop_name": "Winlogon",
                "consent_running": False,
            },
        )
        result = session_guard.session_preflight()
        assert result["ok"] is False

    def test_system_ops_accept_preflight_and_detect_uac(self):
        from pydantic import ValidationError

        from windows_computer_use_mcp.tools.models import SystemOperationRequest

        assert SystemOperationRequest(operation="preflight").operation == "preflight"
        assert SystemOperationRequest(operation="detect_uac").operation == "detect_uac"
        with pytest.raises(ValidationError):
            SystemOperationRequest(operation="nope_not_an_op")

    def test_foreground_window_shape(self):
        result = session_guard.foreground_window()
        assert set(result) >= {"hwnd", "title"}
