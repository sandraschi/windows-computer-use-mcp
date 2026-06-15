# Examples and demos

Runnable scripts for **local Windows** (same dependency stack as `windows-computer-use-mcp`: `pywinauto`, `pyautogui`). Install the project or use **`uv run`** from the repo root.

| Script | What it does |
|--------|----------------|
| [`demo_mouse_dance.py`](demo_mouse_dance.py) | Moves the mouse in a layered Lissajous-style “dance” for a few seconds (`--seconds`). |
| [`demo_notepad_grid.py`](demo_notepad_grid.py) | Tiles **nine** windows in a **3x3** grid. **Default:** nine `cmd.exe` consoles (`PyDemoGrid0`…`8`) so Windows 11 does not merge into one Notepad. **`--use-notepad`** tries nine temp `.txt` files (may find fewer if Notepad is tabbed). `--auto --dwell N`; `--no-close`. |
| [`demo_notepad_typewriter.py`](demo_notepad_typewriter.py) | Opens one Notepad and types a short message with human-ish timing. |
| [`notepad_basic.py`](notepad_basic.py) | Legacy placeholder flow (MCP-oriented comments only). |
| [`calculator_advanced.py`](calculator_advanced.py) | Legacy placeholder flow for Calculator. |
| [`system_monitoring.py`](system_monitoring.py) | System/process oriented sample. |
| [`notepad_automation.ps1`](notepad_automation.ps1) | Older REST-style example (ports may not match your deployment). |

**More demo ideas (not all implemented):** Paint spiral with drag, Calculator “2+2” smoke test via UIA, cascading non-overlapping windows of mixed apps, telemetry HUD duration sweep, clipboard round-trip race.

See **[`docs/SAFETY.md`](../docs/SAFETY.md)** before running anything that drives the real desktop in an unattended agent loop.
