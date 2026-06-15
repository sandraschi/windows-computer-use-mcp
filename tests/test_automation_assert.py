"""Tests for automation_assert and assert_engine."""

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from windows_computer_use_mcp import assert_engine
from windows_computer_use_mcp.tools.models import AssertOperationRequest, ToolResult
from windows_computer_use_mcp.tools.portmanteau_assert import automation_assert


def _solid(path: Path, color: tuple[int, int, int], size: tuple[int, int] = (100, 100)) -> Path:
    img = Image.new("RGB", size, color)
    img.save(path)
    return path


def _with_rect(path: Path, base: tuple[int, int, int], rect_color: tuple[int, int, int]) -> Path:
    img = Image.new("RGB", (100, 100), base)
    draw = ImageDraw.Draw(img)
    draw.rectangle((20, 20, 80, 80), fill=rect_color)
    img.save(path)
    return path


class TestAssertEngine:
    def test_sha256_deterministic(self, tmp_path: Path):
        p = _solid(tmp_path / "a.png", (255, 0, 0))
        img = assert_engine.capture_image(image_path=str(p))
        h1 = assert_engine.image_hash(img, "sha256")
        h2 = assert_engine.image_hash(img, "sha256")
        assert h1 == h2
        assert len(h1) == 64

    def test_dhash_similar_images(self, tmp_path: Path):
        p1 = _solid(tmp_path / "a.png", (100, 100, 100))
        p2 = _solid(tmp_path / "b.png", (102, 100, 100))
        h1 = assert_engine.image_hash(assert_engine.capture_image(image_path=str(p1)), "dhash")
        h2 = assert_engine.image_hash(assert_engine.capture_image(image_path=str(p2)), "dhash")
        assert assert_engine.hashes_match(h1, h2, algorithm="dhash")

    def test_diff_detects_change(self, tmp_path: Path):
        before = _solid(tmp_path / "before.png", (0, 0, 0))
        after = _with_rect(tmp_path / "after.png", (0, 0, 0), (255, 255, 255))
        b = assert_engine.capture_image(image_path=str(before))
        a = assert_engine.capture_image(image_path=str(after))
        diff = assert_engine.image_diff(b, a, output_path=str(tmp_path / "diff.png"))
        assert diff["changed_pct"] > 10.0
        assert Path(diff["diff_path"]).is_file()

    def test_diff_identical_zero_change(self, tmp_path: Path):
        p = _solid(tmp_path / "same.png", (50, 50, 50))
        img = assert_engine.capture_image(image_path=str(p))
        diff = assert_engine.image_diff(img, img)
        assert diff["changed_pct"] == 0.0

    def test_wait_stable_static_file(self, tmp_path: Path):
        p = _solid(tmp_path / "static.png", (10, 20, 30))
        result = assert_engine.wait_stable(image_path=str(p), timeout_s=1.0)
        assert result["stable"] is True
        assert result["final_hash"]

    def test_crop_region(self):
        img = Image.new("RGB", (200, 200), (0, 0, 0))
        cropped = assert_engine.crop_region(img, (10, 10, 50, 50))
        assert cropped.size == (40, 40)


class TestAutomationAssertTool:
    def test_hash_operation(self, tmp_path: Path):
        p = _solid(tmp_path / "h.png", (1, 2, 3))
        req = AssertOperationRequest(operation="hash", image_path=str(p))
        result = automation_assert(req)
        assert isinstance(result, ToolResult)
        assert result.status == "success"
        assert result.data["hash"]
        assert result.data["algorithm"] == "dhash"

    def test_hash_region_requires_region(self, tmp_path: Path):
        p = _solid(tmp_path / "h.png", (1, 2, 3))
        req = AssertOperationRequest(operation="hash_region", image_path=str(p))
        result = automation_assert(req)
        assert result.status == "error"

    def test_diff_operation(self, tmp_path: Path):
        before = _solid(tmp_path / "b.png", (0, 0, 0))
        after = _with_rect(tmp_path / "a.png", (0, 0, 0), (200, 200, 200))
        req = AssertOperationRequest(
            operation="diff",
            image_path=str(before),
            image_path_b=str(after),
            output_path=str(tmp_path / "out.png"),
        )
        result = automation_assert(req)
        assert result.status == "success"
        assert result.data["changed_pct"] > 0

    def test_assert_changed_passes(self, tmp_path: Path):
        before = _solid(tmp_path / "b.png", (0, 0, 0))
        after = _with_rect(tmp_path / "a.png", (0, 0, 0), (255, 0, 0))
        req = AssertOperationRequest(
            operation="assert_changed",
            image_path=str(before),
            image_path_b=str(after),
            change_threshold_pct=1.0,
        )
        result = automation_assert(req)
        assert result.status == "success"

    def test_assert_changed_fails_on_identical(self, tmp_path: Path):
        p = _solid(tmp_path / "same.png", (42, 42, 42))
        req = AssertOperationRequest(
            operation="assert_changed",
            image_path=str(p),
            image_path_b=str(p),
            change_threshold_pct=0.1,
        )
        result = automation_assert(req)
        assert result.status == "error"
        assert result.recovery_tip

    def test_assert_unchanged_passes(self, tmp_path: Path):
        p = _solid(tmp_path / "same.png", (42, 42, 42))
        req = AssertOperationRequest(
            operation="assert_unchanged",
            image_path=str(p),
            image_path_b=str(p),
        )
        result = automation_assert(req)
        assert result.status == "success"

    def test_assert_unchanged_fails_on_change(self, tmp_path: Path):
        before = _solid(tmp_path / "b.png", (0, 0, 0))
        after = _with_rect(tmp_path / "a.png", (0, 0, 0), (255, 255, 0))
        req = AssertOperationRequest(
            operation="assert_unchanged",
            image_path=str(before),
            image_path_b=str(after),
            unchanged_threshold_pct=0.5,
        )
        result = automation_assert(req)
        assert result.status == "error"

    def test_wait_stable_static(self, tmp_path: Path):
        p = _solid(tmp_path / "s.png", (5, 5, 5))
        req = AssertOperationRequest(operation="wait_stable", image_path=str(p), timeout_s=2.0)
        result = automation_assert(req)
        assert result.status == "success"
        assert result.data["stable"] is True

    def test_assert_template_with_synthetic(self, tmp_path: Path):
        haystack_path = tmp_path / "hay.png"
        template_path = tmp_path / "tpl.png"
        _with_rect(haystack_path, (0, 0, 0), (255, 0, 0))
        tpl = Image.new("RGB", (20, 20), (255, 0, 0))
        tpl.save(template_path)

        req = AssertOperationRequest(
            operation="assert_template",
            image_path=str(haystack_path),
            template_path=str(template_path),
            match_threshold=0.7,
        )
        result = automation_assert(req)
        assert result.status == "success"
        assert result.data["found"] is True

    @pytest.mark.skipif(not assert_engine.OCR_AVAILABLE, reason="pytesseract not installed")
    def test_assert_text(self, tmp_path: Path):
        img_path = tmp_path / "text.png"
        img = Image.new("RGB", (200, 60), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "Export VRM", fill=(0, 0, 0))
        img.save(img_path)

        req = AssertOperationRequest(
            operation="assert_text",
            image_path=str(img_path),
            expected_text="Export VRM",
        )
        result = automation_assert(req)
        if result.status == "error" and "tesseract" in (result.message or "").lower():
            pytest.skip("Tesseract binary not available")
        assert result.status == "success"
