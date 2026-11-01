# Troubleshooting — windows-computer-use-mcp

## Mission blocked by preflight (locked session / UAC / resources)

`automation_mission(run)` refuses to start, or a workflow returns `blocked`
with `preflight failed (...)`. Run `automation_system(preflight)` for the
per-check breakdown:
- `interactive_session` failed → unlock the session / restore the RDP window.
  UIA cannot reach a locked or minimized desktop.
- `uac_prompt` failed → a UAC consent prompt is on the secure desktop.
  Approve or dismiss it on the physical console, then re-run. Missions pause
  for UAC mid-run (`paused_uac`) — they do not fail through it.
- `disk_free` / `memory_available` failed → free resources and retry.

`automation_system(detect_uac)` tells a UAC prompt apart from a lock screen.

## Background input ignored by a control

`background_click` / `background_type` / `background_key` return success but
nothing happens: the control ignores PostMessage input (common for custom,
Electron, and IME/composed controls). Confirm with a screenshot, then fall
back in this order: `automation_elements(set_text)` for text (UIA ValuePattern
needs no focus either) → `dispatch="background"` element click (tries UIA
invoke first) → foreground `click`/`type` with the window focused.

## Mission blocked by the app allowlist

`app_blocked` / `Mission stopped by app allowlist`: the target process is
outside `WINDOWS_COMPUTER_USE_MCP_ALLOWED_APPS`. Either add the app or unset
the variable. Unresolvable targets fail open (allowed, flagged `app_unknown`).

## Backend never becomes healthy (`start.ps1 -BackendOnly` times out)

1. Check the port owner: `Get-NetTCPConnection -LocalPort 10789 -State Listen`.
   An elevated squatter (`Access is denied` on kill) blocks binding — prove on
   another port instead: `.\start.ps1 -BackendOnly -BackendPort 18099`.
2. NSSM service `mcp-pywinauto-mcp` holds the port when running:
   `Get-Service mcp-pywinauto-mcp`. Stop it for dev runs, or reuse it.

## `McpError: Session terminated` over HTTP while `/health` is 200

The parent FastAPI app was not entering the FastMCP session lifespan
(BUG-038 class). Fixed in `server.py::lifespan` via
`_mcp_http.lifespan(app)` (FastMCP 3.4.4 contract — `mcp.lifespan(app)`
crashes startup on this version). Verify live:
`POST /mcp` initialize must return 200 + `mcp-session-id`.

## Bare `/mcp` vs `/mcp/` path

Single mount at `/mcp` with `http_app(path="/")` (no double prefix).
Verify both POST initialize and `tools/list` over a session after edits.

## Coverage gate fails (`--cov-fail-under=30`)

Hardware-gated CUA code (win32/pywinauto paths) is skipped off-host.
Run `pytest tests/ -q --no-cov -p no:cacheprovider` for the behavior signal;
treat the coverage number as advisory until hardware-gated tests land.

## `uv sync` fails removing `windows-computer-use-mcp.exe` (os error 32)

The NSSM service (or a running backend) holds the venv entry point.
Use `uv run --no-sync ...` for lint/test, or stop the service first.

## Silent swallows (S110/S112)

Un-ignored 2026-10-10; every handler logs at `debug` (loop probes) or
`warning` (API paths). `tools/archived/*` is frozen dead code with a scoped
per-file-ignore — do not extend that ignore to live code.

## CI shows old `queued` dispatches

GitHub Actions is effectively inert on this repo (last completed run
2026-05-28). Gates run locally: `ruff check`, `ruff format --check`,
`pytest`, `tsc --noEmit`, `biome ci` (web_sota).
