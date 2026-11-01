"""Tests for the per-app safety allowlist (pure logic + fail-soft paths)."""

import pytest

from windows_computer_use_mcp.safety import (
    ENV_ALLOWED_APPS,
    check_app_allowed,
    normalize_app_name,
    parse_allowed_apps,
    resolve_process_name,
)


@pytest.fixture
def no_allowlist(monkeypatch):
    monkeypatch.delenv(ENV_ALLOWED_APPS, raising=False)


@pytest.fixture
def allowlist_notepad_calc(monkeypatch):
    monkeypatch.setenv(ENV_ALLOWED_APPS, "notepad.exe, calc.exe")


class TestParseAllowedApps:
    def test_unset_means_unrestricted(self, no_allowlist):
        assert parse_allowed_apps() is None

    def test_blank_means_unrestricted(self, monkeypatch):
        monkeypatch.setenv(ENV_ALLOWED_APPS, "   ")
        assert parse_allowed_apps() is None

    def test_parses_comma_list(self, allowlist_notepad_calc):
        assert parse_allowed_apps() == ["notepad.exe", "calc.exe"]

    def test_parses_semicolons_and_case(self, monkeypatch):
        monkeypatch.setenv(ENV_ALLOWED_APPS, "Notepad.EXE;Calc")
        assert parse_allowed_apps() == ["notepad.exe", "calc"]


class TestCheckAppAllowed:
    def test_unrestricted_without_env(self, no_allowlist):
        assert check_app_allowed("anything.exe") == {"allow": True, "code": "unrestricted"}

    def test_listed_app_allowed_with_or_without_extension(self, allowlist_notepad_calc):
        assert check_app_allowed("notepad.exe")["allow"] is True
        assert check_app_allowed("NOTEPAD")["allow"] is True
        assert check_app_allowed("calc.exe")["code"] == "ok"

    def test_unlisted_app_blocked(self, allowlist_notepad_calc):
        verdict = check_app_allowed("mspaint.exe")
        assert verdict["allow"] is False
        assert verdict["code"] == "app_blocked"
        assert "mspaint.exe" in verdict["message"]

    def test_unknown_target_fails_open(self, allowlist_notepad_calc):
        for unknown in (None, ""):
            verdict = check_app_allowed(unknown)
            assert verdict["allow"] is True
            assert verdict["code"] == "app_unknown"

    def test_normalize_basename(self):
        assert normalize_app_name("C:\\Windows\\System32\\Notepad.EXE") == "notepad.exe"


class TestResolveProcessName:
    def test_none_handle_resolves_none(self):
        assert resolve_process_name(None) is None

    def test_bogus_handle_resolves_none(self):
        # Fail-soft: never raises, returns None for dead handles.
        assert resolve_process_name(0) is None
