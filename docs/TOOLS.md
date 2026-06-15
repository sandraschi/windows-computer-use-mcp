# MCP tools reference

Portmanteau tools for the Windows **computer use agent**. Each tool takes an `operation` (and operation-specific fields). Call `automation_system(operation="help")` at runtime for the live catalog.

## Core tools

| Tool | Operations (summary) |
|------|----------------------|
| `automation_windows` | list, find, activate, maximize, minimize, move, resize, close, wait |
| `automation_elements` | click, hover, set_text, get_text, tree, rect, exists, … |
| `automation_mouse` | position, click, drag, scroll, move, telemetry |
| `automation_keyboard` | press, hotkey, type, key_down/up |
| `automation_visual` | screenshot, extract_text, find_image |
| `automation_assert` | verify UI state, stability, evidence on failure |
| `automation_dialog` | detect, dismiss, confirm native dialogs |
| `automation_shortcut` | app-specific shortcut tables (e.g. VRoid) |
| `automation_task` | chained steps with retries |
| `automation_system` | help, status, clipboard, processes, start_app |
| `get_desktop_state` | UI tree / set-of-mark snapshot |

## Safety

| Tool | Purpose |
|------|---------|
| `approve_automation` | Grant HITL window for mouse/keyboard |
| `automation_safety` | `status`, `reset_counters` — kill switch, rate limits |

## Opt-in only

| Tool | Enable |
|------|--------|
| `automation_face` | **Off by default.** `WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1` + `face` extra |
| `global_keylogger` | **Off by default.** `WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER=1` — non-stealth debug hook; [SAFETY.md](SAFETY.md) §6 |

## Examples

```python
automation_windows("find", title="Notepad", partial=True)
automation_elements("set_text", window_handle=12345, control_id="Edit1", text="Hello")
automation_mouse("click", x=400, y=300)
automation_assert("window_title", window_handle=12345, expected="Untitled - Notepad")
```

See [examples/README.md](../examples/README.md) and `just demo`.
