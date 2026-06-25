# pywinauto-mcp Build Log

## 2026-06-25 — FastMCP 3.4+ Upgrade (Sandra, AI-assisted)

### Changes

- **FastMCP upgrade**: Migrated from FastMCP 2.13.1 API patterns to FastMCP 3.4+
  - Removed `create_proxy` / `add_provider` pattern from `app.py` (FastMCP 3.x uses transport natively)
  - Fixed `get_registered_tools()` for FastMCP 3.x internal tool manager API
  - Updated transport.py with E10048 retry bind loop (copy from inkscape-mcp reference)
- **run_server.py**: Rewrote for dual transport (MCP_PORT → HTTP, fallback → stdio)
  - Added eager imports for `_strptime`, `_datetime`, `cachetools` (PyInstaller compatibility)
  - Set `OTEL_PYTHON_CONTEXT=contextvars_context` before any import
- **PyInstaller spec**: Created `pywinauto-mcp-backend.spec` (fleet standard naming)
  - `noarchive=True`, `strip=False`, `upx=False`, `console=False`
  - `runtime_hooks=['hooks/runtime-opentelemetry.py']`
  - `.dist-info` strip with fastmcp/prefab_ui/opentelemetry preservation
  - SKIP list for heavy binaries (torch, playwright, pandas, scipy, etc.)
- **hooks/runtime-opentelemetry.py**: Created (fleet standard — patches `importlib.metadata.entry_points`)
- **native/backend.rs**: Updated fleet standard pattern
  - Port changed 10700 → 10789
  - Added `PYTHONUNBUFFERED=1` env var
  - Added indefinite backend health check loop (TCP connect poll with `backend-status` event)
  - `free_port()` with UAC elevation fallback (copy from inkscape-mcp)
- **native/main.rs**: Async spawn in setup (match inkscape-mcp pattern)
- **native/tauri.conf.json**: Updated for fleet standard
  - `frontendDist`: `../web_sota/dist`
  - Resources: `.env.example` instead of `.env` (no API key leak)
  - CSP updated for port 10789
  - `identifier`: `ai.fleet.pywinauto-mcp`
- **native/windows/hooks.nsh**: Added `UninstallPrevious` macro
- **native/build.ps1**: Added PyInstaller smoke test, size gate (>= 5 MB), `.env.example` bundling

### Known Issues (pre-existing, not regressions)

- 10700 hardcoded in old spec/backend (now 10789) — old backup files still reference 10700
- `.env.example` uses PORT=8000 — this is for standalone mode, not Tauri

### Build Status

- [X] PyInstaller backend builds (77.8 MB, smoke test PASSED)
- [X] Frontend (web_sota) builds (496 KB JS, tsc + Biome pass)
- [X] NSIS installer builds (80.3 MB)
- [ ] CUA smoke test passes (pending user execution)

### Verification

| Check | Result |
|-------|--------|
| Ruff lint (Python) | 0 errors |
| Biome lint (TS/JS) | 35 files auto-fixed, 36 pre-existing warnings |
| tsc --noEmit | 0 errors |
| Vite build | Succeeds (4.27s) |
| FastMCP 3.4+ import | `run_http_async`/`run_stdio_async` confirmed |
| Tool registration | 20 tools detected |
| PyInstaller smoke test | PASSED (5s run, no crash) |
| NSIS installer | `Pywinauto MCP_0.7.0_x64-setup.exe` (80.3 MB) |
| Nuclear zombie kill | hooks.nsh: Stop-Process + taskkill + NSIS plugin + UAC elevation + Sleep 3000 |

### File Summary

- `src/windows_computer_use_mcp/app.py` — FastMCP 3.4+ constructor
- `src/windows_computer_use_mcp/main.py` — `get_registered_tools()` via `_list_tools()` async
- `src/windows_computer_use_mcp/transport.py` — E10048 retry bind loop
- `run_server.py` — dual transport (MCP_PORT → HTTP, fallback → stdio)
- `hooks/runtime-opentelemetry.py` — PyInstaller entry_points patch
- `pywinauto-mcp-backend.spec` — fleet standard, noarchive, SKIP list
- `native/src/backend.rs` — port 10789, health check, UAC elevation, PYTHONUNBUFFERED
- `native/src/main.rs` — async spawn in setup
- `native/tauri.conf.json` — web_sota/dist, .env.example, CSP
- `native/windows/hooks.nsh` — nuclear kill + UninstallPrevious
- `native/build.ps1` — smoke test + size gate + .env.example bundling
- `web_sota/src/lib/use-zoom.ts` — Ctrl+Scroll zoom with localStorage
- `web_sota/src/pages/dashboard.tsx` — data-testid dashboard + backend-dot + restart
- `web_sota/src/components/layout/topbar.tsx` — dynamic health dot
- `BUILD_LOG.md` — this file
