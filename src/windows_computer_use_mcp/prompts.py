"""MCP prompts: operator protocol and runbook text for desktop automation."""

from __future__ import annotations

from windows_computer_use_mcp.app import app

if app is not None:

    @app.prompt(
        name="desktop_automation_operator_protocol",
        title="Desktop automation — operator protocol (foreground / terminal)",
    )
    def desktop_automation_operator_protocol() -> str:
        """Tell the user to step back from the terminal/IDE while pywinauto runs; avoid focus fights."""
        return """## Desktop automation — operator protocol

Use this when the user asks to **start an app** and **test or automate it via pywinauto**.

### Tell the user (before the first UI action)

1. **Step back from the terminal and IDE** once automation starts — do not type in the terminal or keep the chat/IDE in the foreground while mouse/keyboard steps run.
2. **Do not bring other apps to the foreground** (browser, mail, second IDE) unless the plan explicitly requires them — the **target app under test should keep focus**.
3. If they need to read logs, use a **second monitor** or wait for a **pause** between steps; **avoid Alt+Tab churn** mid-workflow.
4. If **HITL / approve_automation** is required, they should **only** complete that approval, then **return focus** to the target window (or leave the desktop clear) as needed.

### Why

PyWinAuto drives the **real desktop focus and input queue**. Focus stealing is the #1 cause of flaky “it clicked the wrong thing” runs.

### Docs

Repository: `docs/OPERATOR_PROTOCOL.md` and `docs/SAFETY.md`.
"""

    @app.prompt(
        name="desktop_automation_runbook",
        title="Desktop automation — agent runbook (start app + test)",
    )
    def desktop_automation_runbook() -> str:
        """Structured steps for agents: approve, launch, focus, test, minimize human interference."""
        return """## Runbook: start app + test via pywinauto

1. **Safety**: Confirm `docs/SAFETY.md` expectations; mention **virtualization-mcp** if the user needs a disposable VM/Sandbox.
2. **Set expectations**: Explain **foreground protocol** — user steps back from terminal/IDE; no extra apps in front during the run.
3. **HITL**: If mouse/keyboard automation is gated, call **approve_automation** (or ask the user to approve) **before** long sequences.
4. **Launch**: Start the target app (user or **automation_system** / shell — whichever matches policy); wait until its window exists.
5. **Focus**: Use **automation_windows** to find/activate the target; avoid clicking into the IDE or terminal.
6. **Test**: Drive **automation_elements** / **automation_mouse** / **automation_keyboard** as needed; prefer **get_desktop_state** for discovery when unclear.
7. **Report**: Summarize results without asking the user to foreground the agent UI mid-sequence.

If the user tries to "help" by switching windows, **stop and remind** them of the operator protocol.
"""
