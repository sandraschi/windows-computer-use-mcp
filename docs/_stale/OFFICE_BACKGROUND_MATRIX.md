# Office / LibreOffice background dispatch matrix

**Dispatch:** `WINDOWS_COMPUTER_USE_MCP_DISPATCH=background` or per-call `dispatch="background"`.  
**Blocked:** `status=blocked`, `data.code=background_unavailable`.

| App | `get_window_state` (ax/som) | UIA `invoke` / `click_input` | PostMessage to HWND | Typical fallback |
|-----|----------------------------|------------------------------|---------------------|------------------|
| LibreOffice Calc | Good | Mixed (cells often need focus) | Partial (client area) | `foreground` for cell edit |
| LibreOffice Writer | Good | Mixed | Partial | `foreground` for typing |
| Microsoft Excel | Good | Mixed (ribbon varies by build) | Partial | `foreground` for in-cell edit |
| Notepad | Good | Good | Good | Often works background |
| Chromium (Electron) | Good | Poor | Poor | `foreground` |
| Canvas / game UIs | Poor (tree thin) | Poor | Poor | `vision` + `foreground` |

**Fleet pairing:** Headless convert/PDF → [libreoffice-mcp](https://github.com/sandraschi/libreoffice-mcp). Live GUI loops → **windows-computer-use-mcp** `get_window_state` (e2e: `tests/e2e/test_libreoffice_cua_loop.py`).

**E2E:** `pytest -m e2e` (requires LibreOffice `soffice` on PATH or default install path). Tests set `WINDOWS_COMPUTER_USE_MCP_LOOSE_UIA=1` so LibreOffice `Custom`/`Pane` nodes with names are indexed.

**Loose UIA (office apps):** `WINDOWS_COMPUTER_USE_MCP_LOOSE_UIA=1` includes named visible controls not in the default type allowlist.
