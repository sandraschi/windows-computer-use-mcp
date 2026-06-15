# Cua-style desktop loop (operator)

**Roadmap:** [CUA_PARITY_ROADMAP.md](./CUA_PARITY_ROADMAP.md)  
**Fleet doc:** [CUA_DRIVER_AND_PYWINAUTO.md](file:///D:/Dev/repos/mcp-central-docs/patterns/CUA_DRIVER_AND_PYWINAUTO.md)

## Quick loop

```text
1. automation_windows("find", title="Excel", partial=True)  → HWND
2. get_window_state({ window_handle, capture_mode: "som" }) → snapshot_id
3. automation_elements({ operation: "click", window_handle, snapshot_id, element_index: 3, dispatch: "background" })
4. get_window_state(...)  → verify
```

## Excel while Cursor is focused

**Intent:** Yes — that is what `dispatch=background` and per-window snapshots are for.

**Reality (Phase 1):** Partial. Office UIA often accepts `invoke` / `click_input` without foreground; some controls still need `dispatch: "foreground"`. Coordinate fallback **moves the real cursor** — not true Cua no-warp yet.

Use a **dedicated MCP profile** (not default IDE webapp chain). Read [SAFETY.md](./SAFETY.md).

## Environment

```powershell
$env:WINDOWS_COMPUTER_USE_MCP_DISPATCH = "background"   # optional; default foreground
```

## fleet-agent-mcp

With pywinauto HTTP on **10789**, fleet-agent **`fleet_bridge`** alias **`pywinauto`** can call `get_window_state` and `automation_elements`. See [fleet-agent-mcp/docs/pywinauto-cua-loop.md](file:///D:/Dev/repos/fleet-agent-mcp/docs/pywinauto-cua-loop.md).

Pair **libreoffice-mcp** for headless PDF/convert; use pywinauto e2e against live Calc for GUI verification (`pytest -m e2e`).

## MCP config snippet

```powershell
uv run windows-computer-use-mcp mcp-config
```
