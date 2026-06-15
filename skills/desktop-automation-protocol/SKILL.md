---
name: desktop-automation-protocol
description: How to use windows-computer-use-mcp effectively — tool selection, focus rules, safety, and mission design.
version: 2.0.0
standard: SOTA v14.2.0 (FastMCP 3.2.0)
---

# Desktop automation protocol (windows-computer-use-mcp)

## Tool selection guide

| Goal | Tool | Example |
|------|------|---------|
| Click a known button | `automation_elements(click, title="Save")` | fast, needs exact title |
| Click by intent | `automation_smart(click="the Save button")` | slower, finds across all windows |
| Complex multi-step | `automation_mission(run="save file as PDF")` | autonomous loop with retry |
| Record + replay | `automation_macro(record) → stop → replay` | repeatable sequences |
| Wait for event | `automation_watch(start, "window_appears", "Update")` | event-driven triggers |
| Explore desktop | `automation_smart(discover)` | get all running apps |
| Extract + chain | `automation_mission(workflow, actions, store_as, dollar-ref)` | cross-app data pipeline |

## Focus rules
- After automation starts, do not Alt+Tab or touch the mouse
- The target window must stay in foreground during click/type sequences
- If HITL approval appears, approve it and let the target window regain focus
- Prefer reading logs between paused steps or on a second monitor

## Safety
- Read docs/SAFETY.md before production use
- Pair with virtualization-mcp for sandbox/VM isolation when running untrusted automation
- Opt-in features (face, keylogger) are off by default — enable only when needed

## Mission design (automation_mission)
For `run` operation: provide a clear, concrete goal. The server decomposes via LLM sampling.
For `workflow` operation: provide explicit steps with tool, params, label, and optional store_as/dollar-ref for data chaining.
For self-healing: set app_path on steps so the mission can re-launch crashed apps.
