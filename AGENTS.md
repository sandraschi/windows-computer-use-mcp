# windows-computer-use-mcp — Agent Guide

## Quick Reference

22 tools (20 portmanteaus + `approve_automation` + `automation_safety`). All use `operation` enum. Responses are ToolResult `{status, message, data, recovery_tip}`.

**Autonomous:** `automation_mission(run="open Notepad, type hello, save")` — preflights session, decomposes, executes, retries, verifies; pauses for UAC.
**Smart:** `automation_smart(click="the Save button")` — finds element by intent across all windows.
**Macros:** `automation_macro(record=true)` → run tools → `stop()` → `replay()`.
**Watchers:** `automation_watch(start, condition="window_appears", target="Update")`.
**Telemetry:** `automation_system(telemetry)` — query failure patterns per tool.
**Preflight:** `automation_system(preflight)` — run before any mission; `detect_uac` tells UAC apart from lock screen.
**Background input:** `background_click` / `background_type` / `background_key` — PostMessage, no cursor warp (delivery unverifiable, confirm via screenshot/OCR).
**Tables:** `analyze_winapp(extract_table, header_row=true)`; virtual lists via `crawl_scroll`.
**Tray:** `automation_windows(tray_list/tray_click)`.
**Workflows:** `automation_mission(workflow, actions=[...], app="notepad.exe")`.

## Safety
- Read docs/SAFETY.md first
- DANGEROUS: every click/keystroke hits the live desktop — prefer dry-run or a VM sandbox for anything untrusted
- Mutating actions require HITL approval (bypass with WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1)
- Per-app allowlist: WINDOWS_COMPUTER_USE_MCP_ALLOWED_APPS=notepad.exe,calc.exe
- Face and keylogger are opt-in (off by default)

## Entry Point
`uv run windows-computer-use-mcp` → `windows_computer_use_mcp.main:main`

## Fleet
- mcp-central-docs for fleet-wide standards
- Pair with virtualization-mcp for sandbox isolation
