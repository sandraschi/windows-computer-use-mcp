"""Camera REST API — mocked in CI; optional real OpenCV probe locally."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from windows_computer_use_mcp.api.v1.endpoints.cameras import CameraDevice
from windows_computer_use_mcp.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_cameras_get_returns_json(client: TestClient) -> None:
    """Always runs — mocks enumeration so CI never opens devices."""
    fake = [
        CameraDevice(index=0, label="Camera 0 (640x480)", width=640, height=480),
        CameraDevice(index=1, label="Camera 1 (320x240)", width=320, height=240),
    ]
    with patch("windows_computer_use_mcp.api.v1.endpoints.cameras.enumerate_cameras", return_value=fake):
        r = client.get("/api/v1/cameras/")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["index"] == 0
    assert "640" in data[0]["label"]


@pytest.mark.requires_hardware
def test_enumerate_cameras_runs_on_local_host() -> None:
    """Outside CI: actually probes OpenCV indices (can be slow; may return [])."""
    from windows_computer_use_mcp.api.v1.endpoints.cameras import enumerate_cameras

    devices = enumerate_cameras()
    assert isinstance(devices, list)
    for d in devices:
        assert d.index >= 0
        assert d.label
