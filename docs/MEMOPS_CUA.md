---
title: windows-computer-use-mcp — doctrine (2026-06-16)
status: active
tags: [cua, windows-computer-use-mcp, automation, gui, fleet]
related:
  - docs/ROADMAP.md
  - docs/TOOLS.md
  - docs/ARCHITECTURE.md
  - docs/cua-nsis-certification.md
---

# windows-computer-use-mcp — MemOps note

## One-line thesis

**A Windows UI automation MCP server that is both a tool for AI agents and an agent itself** — 22 portmanteau tools, autonomous mission engine, macros, watchers, self-healing, screen recording, dual OCR providers. Replaces pywinauto-mcp (v0.5.x) with full CUA capability.

## Naming

| Public | GitHub | Port |
|--------|--------|------|
| **windows-computer-use-mcp** | `sandraschi/windows-computer-use-mcp` | 10989 |

Old `pywinauto-mcp` redirects automatically. Local directory still `pywinauto-mcp` (locked by open handles).

## Current state (v0.7.0 — released 2026-06-15)

### Tool surface (22 portmanteau tools)

| Tool | Operations | Phase |
|------|-----------|-------|
| `automation_windows` | list, focus, maximize, minimize, close, get_state, wait_window | core |
| `automation_elements` | find, click, set_text, get_text, select_option, verify, state, tree | core |
| `automation_mouse` | click, double_click, right_click, move_to, drag, scroll, get_pos | core |
| `automation_keyboard` | type_text, press_key, hotkey, paste, get_state | core |
| `automation_visual` | screenshot, ocr, highlight, get_window_state, record, record_to_gif | core |
| `automation_shortcut` | semantic shortcuts per app, multi-shortcut workflows | core |
| `automation_dialog` | list, wait, click_button, set_field, handle_file_dialog | core |
| `automation_assert` | verify_state, verify_text, verify_file, verify_process | core |
| `automation_smart` | discover, click (by intent), set_text (by intent), wait (by intent) | P4 |
| `automation_mission` | run, status, cancel, resume, run_preset | P1 |
| `automation_macro` | record, stop, replay, replay_with_verify, replay_video, list | P3 |
| `automation_watch` | start, stop, status, list | P5 |
| `automation_system` | telemetry, strategies, health, env, settings | P2 |
| `automation_faces` | detect, save (opt-in, off by default) | core |
| `automation_keylogger` | start, stop, status (opt-in, off by default) | core |
| `analyze_winapp` | crawl, discover, portfolio | core |

### Key capabilities

- **Autonomous mission engine**: `automation_mission(run="open Notepad, type hello, save")` — decomposes via LLM sampling, executes each step with retry (exponential backoff), outcome verification, self-healing. Returns per-step pass/fail with evidence.
- **Outcome verification**: post-condition checks after each action — text appeared, element state changed. Verification failure returns `status=blocked` with detail.
- **Retry policy**: unified `RetryPolicy` with strategy chain: refocus → wait_stable → fallback_selector → escalate. Each strategy uses exponential backoff.
- **Adaptive element location**: cascades through title → auto_id → control_id → class+type → OCR region scan when element not found.
- **Self-healing**: mission engine checks window alive before each step, re-launches app if dead, aborts after 5 consecutive failures.
- **Cross-app data flow**: steps with `store_as` save to shared context; `$ref:key` reads from context.
- **Event-driven watchers**: background thread polling — window_appears, window_closes, text_appears, element_appears.
- **Telemetry store**: SQLite-backed at `~/.windows-computer-use-mcp/telemetry.db`. Every action logged with strategy, success, duration.
- **Telemetry-driven strategy**: mission engine queries `get_best_strategy()` from telemetry before each step.
- **Mission presets**: `presets/*.json` files loaded by `automation_mission(run_preset="notepad_demo")`.
- **YAML/JSON workflow runner**: `scripts/run-workflow.py` with `just run-workflow <file>` recipe.

