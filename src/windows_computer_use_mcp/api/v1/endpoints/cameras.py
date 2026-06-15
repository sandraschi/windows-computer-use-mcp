"""Enumerate local UVC / integrated cameras via OpenCV (Windows: DirectShow first)."""

from __future__ import annotations

import logging
import os
import platform

import cv2
from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(tags=["cameras"])

# Probe indices [0, MAX_INDEX) — some systems expose many virtual devices; cap is configurable.
_DEFAULT_MAX = 10
MAX_CAMERA_INDEX = min(
    int(os.getenv("windows_computer_use_mcp_CAMERA_MAX_INDEX", str(_DEFAULT_MAX))),
    32,
)


class CameraDevice(BaseModel):
    """One OpenCV-openable capture device."""

    index: int = Field(..., description="Pass to cv2.VideoCapture(index) / automation_face camera_index")
    label: str = Field(..., description="Human-readable label (may include resolution)")
    width: int | None = None
    height: int | None = None


def _try_open(index: int) -> cv2.VideoCapture | None:
    """Prefer DirectShow on Windows for reliable USB + integrated enumeration."""
    if platform.system() == "Windows":
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            return cap
        cap.release()
    cap = cv2.VideoCapture(index)
    if cap.isOpened():
        return cap
    return None


def enumerate_cameras(max_index: int = MAX_CAMERA_INDEX) -> list[CameraDevice]:
    """Open each index briefly; release immediately. Skips indices that do not open."""
    out: list[CameraDevice] = []
    for i in range(max(0, max_index)):
        cap = None
        try:
            cap = _try_open(i)
            if cap is None:
                continue
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if w <= 0 or h <= 0:
                ok, _frame = cap.read()
                if ok:
                    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            label = f"Camera {i}"
            if w > 0 and h > 0:
                label = f"Camera {i} ({w}x{h})"
            out.append(
                CameraDevice(
                    index=i,
                    label=label,
                    width=w if w > 0 else None,
                    height=h if h > 0 else None,
                )
            )
        except Exception as e:
            logger.debug("Camera probe %s: %s", i, e)
        finally:
            if cap is not None:
                cap.release()
    return out


@router.get("/", response_model=list[CameraDevice])
async def list_cameras() -> list[CameraDevice]:
    """List cameras that OpenCV can open on this host (local USB / integrated UVC)."""
    return enumerate_cameras()
