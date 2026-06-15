# Testing (CI vs local)

Aligned with **mcp-central-docs** → `standards/testing-environment-aware.md` (clone sibling repo **mcp-central-docs**).

## Fleet context

**windows-computer-use-mcp** is the **implemented** variant for **local Windows + OpenCV / USB cameras** (hardware-marked tests skip in CI). Central docs describe the same pattern and **fleet intent**: roll the drop-in scaffold into **all other repos** that touch **hardware** — IP or UVC **cameras**, **robots**, **scanners**, **vacuums**, **smart home / IoT**, and similar — shared **markers** and **hooks**, with **device-specific fixtures** per repo.

## What this repo does

| Location | Behavior |
|----------|----------|
| **GitHub Actions / `CI=true`** | No real Windows desktop, no OpenCV cameras. Tests marked `requires_hardware` or `destructive` are **skipped**. Prefer **mocks** and **HTTP** (`TestClient`) tests. |
| **Local Windows** | You can run real desktop / camera probes. Opt in to heavy suites with env vars (e.g. `PYWINAUTO_TEST_REAL_WINDOWS=1` for Notepad window tests). |

## Markers

Defined in `tests/conftest_env.py` and `[tool.pytest.ini_options]` in `pyproject.toml`.

- **`requires_hardware`** — Opens real OpenCV devices or host-only code paths. **Skipped in CI.**
- **`destructive`** — Drives real UI (e.g. Notepad tests). **Skipped in CI**; locally also needs `PYWINAUTO_TEST_REAL_WINDOWS=1` where documented.
- **`requires_network`** — LAN-dependent; skipped in CI.
- **`ci_only`** — Runs when `CI=true`; skipped on typical local runs.

## Commands

```powershell
# Same as CI: hardware tests skipped
$env:CI = "true"; uv run pytest tests/ -q

# Local: include hardware-marked tests (needs Windows + devices as applicable)
uv run pytest tests/ -q

# Only hardware-marked tests
uv run pytest tests/ -m requires_hardware -q
```

## Camera API

- **`tests/test_cameras_api.py`** — `test_cameras_get_returns_json` mocks `enumerate_cameras` (CI-safe).
- **`test_enumerate_cameras_runs_on_local_host`** is marked **`requires_hardware`** (skipped in CI).

## Web operator (`web_sota`)

| Layer | Tool | Scope |
|-------|------|--------|
| Unit | **Vitest** | `src/**/*.test.ts` (e.g. `toolResult` parser) |
| Browser e2e | **Playwright** | DOM for dashboard, `/targets`, HITL bar; hits live API via Vite proxy |
| Native GUI | **pytest `-m e2e`** | LibreOffice / pywinauto loop (existing) |

### Commands

```powershell
cd web_sota
npm install
npm run test              # Vitest
npm run build             # required before e2e preview
npm run test:e2e:install  # Chromium for Playwright
npm run test:e2e          # starts backend + vite preview (10788/10789)
```

Playwright config: `web_sota/playwright.config.ts`. Stack launcher: `web_sota/scripts/start-e2e-stack.ps1`.

**Do not** conflate Playwright (browser operator UI) with pytest LibreOffice e2e (native Windows automation).

## Desktop (Tauri)

Sidecar + installer build: `docs/DESKTOP_APP.md`.

```powershell
cd web_sota
npm run sidecar:build
npm run tauri:build
```

## CUA-NSIS smoke (installed app)

Tests the actual NSIS installer artifact — catches backend unreachable, CSP/CORS, wrong paths, and orphan processes.

`powershell
just build-native
just cua-nsis-test
`

The smoke script (scripts/cua-smoke.py) runs 9 phases: kill → install → launch → window verify → screenshot → feature route → diagnostics → WebView bridge OCR → uninstall.

All phases are non-fatal except install, launch, and WebView bridge (release gate). The config file scripts/cua-nsis-config.json enables fleet reuse.

See docs/ASSESSMENT_BY_CURSOR_2026-06-14_CUA_NSIS.md for full gap analysis.

