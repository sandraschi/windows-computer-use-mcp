
# Changelog

All notable changes to Windows Computer Use will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] — 2026-06-15

### Added

- **Phase 1: Autonomous mission engine** — `automation_mission(run=...)` decomposes natural-language goals via LLM sampling, executes each step with retry + outcome verification, returns per-step pass/fail with evidence.
- **Phase 1: Outcome verification** — `automation_elements(click, verify=True)` and `(set_text, verify=True)` check post-conditions (text appeared, element state changed) inline. Verification failure returns `status=blocked` with detail.
- **Phase 1: Unified retry policy** — `RetryPolicy` with strategy chain: refocus → wait_stable → fallback_selector → escalate. Each strategy gets exponential backoff. Replaces ad-hoc retry logic.
- **Phase 2: Adaptive element location** — when element not found by title, cascades through auto_id → control_id → class+type → OCR region scan.
- **Phase 2: Telemetry store** — SQLite-backed action log at `~/.windows-computer-use-mcp/telemetry.db`. Every element interaction logged with tool, strategy, success, duration. Query with `automation_system(telemetry=True)`.
- **Phase 3: Macro recording** — `automation_macro(record)` → run tools → `stop()` → `replay()` / `replay_with_verify()`. Saved as JSONL in `~/.cua-mcp/macros/`.
- **Phase 3: Multi-app workflow** — `automation_mission(workflow=True, app="notepad.exe", actions=[...])`. Chains steps across apps with timeout.
- **Phase 4: Smart discovery** — `automation_smart(discover)` scans all visible windows, identifies apps by class/process signatures. `automation_smart(click="the Save button")` finds elements by intent across all windows with LLM disambiguation.
- **Phase 5: Self-healing missions** — mission engine checks window alive before each step, re-launches app if dead, aborts after 5 consecutive failures.
- **Phase 5: Cross-app data flow** — steps with `store_as` save results to shared context; `$ref:key` in params reads from context.
- **Phase 5: Event-driven watchers** — `automation_watch(start, condition="window_appears")` with background thread polling. Four conditions: window_appears, window_closes, text_appears, element_appears.
- **Phase 6: Telemetry-driven strategy** — mission engine queries `get_best_strategy()` from telemetry before each step, prefers historically successful approach.
- **Phase 6: Agent instructions** — CLAUDE.md, AGENTS.md, SKILL.md all updated with full 18-tool surface and usage patterns.
- **Tesseract auto-install** — `scripts/install-tesseract.ps1` downloads UB-Mannheim Tesseract 5.x silently. Bundled in NSIS installer as optional checkbox. `just install-tesseract` for dev.
- **`just smoke`** — quick smoke test verifying all tools import and register.
- **Playwright e2e tests** — 5 spec files covering dashboard (KPIs, host metrics), navigation (all 10 routes via sidebar), REST API (health, diagnostics, system info, 404), and crawler page (form, reports tab). `just e2e` to run.

### Changed

- README slimmed to fleet standard: hero + TOC + 4-method quick-start table + sub-readme nav. Includes cross-ref to browser-mcp.
- `docs/TOOLS.md` rewritten with all 22 tools, phase annotations, and examples.
- `docs/README.md` hub linked to py-stack.md and composing-with-playwright.md.
- `docs/py-stack.md` updated with Tesseract auto-install instructions.
- `docs/composing-with-playwright.md` added — patterns and config for running both MCPs side by side.
- `docs/cua-nsis-certification.md` — documents the 12-phase dogfooding certification flow with config reference and tool mapping.

## [0.6.0] — 2026-06-15

### Added

