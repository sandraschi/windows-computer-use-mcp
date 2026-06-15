"""Tests for automation_task and task_engine."""

from pathlib import Path
from unittest.mock import patch

from windows_computer_use_mcp import task_engine
from windows_computer_use_mcp.app_profiles import get_profile, list_profiles
from windows_computer_use_mcp.tools.models import TaskOperationRequest, ToolResult
from windows_computer_use_mcp.tools.portmanteau_task import automation_task


def test_assert_outcome_file_exists(tmp_path: Path):
    f = tmp_path / "out.vrm"
    f.write_bytes(b"x" * 2000)
    r = task_engine.assert_outcome("file_exists", path=str(f))
    assert r["passed"] is True
    r2 = task_engine.assert_outcome("file_min_kb", path=str(f), min_kb=1)
    assert r2["passed"] is True


def test_vroid_profile():
    p = get_profile("vroidstudio")
    assert p is not None
    assert p.dispatch == "foreground"
    assert p.stable_region is not None


def test_list_profiles():
    assert any(p["app_id"] == "vroidstudio" for p in list_profiles())


@patch("windows_computer_use_mcp.task_engine._execute_step")
def test_run_task_success(mock_exec, tmp_path: Path):
    f = tmp_path / "model.vrm"
    f.write_bytes(b"data")

    def _fake(session, step, hwnd):
        if step.get("kind") == "assert_file":
            outcome = task_engine.assert_outcome("file_exists", path=step["path"])
            if not outcome.get("passed"):
                raise RuntimeError("assert_file failed")
            return {"kind": "assert_file", "outcome": outcome}
        return {"kind": "shortcut", "action": "new"}

    mock_exec.side_effect = _fake
    out = tmp_path / "evidence"
    out.mkdir()
    steps = [
        {"kind": "shortcut", "action": "new", "app": "vroidstudio"},
        {"kind": "assert_file", "path": str(f), "check": "file_exists", "on_fail": "abort"},
    ]
    session = task_engine.run_task(app="vroidstudio", steps=steps, output_dir=str(out))
    assert session.status == "complete"
    assert len(session.evidence) == 2


@patch("windows_computer_use_mcp.task_engine._execute_step")
def test_run_task_fails_with_evidence(mock_exec, tmp_path: Path):
    mock_exec.side_effect = RuntimeError("shortcut missed")
    session = task_engine.run_task(
        app="vroidstudio",
        steps=[{"kind": "shortcut", "action": "export_vrm", "on_fail": "abort"}],
        output_dir=str(tmp_path),
    )
    assert session.status == "failed"
    assert session.evidence[0]["status"] == "failed"


@patch("windows_computer_use_mcp.task_engine._invalidate_snapshots_after_mutation")
@patch("windows_computer_use_mcp.task_engine._execute_step")
def test_run_task_invalidates_snapshots_on_mutation(mock_exec, mock_inv, tmp_path: Path):
    mock_exec.return_value = {"kind": "shortcut", "action": "new"}
    mock_inv.return_value = {"invalidated": 2, "ui_hash": "abc"}

    session = task_engine.run_task(
        app="vroidstudio",
        steps=[{"kind": "shortcut", "action": "new", "app": "vroidstudio"}],
        window_handle=12345,
        output_dir=str(tmp_path),
    )
    assert session.status == "complete"
    mock_inv.assert_called_once_with(12345)
    assert session.evidence[0].get("snapshot_invalidation") == {"invalidated": 2, "ui_hash": "abc"}


@patch("windows_computer_use_mcp.task_engine._execute_step")
def test_run_task_optional_step_skipped(mock_exec, tmp_path: Path):
    mock_exec.side_effect = RuntimeError("optional miss")
    session = task_engine.run_task(
        app="vroidstudio",
        steps=[{"kind": "shortcut", "action": "rare", "optional": True, "on_fail": "abort"}],
        output_dir=str(tmp_path),
    )
    assert session.status == "complete"
    assert session.evidence[0]["status"] == "skipped_optional"


def test_automation_task_list_profiles():
    req = TaskOperationRequest(operation="list_profiles")
    result = automation_task(req)
    assert isinstance(result, ToolResult)
    assert result.status == "success"
    profiles = result.data["profiles"]
    vroid = next(p for p in profiles if p["app_id"] == "vroidstudio")
    assert "stable_region" in vroid


def test_automation_task_list_templates():
    from windows_computer_use_mcp.template_library import ensure_placeholder_templates

    ensure_placeholder_templates("vroidstudio")
    req = TaskOperationRequest(operation="list_templates", app="vroidstudio")
    result = automation_task(req)
    assert result.status == "success"
    assert len(result.data["templates"]) >= 4
