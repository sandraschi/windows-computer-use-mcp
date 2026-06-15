# windows-computer-use-mcp — Claude Code Guide

## Overview
Windows UI automation server: click, type, OCR, missions, macros, event watchers. Pair with virtualization-mcp for sandbox isolation. Read docs/SAFETY.md.

## Tool Surface (18 portmanteau tools)

| Tool | Operations | Phase |
|------|-----------|-------|
| `automation_windows` | list, find, focus, maximize, minimize, close, position | — |
| `automation_elements` | click, set_text, list, info, get_text, exists, wait, verify with verify+verify_text | 1 |
| `automation_mouse` | click, double_click, right_click, scroll, drag, hover | — |
| `automation_keyboard` | type, hotkey, press, hold | — |
| `automation_visual` | screenshot, extract_text (OCR), find_image, highlight | — |
| `automation_assert` | hash, diff, wait_stable, assert_changed, assert_text, assert_template | — |
| `automation_dialog` | set_path, confirm, submit_path | — |
| `automation_shortcut` | send, list, describe (semantic app shortcuts) | — |
| `automation_task` | run, status, cancel, list_profiles (closed-loop runner) | — |
| `automation_system` | status, info, clipboard, processes, start_app, telemetry | 2 |
| `automation_mission` | **run** (autonomous loop), plan, workflow, status, cancel, record, replay | 1, 5 |
| `automation_macro` | record, stop, replay, replay_with_verify, list | 3 |
| `automation_smart` | discover, list_apps, list_controls, **click** (intent-based) | 4 |
| `automation_watch` | start, status, stop, list (event-driven window/text watchers) | 5 |
| `automation_analyze` | crawl, discover, portfolio (WinApp UI tree analysis) | — |
| `get_window_state` | per-window UIA snapshot with SOM/ax/vision capture modes | — |
| `get_desktop_state` | full desktop UI tree | — |
| `automation_face` | face recognition (opt-in) | — |

## Standards
- Tools use `operation` enum param (portmanteau pattern)
- Responses: ToolResult with status, message, data, recovery_tip
- Dual transport: stdio + HTTP (`MCP_TRANSPORT=http`)
- Safety: HITL approval, kill switch, dry-run, rate limits (docs/SAFETY.md)

## Key Files
- README.md, INSTALL.md, docs/TOOLS.md, docs/py-stack.md
- skills/desktop-automation-protocol/SKILL.md
