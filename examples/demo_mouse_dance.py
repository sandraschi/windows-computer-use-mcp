"""Demo: move the mouse in a chaotic but smooth "dance" across the screen.

Run from repo root (with the package on PYTHONPATH), e.g.:
  uv run python examples/demo_mouse_dance.py
  uv run python examples/demo_mouse_dance.py --seconds 12

Uses :mod:`windows_computer_use_mcp.win32_mouse` (same backend as ``automation_mouse``).
Failsafe is off so the pointer can use the full screen (including upper-left).
"""

from __future__ import annotations

import argparse
import math
import time

from windows_computer_use_mcp.win32_mouse import screen_size, set_cursor_pos


def main() -> None:
    parser = argparse.ArgumentParser(description="Mouse pointer dance demo.")
    parser.add_argument(
        "--seconds",
        type=float,
        default=15.0,
        help="How long to run (default 15).",
    )
    args = parser.parse_args()

    w, h = screen_size()
    cx, cy = w / 2.0, h / 2.0
    scale = min(w, h) * 0.35

    t0 = time.perf_counter()
    phase = 0.0
    print("Mouse dance running (Win32 / win32_mouse). Ctrl+C to stop.")

    try:
        while time.perf_counter() - t0 < args.seconds:
            phase += 0.11 + 0.02 * math.sin(phase * 0.5)
            a = phase
            jitter = 0.12 * math.sin(a * 11.7) * math.cos(a * 7.3)
            x = cx + scale * (0.55 * math.sin(a * 2.7) + 0.25 * math.sin(a * 5.1 + 1.3) + jitter)
            y = cy + scale * (0.55 * math.cos(a * 2.1) + 0.25 * math.sin(a * 4.4 + 0.7) - jitter * 0.9)
            wobble = 0.08 * scale * math.sin(phase * 13.0)
            x += wobble * math.cos(phase * 3.0)
            y += wobble * math.sin(phase * 3.0)

            x = max(2, min(w - 3, x))
            y = max(2, min(h - 3, y))

            set_cursor_pos(int(x), int(y), failsafe=False)
            time.sleep(0.003)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        print("Done.")


if __name__ == "__main__":
    main()
