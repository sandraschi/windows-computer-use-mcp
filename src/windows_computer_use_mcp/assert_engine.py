"""Image capture, hashing, diffing, and UI stability assertions for automation_assert."""

from __future__ import annotations

import hashlib
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def _region_tuple(
    left: int | None,
    top: int | None,
    right: int | None,
    bottom: int | None,
) -> tuple[int, int, int, int] | None:
    if all(v is not None for v in (left, top, right, bottom)):
        return int(left), int(top), int(right), int(bottom)
    return None


def capture_image(
    *,
    image_path: str | None = None,
    window_handle: int | None = None,
    region: tuple[int, int, int, int] | None = None,
) -> Image.Image:
    """Load from path or capture window/screen."""
    if image_path:
        return Image.open(image_path).convert("RGB")

    from PIL import ImageGrab

    if window_handle is not None:
        from windows_computer_use_mcp.win32_window import clamp_bbox, get_window_bbox

        left, top, right, bottom = get_window_bbox(window_handle)
        if region:
            left += region[0]
            top += region[1]
            right = min(left + (region[2] - region[0]), right)
            bottom = min(top + (region[3] - region[1]), bottom)
        left, top, right, bottom = clamp_bbox((left, top, right, bottom))
        return ImageGrab.grab(bbox=(left, top, right, bottom)).convert("RGB")

    if region:
        return ImageGrab.grab(bbox=region).convert("RGB")

    return ImageGrab.grab().convert("RGB")


def crop_region(image: Image.Image, region: tuple[int, int, int, int] | None) -> Image.Image:
    if not region:
        return image
    left, top, right, bottom = region
    return image.crop((left, top, right, bottom))


def compute_sha256(image: Image.Image) -> str:
    buf = image.tobytes()
    return hashlib.sha256(buf).hexdigest()


def compute_dhash(image: Image.Image, hash_size: int = 8) -> str:
    """Difference hash — 64-bit hex, tolerant of minor rendering noise."""
    gray = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = list(gray.getdata())
    bits: list[int] = []
    for row in range(hash_size):
        row_start = row * (hash_size + 1)
        for col in range(hash_size):
            bits.append(1 if pixels[row_start + col] > pixels[row_start + col + 1] else 0)
    value = sum(bit << i for i, bit in enumerate(bits))
    return f"{value:016x}"


def hamming_distance_hex(a: str, b: str) -> int:
    """Hamming distance between equal-length hex hashes."""
    if len(a) != len(b):
        return max(len(a), len(b)) * 4
    ai = int(a, 16)
    bi = int(b, 16)
    xor = ai ^ bi
    return xor.bit_count()


def hashes_match(a: str, b: str, *, algorithm: str, max_hamming: int = 5) -> bool:
    if algorithm == "dhash":
        return hamming_distance_hex(a, b) <= max_hamming
    return a == b


def image_hash(image: Image.Image, algorithm: str = "dhash") -> str:
    if algorithm == "sha256":
        return compute_sha256(image)
    return compute_dhash(image)


def image_diff(
    before: Image.Image,
    after: Image.Image,
    *,
    change_threshold: int = 25,
    output_path: str | None = None,
) -> dict[str, Any]:
    """Pixel diff between two images. Returns changed_pct and optional diff PNG."""
    a = np.array(before.convert("RGB"))
    b = np.array(after.convert("RGB"))

    if a.shape != b.shape:
        after_resized = after.convert("RGB").resize(before.size, Image.Resampling.LANCZOS)
        b = np.array(after_resized)

    diff = np.abs(a.astype(np.int16) - b.astype(np.int16))
    gray_diff = diff.mean(axis=2)
    mask = gray_diff > change_threshold
    changed = int(np.count_nonzero(mask))
    total = mask.size
    changed_pct = round((changed / total) * 100.0, 3) if total else 0.0

    diff_path = None
    if output_path and CV2_AVAILABLE:
        heatmap = mask.astype(np.uint8) * 255
        cv2.imwrite(output_path, heatmap)
        diff_path = output_path
    elif output_path:
        Image.fromarray(mask.astype(np.uint8) * 255).save(output_path)
        diff_path = output_path

    return {
        "changed_pct": changed_pct,
        "pixels_changed": changed,
        "total_pixels": total,
        "diff_path": diff_path,
        "sizes_match": before.size == after.size,
    }


