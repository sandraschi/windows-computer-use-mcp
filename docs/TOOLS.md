# MCP tools reference

22 portmanteau tools. All use `operation` enum. Responses are `ToolResult {status, message, data, recovery_tip}`.

## Core automation

| Tool | Key operations | Added |
|------|---------------|-------|
| `automation_windows` | list, find, focus, maximize, minimize, close, position, state | — |
| `automation_elements` | click, set_text, list, info, get_text, exists, wait | — |
| `automation_elements` (verify) | + `verify=True`, `verify_text="expected"` — outcome check after action | 1 |
| `automation_mouse` | click, double_click, right_click, scroll, drag, hover, position, telemetry | — |
| `automation_keyboard` | type, hotkey, press, hold, release | — |
| `automation_visual` | screenshot, extract_text (OCR), find_image, highlight | — |
| `automation_assert` | hash, diff, wait_stable, assert_changed, assert_unchanged, assert_template, assert_text | — |
| `automation_dialog` | set_path, confirm, submit_path (file dialog entry) | — |
| `automation_shortcut` | send, list, describe (app-specific semantic shortcuts) | — |
| `automation_task` | run, status, cancel, list_profiles, list_templates | — |
| `automation_system` | status, info, clipboard, processes, start_app, **telemetry** | 2 |
| `get_window_state` | per-window UIA snapshot (ax/som/vision), snapshot_id + element_index | — |
| `get_desktop_state` | full desktop UI tree with optional OCR enrichment | — |

## Autonomous & agentic

| Tool | Key operations | Added |
|------|---------------|-------|
| `automation_mission` | **run** (goal → decompose → execute → retry → verify), plan, status, cancel | 1 |
| `automation_mission` (workflow) | **workflow** — explicit steps, app launch, timeout, data chaining with `$ref:` | 3, 5 |
| `automation_macro` | record, stop, replay, **replay_with_verify**, list | 3 |
| `automation_smart` | **click** (intent-based, across all windows), **discover**, list_apps, list_controls | 4 |
| `automation_watch` | start, status, stop, list (background thread, 4 condition types) | 5 |
| `automation_analyze` | crawl, discover, portfolio (WinApp UI tree analysis with HUD overlay) | — |

## Safety & opt-in

| Tool | Notes |
|------|-------|
| `approve_automation` | Grant HITL time window for mouse/keyboard |
| `automation_safety` | status, reset_counters — kill switch, rate limits, dry-run |
| `automation_face` | **Off by default** — `WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1` + `face` extra |
| `global_keylogger` | **Off by default** — `WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER=1` (non-stealth debug hook) |

## Examples

```python
# Autonomous mission
automation_mission(run="open Notepad, type 'hello world', save as test.txt")

# Smart intent-based click (finds across all windows)
automation_smart(click="the Save button")

# Record and replay a sequence
automation_macro(record=True)  # ... run tools ...  automation_macro(stop=True)
automation_macro(replay=True, name="my_macro")

# Watch for a window to appear
automation_watch(start=True, condition="window_appears", target="Update Available")
# Poll with:  automation_watch(status=True, watcher_id=...)

# Multi-app workflow with data chaining
automation_mission(workflow=True, app="notepad.exe", actions=[
    {"tool": "elements", "params": {"click": True, "title": "Yes"}, "store_as": "clicked"},
    {"tool": "mouse", "params": {"click": True, "x": 100, "y": 200}},
])

# Telemetry query
automation_system(telemetry=True)
```

## Retry policy (server-side)

All mutating operations use `RetryPolicy` with strategy chain: refocus → wait_stable → fallback_selector → escalate. Each strategy gets up to 3 attempts with exponential backoff. The mission engine additionally self-heals: if target window dies, re-launches the app and retries.

## Adaptive element location

When `automation_elements(click, title="Save")` fails, the cascade tries: title → auto_id → control_id → class+type → OCR region scan. The winning strategy is logged to telemetry so future missions can prefer it.

## Telemetry

Every action is logged to `~/.windows-computer-use-mcp/telemetry.db`. Query with `automation_system(telemetry=True)` for per-tool failure rates, best strategies, and top error patterns.
