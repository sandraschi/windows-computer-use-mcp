"""Demo: open one Notepad and type a short message with human-ish pauses.

Opens a dedicated temp ``.txt`` so the window title is discoverable (Windows 11
often does not map the launcher PID to the editor HWND).

Run: ``uv run python examples/demo_notepad_typewriter.py``
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import subprocess
import sys
import time
from pathlib import Path

_EXAMPLES_DIR = str(Path(__file__).resolve().parent)
if _EXAMPLES_DIR not in sys.path:
    sys.path.insert(0, _EXAMPLES_DIR)

import pyautogui
from demo_notepad_helpers import make_temp_demo_files, notepad_exe, wait_for_notepad_title
from pywinauto import Desktop

logger = logging.getLogger(__name__)

TEXT = """=== windows-computer-use-mcp demo ===

The cursor danced, nine panes aligned,
And this line was typed by design.

- typed by demo_notepad_typewriter.py
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Typewriter effect in Notepad.")
    parser.add_argument("--fast", action="store_true", help="Shorter delays between keys.")
    args = parser.parse_args()

    tmp, basenames = make_temp_demo_files("demo_typewriter", 1)
    path = os.path.join(tmp, basenames[0])
    np = notepad_exe()
    subprocess.Popen([np, path], shell=False)

    print(f"Waiting for Notepad ({basenames[0]!r})…")
    hwnd = wait_for_notepad_title(basenames[0], timeout=30.0)
    if hwnd is None:
        print("Could not find Notepad window by title.", file=sys.stderr)
        sys.exit(1)

    desktop = Desktop(backend="uia")
    wnd = desktop.window(handle=hwnd)
    try:
        wnd.set_focus()
    except Exception as e:
        logger.debug("set_focus: %s", e)
        wnd.activate()
    time.sleep(0.35)

    base = 0.012 if args.fast else 0.045
    pyautogui.PAUSE = 0
    for i, ch in enumerate(TEXT):
        if ch == "\n":
            pyautogui.press("enter")
        else:
            pyautogui.write(ch, interval=0)
        wobble = base * 0.8 * abs(math.sin(i * 2.17))
        time.sleep(base + wobble)

    print("Typed. Leave Notepad open or close it yourself. Done.")


if __name__ == "__main__":
    main()
