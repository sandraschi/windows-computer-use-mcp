"""REST safety snapshot — no hardware."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from windows_computer_use_mcp.server import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_safety_status_returns_snapshot(client: TestClient) -> None:
    r = client.get("/api/v1/safety/status")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "success"
    assert "snapshot" in data
    assert "face_tool_opt_in" in data
    assert "env" in data
    assert "hitl" in data
