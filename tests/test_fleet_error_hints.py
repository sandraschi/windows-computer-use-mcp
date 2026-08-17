"""Tests for fleet error hints (W5 of FLEET_ERROR_TELEMETRY.md).

No network: depot queries are monkeypatched or pointed at dead ports.
"""

from __future__ import annotations

import httpx
import pytest

from windows_computer_use_mcp import fleet_error_hints as feh
from windows_computer_use_mcp.fleet_error_telemetry import query_fleet_errors


class TestFleetErrorTypeFor:
    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("element not found in tree", "element_not_found"),
            ("ElementNotFoundError: no match", "element_not_found"),
            ("request timed out after 30s", "timeout"),
            ("Access denied by policy", "access_denied"),
            ("connection refused to 127.0.0.1", "connection_error"),
            ("unexpected keyword argument", "validation"),
            ("something totally unknown happened", "mission_step_error"),
        ],
    )
    def test_mapping(self, message, expected):
        assert feh.fleet_error_type_for(message) == expected


class TestRecordFleetFailure:
    def test_records_to_local_ring(self, tmp_path, monkeypatch):
        monkeypatch.setattr(feh, "_DB_PATH", tmp_path / "fleet_errors.sqlite3")
        feh.record_fleet_failure(
            tool="automation_elements",
            operation="click",
            error_type="element_not_found",
            message="no match",
            params={"title": "Save"},
        )
        rows = query_fleet_errors(
            tool="automation_elements",
            error_type="element_not_found",
            last_n=5,
            db_path=str(tmp_path / "fleet_errors.sqlite3"),
        )
        assert len(rows) == 1
        assert rows[0]["server"] == "windows-computer-use-mcp"

    def test_fail_soft_on_bad_path(self, monkeypatch):
        monkeypatch.setattr(feh, "_DB_PATH", None)
        feh.record_fleet_failure(tool="x", operation=None, error_type="y", message="z")


class TestFetchDepotHints:
    def test_offline_depot_returns_empty(self, monkeypatch):
        monkeypatch.setattr(feh, "_DEPOT_URL", "http://127.0.0.1:59999")
        assert feh.fetch_depot_hints(tool="t", error_type="e") == []

    def test_extracts_recovery_strings(self, monkeypatch):
        captured = {}

        class FakeResponse:
            status_code = 200

            def json(self):
                return {
                    "results": [
                        {"recovery": ["use title= not text=", "maximize window first"]},
                        {"recovery": ["use title= not text="]},
                        {"recovery": None},
                    ]
                }

        def fake_get(url, params, timeout):
            captured["url"] = url
            captured["params"] = params
            return FakeResponse()

        monkeypatch.setattr(httpx, "get", fake_get)
        hints = feh.fetch_depot_hints(tool="automation_elements", error_type="element_not_found")
        assert hints == ["use title= not text=", "maximize window first"]
        assert captured["params"] == {"tool": "automation_elements", "error_type": "element_not_found", "limit": 3}

    def test_http_error_returns_empty(self, monkeypatch):
        class FakeResponse:
            status_code = 500

            def json(self):
                return {}

        monkeypatch.setattr(httpx, "get", lambda url, params, timeout: FakeResponse())
        assert feh.fetch_depot_hints(tool="t", error_type="e") == []


class TestFetchOrLocalHints:
    def test_depot_wins_over_local(self, monkeypatch, tmp_path):
        monkeypatch.setattr(feh, "fetch_depot_hints", lambda **kw: ["from depot"])
        assert feh.fetch_or_local_hints(tool="t", error_type="e") == ["from depot"]

    def test_local_fallback(self, monkeypatch, tmp_path):
        monkeypatch.setattr(feh, "fetch_depot_hints", lambda **kw: [])
        monkeypatch.setattr(feh, "_DB_PATH", tmp_path / "fleet_errors.sqlite3")
        from windows_computer_use_mcp.fleet_error_telemetry import record_fleet_error

        record_fleet_error(
            server="windows-computer-use-mcp",
            tool="automation_mouse",
            error_type="timeout",
            message="stuck",
            recovery=["scroll before click"],
            db_path=str(tmp_path / "fleet_errors.sqlite3"),
        )
        hints = feh.fetch_or_local_hints(tool="automation_mouse", error_type="timeout")
        assert "scroll before click" in hints


def test_depot_url_env_override(monkeypatch):
    monkeypatch.setenv("windows_computer_use_mcp_DEPOT_URL", "http://10.0.0.1:8080")
    import importlib

    importlib.reload(feh)
    assert feh._DEPOT_URL == "http://10.0.0.1:8080"
    monkeypatch.delenv("windows_computer_use_mcp_DEPOT_URL")
    importlib.reload(feh)
