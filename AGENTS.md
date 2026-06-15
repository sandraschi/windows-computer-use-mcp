# windows-computer-use-mcp — Agent Guide

## Quick Reference

18 portmanteau tools. All use `operation` enum. Responses are ToolResult `{status, message, data, recovery_tip}`.

**Autonomous:** `automation_mission(run="open Notepad, type hello, save")` — decomposes, executes, retries, verifies.
**Smart:** `automation_smart(click="the Save button")` — finds element by intent across all windows.
**Macros:** `automation_macro(record=true)` → run tools → `stop()` → `replay()`.
**Watchers:** `automation_watch(start, condition="window_appears", target="Update")`.
**Telemetry:** `automation_system(telemetry)` — query failure patterns per tool.
**Workflows:** `automation_mission(workflow, actions=[...], app="notepad.exe")`.

## Safety
- Read docs/SAFETY.md first
- Mutating actions require HITL approval (bypass with WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1)
- Face and keylogger are opt-in (off by default)

## Entry Point
`uv run windows-computer-use-mcp` → `windows_computer_use_mcp.main:main`

## Fleet
- mcp-central-docs for fleet-wide standards
- Pair with virtualization-mcp for sandbox isolation
