# CUA-NSIS Certification

**Using windows-computer-use-mcp to test its own installer.** Dogfooding at its finest.

## The Problem

Every NSIS installer has a dozen failure modes that unit tests never catch:

- WebView2 runtime missing or outdated
- Backend spawns then immediately crashes (wrong port, missing `.exe`, cache path error)
- CORS misconfiguration blocks API calls from the Tauri WebView
- CSP headers reject the frontend's fetch requests
- Silent install succeeds but the app doesn't launch
- Uninstall leaves behind registry keys or cached files

Manual QA catches these — at \$2k and 3 days per round. Unit tests don't.

## The Solution

A 12-phase autonomous smoke test that installs the real NSIS build, launches it, verifies every layer, and reports pass/fail — all driven by the same tools the repo exposes.

## The 12-Phase Flow

| Phase | What it does | Tool used |
|-------|-------------|-----------|
| 1. Kill stale | `taskkill` leftover processes | `automation_system` |
| 2. Install | `setup.exe /S` silent | subprocess |
| 3. Launch | Start operator.exe, poll for HTTP 200 | `automation_system(start_app)` + health poll |
| 4. Window | Find window by title regex, maximize | `automation_windows(find)` + `(maximize)` |
| 5. Screenshot | Capture window as PNG evidence | `automation_visual(screenshot)` |
| 6. Feature route | Hit `/api/v1/system/info` | `httpx` GET |
| 7. Diagnostics | Hit `/api/v1/diagnostics` — tools, Tesseract, system | `httpx` GET |
| 8. WebView bridge | OCR the screenshot for "REST bridge reachable" | `automation_visual(extract_text)` |
| 9. Nav click-through | Click sidebar links via pywinauto, OCR each page header | `automation_elements(click)` + OCR |
| 10. Log analysis | Read app log file for errors/warnings | file read |
| 11. Uninstall | Run uninstaller, verify registry cleanup | subprocess |
| 12. Report | Write JSON + HTML cert report to mcp-central-docs | file write |

## The \$2 Stat

Used in production to build and validate **100 Tauri/NSIS Windows installers** in a single unattended run — install, test, screenshot, verify, report, iterate. **\$2 in DeepSeek API costs. Zero human intervention.**

The alternative: a QA contractor at \$2k per round. Same coverage, 1000× the cost.

## Run It

```powershell
# Build the installer first
just build-native

# Run certification
just cua-nsis-test
```

Or point at an existing installer:

```powershell
uv run python scripts/cua-smoke.py --installer path/to/setup.exe
```

## Configuration

The smoke test is config-driven via `scripts/cua-nsis-config.json`:

```json
{
  "product_name": "Windows Computer Use",
  "install_dir": "%LOCALAPPDATA%\\Windows Computer Use",
  "operator_exe": "windows-computer-use-operator.exe",
  "backend_port": 10789,
  "window_title_re": "Windows Computer Use",
  "nav_routes": [
    ["Dashboard", "Dashboard"],
    ["Logging", "Logging"],
    ["Settings", "Settings"],
    ["Help", "Help"]
  ]
}
```

Fleet repos use the same config template — swap the `product_name`, `install_dir`, and `window_title_re` to certify any Tauri-wrapped MCP server.

## Dogfooding Map

Every phase uses a tool this repo exposes. The certifier tests the same PyInstaller backend that the certifier depends on. If something breaks in the element-location cascade, the nav click-through phase catches it. If the REST API changes, the diagnostics phase catches it. If the WebView CORS config drifts, the OCR bridge proof catches it.

| Repo feature | Tested by phase |
|-------------|----------------|
| `automation_windows` | 4 (find, maximize) |
| `automation_visual` (screenshot) | 5, 8 |
| `automation_visual` (OCR) | 8 |
| `automation_elements` | 9 (nav click-through) |
| REST API (`/api/v1/*`) | 6, 7 |
| Backend startup + health | 3 |
| NSIS installer | 2, 11 |

## Fleet Standard

This pattern is codified as fleet standard at `mcp-central-docs/standards/rules/cua_nsis_smoke_testing.md`. Every Tauri-wrapped fleet repo must pass CUA-NSIS before release.

See also: `mcp-central-docs/patterns/CUA_DRIVER_AND_PYWINAUTO.md` for the Cua Driver parity comparison.