### OCR (dual provider)

| Provider | Default | Install | Speed |
|----------|---------|---------|-------|
| **Windows Media OCR** | **Yes** (auto-probed first) | Zero-install (WinRT built-in) | Fast |
| **Tesseract 5.5** | Fallback | `just install-tesseract` or manual | Moderate |

Env: `WINDOWS_COMPUTER_USE_MCP_OCR_PROVIDER=auto|tesseract|windowsmedia`

### Screen recording

- `automation_visual(record, duration=10, fps=10)` — MP4 via ffmpeg pipe (no intermediate files)
- `record_to_gif` — animated GIF output
- `automation_macro(replay, record_video=True)` — records screen during macro replay
- ffmpeg 8.1.1 at `C:\Users\sandr\scoop\shims\ffmpeg.exe`

### System tray controller

- `scripts/tray-control.py` — standalone tray app
- Health icon (green/grey), HITL toggle, approve 5min
- Recording indicator (red R icon) during capture
- Quick macro replay from saved files
- View log, server status, telemetry query
- Ctrl+Shift+R hotkey for recording
- 5-second polling

### CUA-NSIS certification

12 phases pass: kill → install → launch → health → window → screenshot → diagnostics → uninstall → Tesseract → 3 desktop tests → cert. Config at `scripts/cua-nsis-config.json`.

### Safety

- HITL (human-in-the-loop) blocks all mutating actions by default
- Bypass via `WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1`
- Blocked actions return `status="error"` with `"Blocked by HITL safety setting: ..."`
- Keylogger and face detection opt-in only (off by default)

## What it is NOT

- Not a vision model — screenshots go to host LLM
- Not reliable on Unity/GPU apps without foreground + calibration
- Not a replacement for `autohotkey-mcp` (AHK has faster hotkey dispatch for power users)

## Fleet role

```
windows-computer-use-mcp (10989)  ← hands: click, type, mission, record
  → autohotkey-mcp (10747)         ← alternative: faster hotkey dispatch for power users
  → system-admin-mcp (10861)      ← preflight: process find, RAM/disk depletion
  → browser-mcp (10781)           ← cross-ref: Playwright + CUA composing
```

## Design principles

1. **Mission-first** — complex goals should be decomposed and verified, not scripted
2. **Assert everything** — every action must verify its outcome
3. **Evidence on failure** — before/after/diff for host LLM review
4. **Telemetry-driven** — learn from past failures to choose better strategies
5. **Shortcut where possible** — clicks only as fallback

## Roadmap

See [docs/ROADMAP.md](./ROADMAP.md) — 14 items across short/medium/long term:

- **Short (done)**: Win Media OCR default, screen recording, replay-to-video, tray polish, mission presets, YAML workflow runner
- **Medium**: multi-monitor coordinates, app-specific automation profiles, YAML/JSON portable runner
- **Long**: computer vision, voice control, remote desktop, self-improving telemetry, Docker sandbox

## Env cheatsheet

```powershell
$env:WINDOWS_COMPUTER_USE_MCP_URL = "http://127.0.0.1:10989"
$env:WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL = "1"       # disable HITL
$env:WINDOWS_COMPUTER_USE_MCP_OCR_PROVIDER = "tesseract"  # force Tesseract
$env:WINDOWS_COMPUTER_USE_MCP_DISPATCH = "foreground"  # VRoid / Unity
$env:WINDOWS_COMPUTER_USE_MCP_KEYBOARD = "win32"       # raw Win32 input
$env:SYSTEM_ADMIN_MCP_URL = "http://127.0.0.1:10861"
```

## Relations

- implements [[FLEET_AUTOMATION_PIPELINE]] Windows GUI automation leg
- blocks [[vroidstudio-mcp]] reliability until fully calibrated
- pairs with [[virtualization-mcp]] for sandbox isolation (not wired)
- cross-ref [[autohotkey-mcp]] for complementary AHK-based automation
