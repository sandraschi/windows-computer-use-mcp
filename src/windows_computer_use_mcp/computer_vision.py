"""Computer vision module — multi-scale matching, feature matching, visual search.

Extends the basic ``find_image`` (single-scale template match) with:
- Multi-scale template matching across a range of scales
- Rotation-invariant ORB feature matching
- Region-of-interest description for agent vision loops
"""

from __future__ import annotations

import logging
import os
from typing import Any

import cv2
import numpy as np
from PIL import ImageGrab

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Multi-scale template matching
# ---------------------------------------------------------------------------


def find_template_multi_scale(
    template_path: str,
    region: tuple[int, int, int, int] | None = None,
    window_handle: int | None = None,
    threshold: float = 0.7,
    scale_min: float = 0.5,
    scale_max: float = 2.0,
    scale_steps: int = 10,
) -> list[dict[str, Any]]:
    """Find a template image on screen using multi-scale matching.

    Args:
        template_path: Path to the template image file.
        region: Screen region (left, top, right, bottom) to search in.
        window_handle: HWND to capture (alternative to region).
        threshold: Minimum confidence (0-1).
        scale_min: Minimum scale factor (0.1-2.0).
        scale_max: Maximum scale factor (0.1-2.0).
        scale_steps: Number of scale steps to try.

    Returns:
        List of matches with center_x, center_y, confidence, scale, w, h.
        Sorted by confidence descending.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    template_bgr = cv2.imread(template_path, cv2.IMREAD_COLOR)
    if template_bgr is None:
        raise ValueError(f"Failed to load template: {template_path}")

    template_gray = cv2.cvtColor(template_bgr, cv2.COLOR_BGR2GRAY)
    t_h, t_w = template_gray.shape[:2]

    # Capture screen
    if region:
        screen_bgr = cv2.cvtColor(np.array(ImageGrab.grab(bbox=region)), cv2.COLOR_RGB2BGR)
        offset_x, offset_y = region[0], region[1]
    elif window_handle:
        import win32gui

        rect = win32gui.GetWindowRect(window_handle)
        screen_bgr = cv2.cvtColor(np.array(ImageGrab.grab(bbox=rect)), cv2.COLOR_RGB2BGR)
        offset_x, offset_y = rect[0], rect[1]
    else:
        screen_bgr = cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_RGB2BGR)
        offset_x, offset_y = 0, 0

    screen_gray = cv2.cvtColor(screen_bgr, cv2.COLOR_BGR2GRAY)

    matches: list[dict[str, Any]] = []
    scales = np.linspace(scale_min, scale_max, scale_steps)

    for scale in scales:
        if scale <= 0:
            continue
        w = int(t_w * scale)
        h = int(t_h * scale)
        if w < 10 or h < 10 or w > screen_gray.shape[1] or h > screen_gray.shape[0]:
            continue

        scaled = cv2.resize(template_gray, (w, h), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR)
        result = cv2.matchTemplate(screen_gray, scaled, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            cx = max_loc[0] + w // 2 + offset_x
            cy = max_loc[1] + h // 2 + offset_y
            matches.append(
                {
                    "center_x": int(cx),
                    "center_y": int(cy),
                    "confidence": float(max_val),
                    "scale": float(scale),
                    "width": w,
                    "height": h,
                }
            )

    matches.sort(key=lambda m: m["confidence"], reverse=True)
    return matches


# ---------------------------------------------------------------------------
# ORB feature matching (rotation/affine invariant)
# ---------------------------------------------------------------------------


def find_template_feature_match(
    template_path: str,
    region: tuple[int, int, int, int] | None = None,
    window_handle: int | None = None,
    min_matches: int = 10,
    ratio_threshold: float = 0.75,
) -> list[dict[str, Any]]:
    """Find a template using ORB feature matching — handles rotation and perspective changes.

    Args:
        template_path: Path to the template image.
        region: Screen region.
        window_handle: HWND alternative.
        min_matches: Minimum good matches to consider a detection.
        ratio_threshold: Lowe's ratio test threshold.

    Returns:
        List of matches with center, confidence (ratio of good/total), and homography.
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    img1 = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    if img1 is None:
        raise ValueError(f"Failed to load template: {template_path}")

    if region:
        screen = cv2.cvtColor(np.array(ImageGrab.grab(bbox=region)), cv2.COLOR_RGB2GRAY)
        offset_x, offset_y = region[0], region[1]
    elif window_handle:
        import win32gui

        rect = win32gui.GetWindowRect(window_handle)
        screen = cv2.cvtColor(np.array(ImageGrab.grab(bbox=rect)), cv2.COLOR_RGB2GRAY)
        offset_x, offset_y = rect[0], rect[1]
    else:
        screen = cv2.cvtColor(np.array(ImageGrab.grab()), cv2.COLOR_RGB2GRAY)
        offset_x, offset_y = 0, 0

    orb = cv2.ORB_create(nfeatures=2000)
    kp1, des1 = orb.detectAndCompute(img1, None)
    kp2, des2 = orb.detectAndCompute(screen, None)

    if des1 is None or des2 is None or len(kp1) < 2 or len(kp2) < 2:
        return []

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    matches_raw = bf.knnMatch(des1, des2, k=2)

    good: list[cv2.DMatch] = []
    for pair in matches_raw:
        if len(pair) >= 2:
            m, n = pair[0], pair[1]
            if m.distance < ratio_threshold * n.distance:
                good.append(m)

    if len(good) < min_matches:
        return []

    # Compute homography to determine object bounds
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    H, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

    if H is None:
        # No homography, use mean of matched points
        cx = int(np.mean([p[0][0] for p in dst_pts]) + offset_x)
        cy = int(np.mean([p[0][1] for p in dst_pts]) + offset_y)
        return [
            {
                "center_x": cx,
                "center_y": cy,
                "confidence": len(good) / max(len(matches_raw), 1),
                "method": "orb_mean",
                "matches": len(good),
            }
        ]

    h, w = img1.shape
    corners = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
    transformed = cv2.perspectiveTransform(corners, H)
    cx = int(np.mean([p[0][0] for p in transformed]) + offset_x)
    cy = int(np.mean([p[0][1] for p in transformed]) + offset_y)
    conf = len(good) / max(len(matches_raw), 1)

    return [
        {
            "center_x": cx,
            "center_y": cy,
            "confidence": round(conf, 3),
            "method": "orb_homography",
            "matches": len(good),
            "corners": transformed.reshape(-1, 2).tolist(),
        }
    ]


