# Operator protocol — desktop automation (windows-computer-use-mcp)

When you ask to **start an application** and **test or drive it via pywinauto**, the automation only works if **one foreground story** is stable. This doc is for **humans** and for **agents** explaining the same rules to the user.

## Why this exists

- PyWinAuto drives **whatever window is focused** and the **real mouse/keyboard queue**.
- If you keep **the IDE, terminal, or chat** in front, automation may click/type the **wrong surface**, or fight you for focus.
- “Helping” by **switching apps mid-run** (Alt+Tab, clicking the terminal, opening another window) is the most common way to **flakify** a run.

## Rules (share with the user before the first click)

1. **Step back from the terminal / IDE** once the run has started — do not type in the terminal or bring the agent UI to the foreground unless you are answering **HITL (human-in-the-loop) approval** or **stopping** the run.
2. **Do not surface another app on purpose** (browser, mail, second IDE) while the workflow is driving the target app — let the **target app hold focus** unless the plan explicitly needs a different window.
3. **If you must read output**, prefer **side-by-side** or a **second monitor**, or wait for a **natural pause** between tool calls — avoid stealing focus from the app under test.
4. **HITL (human-in-the-loop; `approve_automation`)** may appear for mouse/keyboard — when it does, **complete only that approval**, then **return focus** to the target app (or leave the desktop clear) as the workflow expects.
5. **Kill switch / dry-run** — see [`SAFETY.md`](SAFETY.md); automation is not a substitute for Sandbox/VM isolation when you need a disposable desktop.

## For agents (wording you can surface verbatim)

> “I’m going to start or test **{app}** using desktop automation. **Please don’t keep the terminal or IDE in the foreground** while clicks run — switch to **{app}** or leave it focused, and **avoid Alt+Tabbing** to other apps until I say the step is done. If you need to approve a prompt, do that only, then let the automated window stay on top.”

## Profiles: foreground (default) vs background (Cua-style)

| Profile | Env | Operator expectation |
|---------|-----|----------------------|
| **Foreground** (default) | `WINDOWS_COMPUTER_USE_MCP_DISPATCH=foreground` or unset | Target app should hold focus; see rules above. |
| **Background** | `WINDOWS_COMPUTER_USE_MCP_DISPATCH=background` | User may keep **Cursor/IDE** focused; agent uses `get_window_state` + `snapshot_id` / `element_index`. Coordinate clicks may still move the **physical** cursor unless UIA/PostMessage succeeds. |

Background profile is for **dedicated computer-use MCP configs only** — not default IDE + webapp chains. See [`CUA_PARITY.md`](CUA_PARITY.md), [`OFFICE_BACKGROUND_MATRIX.md`](OFFICE_BACKGROUND_MATRIX.md).

Optional: `WINDOWS_COMPUTER_USE_MCP_TRAJECTORY_LOG=1` (JSONL under `%LOCALAPPDATA%\windows-computer-use-mcp\trajectories`), `WINDOWS_COMPUTER_USE_MCP_AGENT_OVERLAY=1` (virtual agent marker).

## Related

- [`SAFETY.md`](SAFETY.md) — HITL (human-in-the-loop), env limits, two-server model with `virtualization-mcp`.
- [`CUA_PARITY.md`](CUA_PARITY.md) — Cua-shaped tool loop
