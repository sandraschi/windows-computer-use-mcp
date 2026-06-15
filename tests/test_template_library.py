"""Tests for per-app template library (T2.3)."""

from pathlib import Path

from windows_computer_use_mcp import template_library


def test_manifest_lists_vroid_templates():
    entries = template_library.list_template_entries("vroidstudio")
    ids = {e.template_id for e in entries}
    assert "export_dialog_title" in ids
    assert "sample_tile_female" in ids


def test_ensure_placeholder_templates(tmp_path: Path, monkeypatch):
    root = tmp_path / "templates"
    monkeypatch.setattr(template_library, "_TEMPLATES_ROOT", root)
    manifest = root / "vroidstudio" / "manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        """
app: vroidstudio
version: default
templates:
  - id: test_tile
    file: test_tile.png
    description: test
""",
        encoding="utf-8",
    )
    created = template_library.ensure_placeholder_templates("vroidstudio")
    assert len(created) == 1
    assert Path(created[0]).is_file()


def test_resolve_template_after_placeholder(monkeypatch, tmp_path: Path):
    root = tmp_path / "templates"
    monkeypatch.setattr(template_library, "_TEMPLATES_ROOT", root)
    manifest = root / "vroidstudio" / "manifest.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        """
app: vroidstudio
version: default
templates:
  - id: ok_btn
    file: ok_btn.png
""",
        encoding="utf-8",
    )
    template_library.ensure_placeholder_templates("vroidstudio")
    path = template_library.resolve_template("vroidstudio", "ok_btn")
    assert path.is_file()