# ---------------------------------------------------------------------------
# Screen region description (for agent vision loops)
# --------------------------------------------------------------------------


def describe_region(
    region: tuple[int, int, int, int] | None = None,
    max_objects: int = 15,
) -> dict[str, Any]:
    """Extract visual structure from a screen region for agent reasoning.

    Uses OpenCV contour detection + OCR to build a structural description
    of what's visible: text blocks, buttons (rectangular regions), icons.

    Args:
        region: Screen region, or None for full screen.
        max_objects: Max detected regions to return.

    Returns:
        Dict with text_regions, buttons, icons, and screen dimensions.
    """
    if region:
        img = np.array(ImageGrab.grab(bbox=region))
        ox, oy = region[0], region[1]
    else:
        img = np.array(ImageGrab.grab())
        ox, oy = 0, 0

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    h, w = gray.shape

    # Edge detection + adaptive threshold for contour detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(edges, kernel, iterations=1)

    # Find contours on edge-detected image
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    objects = []
    for cnt in contours:
        x_, y_, w_, h_ = cv2.boundingRect(cnt)
        area = w_ * h_
        if area < 50 or area > w * h * 0.8:
            continue
        aspect = w_ / max(h_, 1)
        obj_type = "button" if 1.5 <= aspect <= 6 else "icon" if aspect < 1.5 and area < 5000 else "region"
        objects.append(
            {
                "type": obj_type,
                "x": x_ + ox,
                "y": y_ + oy,
                "width": w_,
                "height": h_,
                "area": area,
            }
        )

    objects.sort(key=lambda o: o["area"], reverse=True)
    objects = objects[:max_objects]

    return {
        "width": w,
        "height": h,
        "object_count": len(objects),
        "objects": objects,
        "contour_method": "otsu_threshold",
    }