def wait_stable(
    *,
    window_handle: int | None = None,
    image_path: str | None = None,
    region: tuple[int, int, int, int] | None = None,
    stable_frames_required: int = 2,
    poll_interval_s: float = 0.5,
    timeout_s: float = 10.0,
    hash_algorithm: str = "dhash",
    output_dir: str | None = None,
) -> dict[str, Any]:
    """Poll until UI hash is unchanged for N consecutive frames."""
    deadline = time.monotonic() + timeout_s
    last_hash = ""
    stable_count = 0
    frames_observed = 0
    last_path: str | None = None
    out_dir = Path(output_dir) if output_dir else Path.cwd()

    while time.monotonic() < deadline:
        img = capture_image(image_path=image_path, window_handle=window_handle, region=region)
        current_hash = image_hash(img, hash_algorithm)
        frames_observed += 1

        if last_hash and hashes_match(last_hash, current_hash, algorithm=hash_algorithm):
            stable_count += 1
            if stable_count >= stable_frames_required:
                return {
                    "stable": True,
                    "frames_observed": frames_observed,
                    "final_hash": current_hash,
                    "screenshot_path": last_path,
                    "hash_algorithm": hash_algorithm,
                }
        else:
            stable_count = 1
            last_hash = current_hash
            if window_handle is not None or image_path is None:
                snap = out_dir / f"stable_{int(time.time() * 1000)}.png"
                img.save(snap)
                last_path = str(snap)

        if image_path:
            # Static file — one read is enough for testing; simulate one stable frame
            return {
                "stable": True,
                "frames_observed": 1,
                "final_hash": current_hash,
                "screenshot_path": image_path,
                "hash_algorithm": hash_algorithm,
            }

        time.sleep(poll_interval_s)

    return {
        "stable": False,
        "frames_observed": frames_observed,
        "final_hash": last_hash,
        "screenshot_path": last_path,
        "hash_algorithm": hash_algorithm,
        "timeout_s": timeout_s,
    }


def assert_template_match(
    haystack: Image.Image,
    template_path: str,
    *,
    match_threshold: float = 0.8,
    region: tuple[int, int, int, int] | None = None,
) -> dict[str, Any]:
    if not CV2_AVAILABLE:
        raise RuntimeError("OpenCV required for assert_template")

    search = crop_region(haystack, region)
    template = cv2.imread(template_path)
    if template is None:
        raise FileNotFoundError(f"Template not found: {template_path}")

    hay = cv2.cvtColor(np.array(search), cv2.COLOR_RGB2BGR)
    result = cv2.matchTemplate(hay, template, cv2.TM_CCOEFF_NORMED)
    _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

    th, tw = template.shape[:2]
    center_x = max_loc[0] + tw // 2
    center_y = max_loc[1] + th // 2
    if region:
        center_x += region[0]
        center_y += region[1]

    return {
        "found": max_val >= match_threshold,
        "confidence": round(float(max_val), 4),
        "center_x": center_x,
        "center_y": center_y,
        "match_threshold": match_threshold,
    }


def assert_text_in_image(
    image: Image.Image,
    expected_text: str,
    *,
    exact_match: bool = False,
    region: tuple[int, int, int, int] | None = None,
    language: str = "eng",
) -> dict[str, Any]:
    if not OCR_AVAILABLE:
        raise RuntimeError("pytesseract required for assert_text")

    crop = crop_region(image, region)
    ocr_text = pytesseract.image_to_string(crop, lang=language).strip()
    if exact_match:
        found = ocr_text == expected_text
    else:
        found = expected_text.lower() in ocr_text.lower()

    return {"found": found, "ocr_text": ocr_text, "expected_text": expected_text}
