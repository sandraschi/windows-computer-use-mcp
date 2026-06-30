"""E2E fixtures — LibreOffice GUI (requires soffice on host)."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

_MARK_E2E = pytest.mark.e2e
_MARK_LO = pytest.mark.libreoffice
_MARK_GUI = pytest.mark.requires_gui


def _resolve_soffice() -> Path | None:
    env = os.getenv("PYWINAUTO_E2E_SOFFICE", "").strip()
    if env:
        p = Path(env)
        return p if p.is_file() else None
    candidates = [
        Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
        Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


SOFFICE_EXE = _resolve_soffice()


@pytest.fixture(autouse=True)
def loose_libreoffice_uia(monkeypatch):
    """LibreOffice exposes many Custom/Pane nodes — include named visible controls."""
    monkeypatch.setenv("windows_computer_use_mcp_LOOSE_UIA", "1")


SKIP_NO_SOFFICE = pytest.mark.skipif(
    SOFFICE_EXE is None,
    reason="LibreOffice soffice not found (set PYWINAUTO_E2E_SOFFICE)",
)


@pytest.fixture
def soffice_exe():
    if SOFFICE_EXE is None:
        pytest.skip("LibreOffice soffice not installed")
    return SOFFICE_EXE


@pytest.fixture
def libreoffice_calc(soffice_exe: Path):
    """Launch Calc and yield HWND; kill process on teardown."""
    proc = subprocess.Popen(
        [str(soffice_exe), "--calc"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    handle = _wait_for_window("LibreOffice Calc", timeout=45.0)
    if handle is None:
        proc.terminate()
        pytest.skip("LibreOffice Calc window did not appear")
    try:
        yield {"process": proc, "handle": handle, "title_hint": "LibreOffice Calc"}
    finally:
        _close_process(proc)


def _wait_for_window(title_fragment: str, timeout: float) -> int | None:
    from pywinauto import Desktop

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            for w in Desktop(backend="uia").windows():
                text = w.window_text() or ""
                if title_fragment in text:
                    return int(w.handle)
        except Exception:
            pass
        time.sleep(0.5)
    return None


def _close_process(proc: subprocess.Popen) -> None:
    try:
        proc.terminate()
        proc.wait(timeout=8)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
