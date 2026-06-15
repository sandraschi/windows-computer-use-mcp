---
name: desktop-automation-protocol
description: Foreground and focus rules when driving Windows UI via windows-computer-use-mcp (step back from terminal/IDE; avoid focus fights).
version: 1.0.0
standard: SOTA v14.2.0 (FastMCP 3.2.0)
---

# Desktop automation protocol (windows-computer-use-mcp)

## When this applies

The user wants to **start an app** and **test or automate it** using **pywinauto** / **windows-computer-use-mcp** tools.

## Tell the user

- After automation starts, **do not keep the terminal or IDE in the foreground** for typing or “helping.”
- **Do not Alt+Tab** to other apps (browser, mail, chat) while a click/type sequence is in progress — the **target app should keep focus**.
- If **HITL (human-in-the-loop) approval** appears, complete **only** that, then let the **target window** stay in front again.
- Prefer reading logs on a **second monitor** or between **paused** steps.

## Canonical docs in repo

- `docs/OPERATOR_PROTOCOL.md`
- `docs/SAFETY.md`

## MCP prompts (v14.2.0 registered)

- `desktop_automation_runbook`: Use this to generate high-level execution plans before starting an `automation_mission`.
- `safety_audit_protocol`: Use this to verify current server-side safety flags.

## Mission Planning (Sampling)

When using `automation_mission`, the server will internally call `ctx.sample()`. Agents should provide a clear, descriptive natural language goal to maximize planning fidelity.