- **Repo renamed: `pywinauto-mcp` → `windows-computer-use-mcp`** — GitHub redirects old URL, all docs and cross-refs updated across fleet.
- **`docs/py-stack.md`** — dedicated Python dependency breakdown doc.
- **`web_sota/README.md`** — operator UI build/dev guide.
- **`analyze_winapp` tool** — auto-crawl Windows apps: walk UI tree, SOM annotated screenshot, element map with coordinates/types/names, markdown report. Three operations: `crawl` (full tree), `discover` (shortcut probe), `portfolio` (named state captures).
- **`CuaHUD` module** — always-on-top "CUA at work" blinking red overlay with emergency stop button. Used by `analyze_winapp` (all operations) and `global_keylogger` (start/stop). Target window auto-refocused before each action to prevent focus stealers.
- **Crawler webapp page** — new `/crawler` route with three tabs: Start Crawl (target + options form), Reports (history from localStorage), Tree Viewer (collapsible element tree grouped by type + full-screen screenshot modal).
- **Cross-connection docs** — README fleet/siblings table updated with "when to use" guidance vs `autohotkey-mcp`. Both repos now cross-reference each other.

### Changed

- **`get_window_state` / `automation_visual` / `automation_assert`** — fixed "tile cannot extend outside image" error by adding `virtual_screen_bounds()` + `clamp_bbox()` helpers. Window rects extending off-screen are now clamped to the virtual screen bounds before `PIL.ImageGrab.grab()` calls.
- **`global_keylogger`** — shows CUA HUD while active; `status` response includes `hud_active` field.
- **`win32_window.py`** — added `virtual_screen_bounds()`, `clamp_bbox()`, updated `grab_window_image()`.
- **`annotator.py`** — `capture_and_annotate()` clamps bbox + try/except fallback; `_draw_element()` clamps label y-coords to ≥0.
- **`assert_engine.py`** — `capture_image()` clamps bbox before `ImageGrab.grab()`.

## [0.5.4] - 2026-06-08

### Added

- **Tauri desktop 0.5.4**: Production shell on port 10789 with sidecar backend spawn and fleet-standard CORS/API config.

### Changed
- **Documentation (fleet standard):** Root **README** shortened with TOC and sub-readme tables; hero positions the project as a Windows **computer use agent**. Added **docs/ARCHITECTURE.md**, **docs/TOOLS.md**. Refreshed **docs/README.md**, **docs/PRD.md** (CUA tools, v0.5.x), **mcpb/README.md**, **mcpb/manifest.json** (v0.5.4).
- **MCPB build:** `scripts/build-mcpb-package.ps1` syncs `src/windows_computer_use_mcp` into `mcpb/` and packs `dist/windows-computer-use-mcp.mcpb`; **`just mcpb-pack`** recipe added.

### Removed
- **Legacy DXT docs** under `mcpb/`: `DXT_BUILDING_GUIDE.md`, `DXT_PACKAGING_ISSUES.md`, `DXT_README.md` (superseded by MCPB — see `docs/mcpb-packaging/`).

### Fixed
- **Web orchestration (`start.ps1`)**: Root and **`web_sota/start.ps1`** now wait until the API port accepts connections (or **`/api/v1/health`** on pywinauto) before starting Vite, set **`WorkingDirectory`** correctly for the uvicorn child, and resolve **`$RepoRoot`** without overwriting **`$PSScriptRoot`** — avoids Vite proxy **`ECONNREFUSED`** during slow `uv run` / first import. Root script uses **`Join-Path`** for **`web_sota`** so it works when the shell cwd is not the repo root.

## [0.4.2] - 2026-04-10

