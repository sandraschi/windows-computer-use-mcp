"""Per-app template image library for assert_template / find_image (T2.3)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_TEMPLATES_ROOT = Path(__file__).resolve().parent / "templates"


@dataclass(frozen=True)
class TemplateEntry:
    template_id: str
    file: str
    description: str
    match_threshold: float = 0.8
    region_hint: str | None = None
    version: str = "default"

    def resolve_path(self, app: str) -> Path:
        return _TEMPLATES_ROOT / app / self.version / self.file


def templates_root() -> Path:
    return _TEMPLATES_ROOT


def manifest_path(app: str) -> Path:
    return _TEMPLATES_ROOT / app / "manifest.yaml"


def load_manifest(app: str) -> dict[str, Any]:
    path = manifest_path(app)
    if not path.is_file():
        return {"app": app, "version": "default", "templates": []}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


def list_template_entries(app: str) -> list[TemplateEntry]:
    data = load_manifest(app)
    default_version = str(data.get("version", "default"))
    entries: list[TemplateEntry] = []
    for raw in data.get("templates") or []:
        if not isinstance(raw, dict) or not raw.get("id"):
            continue
        entries.append(
            TemplateEntry(
                template_id=str(raw["id"]),
                file=str(raw.get("file", f"{raw['id']}.png")),
                description=str(raw.get("description", "")),
                match_threshold=float(raw.get("match_threshold", 0.8)),
                region_hint=raw.get("region_hint"),
                version=str(raw.get("version", default_version)),
            )
        )
    return entries


def resolve_template(app: str, template_id: str, *, version: str | None = None) -> Path:
    """Resolve template_id to an on-disk PNG path; raises FileNotFoundError if missing."""
    for entry in list_template_entries(app):
        if entry.template_id != template_id:
            continue
        ver = version or entry.version
        path = _TEMPLATES_ROOT / app / ver / entry.file
        if path.is_file():
            return path
        raise FileNotFoundError(f"Template file missing for {app}/{template_id}: {path}")
    raise KeyError(f"Unknown template_id '{template_id}' for app '{app}'")


def list_templates(app: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for entry in list_template_entries(app):
        path = _TEMPLATES_ROOT / app / entry.version / entry.file
        out.append(
            {
                "template_id": entry.template_id,
                "app": app,
                "version": entry.version,
                "file": entry.file,
                "path": str(path),
                "exists": path.is_file(),
                "description": entry.description,
                "match_threshold": entry.match_threshold,
                "region_hint": entry.region_hint,
            }
        )
    return out


def ensure_placeholder_templates(app: str = "vroidstudio") -> list[str]:
    """Create minimal placeholder PNGs for manifest entries (dev/smoke bootstrap)."""
    try:
        from PIL import Image
    except ImportError:
        logger.warning("PIL not available — cannot create placeholder templates")
        return []

    created: list[str] = []
    for entry in list_template_entries(app):
        path = entry.resolve_path(app)
        if path.is_file():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        # Distinct colors per template id for debugging
        seed = sum(ord(c) for c in entry.template_id)
        color = ((seed * 37) % 200 + 32, (seed * 59) % 200 + 32, (seed * 91) % 200 + 32)
        Image.new("RGB", (32, 32), color=color).save(path)
        created.append(str(path))
    return created