### Added
- **`win32_mouse` module** (`src/windows_computer_use_mcp/win32_mouse.py`): DPI-aware **`SetCursorPos`** + **`mouse_event`** for pointer injection. **`automation_mouse`** and coordinate-based paths in **`automation_elements`** use this backend instead of PyAutoGUI alone (reliable move / click / drag / scroll on scaled displays). Responses include `input_backend: "win32_mouse"` where applicable.
- **`global_keylogger`** portmanteau tool (opt-in): set **`WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER=1`** to register; see **`docs/SAFETY.md` §6**. Shutdown stops the listener; **`gate_invasive_monitoring()`** applies kill-switch / dry-run without burning the mutation rate limiter.
- **Documentation:** **`docs/SAFETY.md`** — dual-use tooling (research / forensics / guardrails) and global keylogger §6; root **README** links.
- **Examples:** `examples/demo_mouse_dance.py`, `examples/demo_notepad_grid.py`, `examples/demo_notepad_typewriter.py`, `examples/demo_notepad_helpers.py`, **`examples/README.md`**. **`just demo`** recipe (justfile) runs the three Python demos in sequence (requires [just](https://github.com/casey/just) on `PATH`).

### Fixed
- **`demo_notepad_grid`:** tile windows with Win32 **`MoveWindow`** (and close via **`PostMessage` `WM_CLOSE`**) so **cmd.exe** consoles position correctly; UIA **`move_window`** was not wrapping those HWNDs.

### Changed
- **Failsafe** for injected pointer ops: upper-left corner only (aligned with PyAutoGUI); **`WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1`** disables it for **`win32_mouse`** as for PyAutoGUI.

## [0.4.1] - 2026-04-10

### Added
- **Justfile Demo Orchestration**: Replaced external `.py` scripts for the MS Paint demo with a native PowerShell/CLI orchestration in the `justfile` (`just paint-demo`).
- **HITL Bypass Hardening**: Added `WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL` support to disable `pyautogui.FAILSAFE` at runtime, ensuring reliable automated demos in non-interactive environments.
- **API Alias**: Standardized `automation_windows` to accept `window_handle` as an alias for `handle`, ensuring 100% consistency across all portmanteau tools.
- **Biometrics → `automation_face`:** Web UI calls **`POST /api/v1/tools/call`** for **list / capture & match / delete** when the tool is registered (`web_sota` helper `lib/mcpTools.ts`).
- **REST `GET /api/v1/safety/status`:** Same payload as MCP **`automation_safety("status")`** (webapp biometrics).
- **ASGI composite server:** FastAPI **`/api/v1/*`** (REST) + FastMCP HTTP **`/mcp`** — `windows_computer_use_mcp.server:app` for uvicorn; CORS for `web_sota`.
- **web_sota `/chat` — local LLM:** OpenAI-compatible proxy (`/api/v1/llm/*`) to **Ollama** / **LM Studio** on localhost only (SSRF-safe localhost); model list, **personas**, **prompt refiner**, optional **repo knowledge** from `llm_repo_context.py`. Env: **`PYWINAUTO_LLM_BASE_URL`**.
- **Camera enumeration:** `GET /api/v1/cameras/` probes OpenCV indices; **Biometrics** + **Tools** (`camera_index` for `automation_face`) show a **dropdown when multiple cameras** exist; `localStorage` sync. Env: **`WINDOWS_COMPUTER_USE_MCP_CAMERA_MAX_INDEX`** (default 10).
- **Environment-aware pytest** (aligned with **mcp-central-docs** `testing-environment-aware.md`): `tests/conftest_env.py`, markers (`requires_hardware`, `destructive`, …), **`docs/TESTING.md`** (fleet context), **`[tool.pytest.ini_options]`**; **`tests/test_cameras_api.py`**; real-window class marked for CI skip.
- **Visual Telemetry HUD**: Implemented a high-visibility, "Always-on-Top" overlay for real-time coordinate tracking and input verification, replacing covert logging with a transparent, non-persistent diagnostic tool.
- **Docs:** **`docs/PRD.md`** refreshed (web stack, REST, LLM, testing); **`docs/README.md`** index; **`docs/TESTING.md`**; **`docs/LLM_REPO_CONTEXT.md`** pointer; camera notes in **`docs/SAFETY.md`** §5.

### Changed
- **`web_sota`:** Removed legacy **robotics teleop** (`/control`) and **Unity/3D placeholder** (`/visualizer`). **Biometrics** now has a **live browser webcam preview** (2D pan/zoom/rotate) plus **live safety** from **`/api/v1/safety/status`**. Fleet catalog entry **robotics-mcp** clarified (not this server).
- **`automation_face` is opt-in at runtime:** set **`WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1`** and install the **`face`** extra; otherwise the tool is not registered. **`automation_safety(status)`** reports **`face_tool_opt_in`**. Docs: **`docs/SAFETY.md` §5** (wording tightened; no “creepware” framing).
- **README / help:** Marketing tone reduced; **`automation_system("help")`** returns structured docs (version, safety env, prompts, tool list). **`web_sota`** adds **`/help`** page; dashboard badges no longer show fake telemetry.

### Changed (tooling)
- **`automation_system`:** `Literal` aligned with implemented operations (`help` added; removed non-existent `screenshot` / `terminal` entries).

## [0.3.2] - 2026-03-21

### Changed
- **Discovery (Glama / PyPI):** `glama.json` and `pyproject.toml` package description lead with **safety** and **`virtualization-mcp`** for Sandbox/VM isolation; metadata aligned (version **0.3.2**, **FastMCP 3.1+**, `safety_and_isolation` feature block, keywords).
- **README:** Added **Discovery** subsection — stars reflect distribution, not safety; link to fleet isolation server.

## [0.3.1] - 2026-01-25

### Fixed
- **Docstring Refactoring**: Fixed missing blank lines after sections (D413) across all 8 portmanteau tools.
- **SOTA 2026 Alignment**: Standardized documentation to Jan 2026 industrial SOTA patterns.

### Added
- **Formal PRD**: Created `docs/PRD.md` to define project requirements and technical standards.
- **Improved Grounding**: Enhanced tool documentation for better AI agent navigation.

## [0.3.0] - 2025-10-08

### Added
- Comprehensive DXT manifest with 22+ automation tools
- Extensive prompt templates for conversational AI interaction
- GitHub Actions CI/CD pipeline with automated testing
- Issue and pull request templates for better contributions
- Contributing guidelines and development documentation

### Changed
- Reorganized repository structure with dedicated `dxt/` directory
- Updated pywin32 dependency to version 311
- Enhanced package metadata and descriptions

## [0.2.0] - 2025-01-23

### Added
- **Complete DXT Package**: Comprehensive Windows UI automation with face recognition
- **22 Automation Tools**: Window management, element interaction, OCR, mouse/keyboard control
- **Dual Interface Architecture**: MCP tools + REST API with feature parity
- **Face Recognition Security**: Webcam authentication and intruder detection
- **OCR Integration**: Text extraction from windows and images
- **Advanced Element Interaction**: Click, type, hover, and drag operations

### Changed
- Major architecture overhaul with modular plugin system
- Enhanced error handling and retry mechanisms
- Improved configuration management

## [0.1.0] - 2025-07-30

### Added
- Initial Windows Computer Use server implementation
- Basic window management tools
- Face recognition API endpoints
- Security monitoring features
- DXT packaging support

### Changed
- Initial release with core automation functionality

---

## 📊 Version Information

- **Current Version**: 0.4.2
- **Python Support**: 3.10, 3.11, 3.12
- **Platform**: Windows 10/11
- **License**: MIT

## 🔄 Release Process

Releases are automated through GitHub Actions:
1. Push to `master` branch triggers CI
2. Tests run on Windows with multiple Python versions
3. DXT package is built and uploaded as artifact
4. Release creation triggers final package distribution

## 🤝 Contributing to Changelog

When contributing to this project, please:
- Add entries to the "Unreleased" section above
- Use present tense for changes ("Add feature" not "Added feature")
- Group changes under appropriate headings (Added, Changed, Fixed, etc.)
- Reference issue numbers when applicable

---

*For more detailed information about each release, see the [GitHub Releases](https://github.com/yourusername/windows-computer-use-mcp/releases) page.*



