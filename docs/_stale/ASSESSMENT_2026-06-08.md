# windows-computer-use-mcp / cua-mcp — Assessment & TODO
**Date:** 2026-06-08 (rev 2 — full source audit)
**Version assessed:** 0.5.3
**Supersedes:** rev 1 (same day, incomplete)
**Operator console spec:** [TARGETS_PAGE_SKETCH.md](TARGETS_PAGE_SKETCH.md) (W1)

---

## Reconciliation (Cursor, 2026-06-08)

Items verified against running fleet + commits through `07d5358`:

| ID | Original claim | Reconciled status |
|----|----------------|-------------------|
| Bug 1 | Version drift in `app.py` | **Fixed** — `app.py` reads `importlib.metadata.version("windows-computer-use-mcp")` |
| Bug 2 | Portmanteau tools not registered | **Closed — false alarm** — `main.py` imports `windows_computer_use_mcp.tools`; `tools/__init__.py` loads `portmanteau_assert`, `portmanteau_task`, etc. HTTP smoke: `automation_task`, `automation_windows` work |
| Bug 4 | VRoid region hardcoded 1920×1080 | **Partial** — `RegionMask` in `app_profiles.py` + `task_engine._step_region`; still needs F2 auto-calibration on 4K/DPI |
| Bug 5 | No template PNGs | **Partial** — manifest + 32×32 placeholders committed; **production captures still required** (F1) |
| T2.3 / T2.4 | Template library + region masks | **Done** v0.5.3 |
| T2.2 | Snapshot invalidation after mutation | **Done** v0.5.2 |
| W1 | Targets operator console | **Spec ready** — see [TARGETS_PAGE_SKETCH.md](TARGETS_PAGE_SKETCH.md); implementation = T3.4 |
| — | `automation_windows find` slow/hang | **Fixed** — pygetwindow fast path in `portmanteau_windows.py` |

**Still open (confirmed):** Bug 3 (`mission.plan` non-sampling fallback), Bug 7 (`mission.status` stub), F1 real template capture, F2 region calibration, F4 evidence base64, `type_text` step kind (noted in TARGETS sketch).

---

## What This Actually Is

After reading the full source: this is a real, production-grade Windows CUA (Computer Use Agent) substrate, not a GUI automation helper. The layering is complete:

```
automation_task         ← closed-loop step runner with evidence, retry, refocus
  → shortcut_engine     ← per-app shortcut registry (VRoid, more to add)
  → dialog_engine       ← save/open/export dialog driver
  → assert_engine       ← dhash/wait_stable/diff/template/OCR assertions
  → snapshot_store      ← per-window element snapshots, auto-invalidated after mutations
  → trajectory.py       ← JSONL session log (CUA parity Phase 3)
  → mission_store.py    ← JSONL record/replay per mission_id
  → app_profiles.py     ← per-app dispatch policy + stable_region
  → template_library.py ← per-app PNG template registry (manifest.yaml)
  → agent_overlay.py    ← virtual cursor marker
  → win32_mouse.py      ← DPI-aware SetCursorPos + mouse_event
  → win32_keyboard.py   ← HWND-targeted SendInput (no global PyAutoGUI)
  → win32_window.py     ← PostMessage click, bbox grab, MoveWindow
```

`task_engine.run_task()` is the MVP. It does: per-step before/after screenshots, retry with configurable `on_fail` policy (`retry` / `refocus_retry` / `abort`), optional steps, snapshot invalidation after mutations, and assembles a full evidence bundle. `automation_task` exposes this as an MCP tool.

The CUA parity phases 1–4 are genuinely done. Phase 6 (rename) is 60% done (`cua_env.py` transition shim live). Phases 7–9 are partial.

---

## Issues & TODO

### Critical

**1. ~~Version drift~~ → FIXED (reconciliation).** `server.py` FastAPI title version may still lag — align on next touch.

**2. ~~Tools not registered~~ → CLOSED (false alarm).** Verified via `POST /api/v1/tools/call` for `automation_task`, `automation_windows`. Registration path: `main.py` → `import tools` → `tools/__init__.py` portmanteau imports.

**3. `automation_mission.plan` operation requires FastMCP sampling context — it returns an error if the host doesn't support it.**
The error message is clear but the fallback is useless ("fall back to manual tool chaining"). A non-sampling `plan` that just decomposes a goal into a static step template would be far more useful. The sampling path is a bonus, not the primary.

### High Priority

**4. `app_profiles.py` VRoid stable region is hardcoded to `(280, 120, 1640, 980)` — assumes 1920×1080.**
On Goliath with a 4K display or custom DPI scaling this is wrong, and wrong region masks are worse than no mask (they hash the wrong area). The profile needs either a resolution-relative ratio or a runtime calibration step that measures the VRoid editor canvas bounds from a fresh screenshot.

**5. Template library has placeholders only — production captures still required.**
`manifest.yaml` + 32×32 placeholders exist (smoke/CI). **Do not treat `assert_template` as production-ready until F1 captures** at your calibrated resolution: `export_dialog_title`, `sample_picker_grid`, `save_confirm_dialog`, `f8_export_button_active`.

**6. `shortcut_engine.py` exists and is called by `task_engine.py` but the module has not been read yet — confirm it has the VRoid shortcut registry and `send_shortcut()` with `verify_stable` support.**
If `shortcut_engine` only wraps `automation_keyboard(hotkey)` without the per-app expect-state verification, vroidstudio-mcp's `VROID_USE_CUA_SHORTCUT=1` path buys nothing over raw keyboard.

**7. `automation_mission.status` operation returns hardcoded `"progress": 50, "status": "active"` regardless of actual state.**
This is a stub. Real status should read from `mission_store.get_steps()` and report step count, last timestamp, last step kind. Agents querying status to decide whether to wait or intervene get garbage.

**8. README tool table lists 8 tools but source has at least 12 registered (automation_assert, automation_task, automation_mission, automation_shortcut, automation_dialog, get_window_state, cua_computer_use_screenshot, approve_automation, automation_safety — plus 8 portmanteau). Update README.**

**9. `src/windows_computer_use_mcp/main.bak` in source tree. Delete.**

**10. `coverage.xml`, `htmlcov/`, `ruff_stats*.txt`, `paint_elements.json`, `windows-computer-use-mcp.log` committed to repo root. Gitignore and clean.**

### Medium Priority

**11. `task_engine._resolve_hwnd()` uses `pygetwindow` to find windows by title — this races with pywinauto's own window-find. Should use `automation_windows(find)` logic from `win32_window.py` for consistency.**

**12. `automation_task` is synchronous (`def automation_task`) but calls `shortcut_engine`, `dialog_engine`, and `assert_engine` which may block for seconds (wait_stable timeout up to 30s). Should be `async def` with `asyncio.get_event_loop().run_in_executor()` wrapping the blocking engine calls, or the entire task_engine should be async.**

**13. `mission_store.py` writes JSONL with `ts` field set in `record_step()` but the `step` dict passed in may already contain a `ts` key from the caller, causing duplicate/overwritten timestamps. Normalize.**

**14. `trajectory.py` ENV var is `WINDOWS_COMPUTER_USE_MCP_TRAJECTORY_LOG` but `cua_env.py` transition shim is not used — it should use `cua_truthy("CUA_MCP_TRAJECTORY_LOG", "WINDOWS_COMPUTER_USE_MCP_TRAJECTORY_LOG")`.**

**15. `automation_task` docstring says "VRoid export: shortcut steps + dialog + assert_file in one call" — this is the most valuable feature, yet there are no worked examples in `examples/` or `docs/`. Add one.**

**16. `web_sota/` has two `.bak` files from 2026-05-08. Remove. `start.bat` at repo root and `web_sota/start.bat` — consolidate.**

**17. `docs/CUA_ASSISTANT_TODO.md` exists but was not read — it may contain more planned items that should be folded into this assessment.**

### Low Priority

**18. `approval_state` in `app.py` is module-level global — it doesn't survive server restart, which is by design, but there's no warning in `automation_safety(status)` that HITL approval is always cleared on restart. Document.**

**19. `cua_computer_use_screenshot` compat alias — confirm it returns `screenshot_base64` in the field Claude's computer-use loop expects.**

**20. CHANGELOG `[Unreleased]` should become `[0.5.3]` with today's date.**

---

## Feature Suggestions for Cursor

These are concrete next builds, roughly ordered by payoff. vroidstudio is called out explicitly where it is the primary test subject.

### F1 — VRoid Template Capture Workflow (1 day)
**The single highest-value thing missing.** `assert_template` is wired but has no real templates.

Add `automation_task` operation `capture_templates` or a standalone `automation_visual(capture_template)` that:
1. Takes a screenshot of the target window
2. Lets the agent specify a bounding box (x, y, w, h) by name
3. Saves the crop to `templates/{app}/{version}/{name}.png`
4. Updates `manifest.yaml` with threshold and region_hint

Without real templates, all the `assert_template` machinery in the task runner is inert for VRoid. With 6–8 templates (export dialog title, sample picker grid, save confirm, F8 active, editor canvas with hair/face/body/outfit selected), VRoid export becomes genuinely verifiable.

### F2 — Stable Region Auto-Calibration (1 day)
**Kills the hardcoded `(280, 120, 1640, 980)` problem.**

`automation_task` step kind `calibrate_region` (or `app_profiles` operation `calibrate`):
1. Takes a baseline screenshot of the target app
2. Optionally prompts the agent with the screenshot for the host LLM to identify the editor canvas bounds
3. Or: uses a simple heuristic — find the largest non-chrome rectangular area by color variance
4. Stores the result in `~/.cua-mcp/profiles/{app_id}_region.json`
5. `get_profile()` merges this over the hardcoded defaults

This makes `automation_assert(wait_stable)` resolution-independent.

### F3 — VRoid Full Export Task Template (half day)
**The killer demo that proves the whole stack.**

A pre-built `automation_task` step list for the canonical VRoid export flow, exposed as:
- `automation_task(operation="run", app="vroidstudio", steps=VROID_EXPORT_TEMPLATE, output_dir=...)`
- Or `automation_task(operation="list_templates", app="vroidstudio")` returning it by name

Steps: `preflight` → `focus` → `shortcut:new_project` → `wait_stable` → `shortcut:select_sample` → `click:sample_tile` → `wait_stable` → `shortcut:export_vrm(F8)` → `dialog:save_path` → `wait_stable` → `assert_file` → `screenshot`

This replaces vroidstudio-mcp's YAML archetypes with a direct `automation_task` call and proves cua-mcp can drive VRoid without the vroidstudio-mcp layer — which is the natural end state of the CUA evolution.

### F4 — Evidence Bundle Return Type (half day)
**Makes failure debugging from MCP clients practical.**

When any `automation_task` step fails, the current evidence dict has paths to screenshots but no base64. An agent in Claude Desktop or Cursor can't see a file path — it needs inline base64 to show the before/after to the host LLM for recovery advice.

Add `include_screenshots_b64: bool = False` to `TaskOperationRequest`. When true, read each evidence screenshot and embed as base64 in the returned `ToolResult.data`. Cap at 3 images to keep response size sane.

Combined with the host LLM analyzing the images, this gives real self-healing: agent sees the diff, decides whether to retry with different params or abort.

### F5 — `automation_mission.plan` Non-Sampling Fallback (half day)
**Makes plan useful when not running in a sampling-capable host.**

Replace the current "sampling not available" error with a template decomposer:
- Parse the `goal` string for known app names and action verbs
- Return a static step list based on app profile templates
- E.g. `goal="export VRoid character to VRM"` → returns the standard VRoid export step list
- The sampling path remains available as a richer alternative

### F6 — Multi-Match `find_image` (1 day)
**Needed for VRoid sample picker and preset grids.**

Currently `find_image` returns the single best match. VRoid's sample model picker is a grid of thumbnails — the agent needs to find all matches above a threshold and click the Nth one by position. Add `find_all: bool` and `max_results: int` to `automation_visual(find_image)`.

This also unlocks grid navigation patterns (Office toolbars, icon grids) that are currently impossible to drive reliably.

### F7 — App Profile Hot-Reload + CLI (half day)
**Makes calibration persistent without code changes.**

`automation_task(operation="list_profiles")` works, but profiles are hardcoded in `app_profiles.py`. Add:
- `~/.cua-mcp/profiles/*.yaml` override directory read at startup and on `reload`
- `automation_task(operation="reload_profiles")` tool operation
- `windows-computer-use-mcp profile add --app vroidstudio --stable-region 280,120,1640,980` CLI subcommand

Pairs with F2 (auto-calibration writes to the override dir).

### F8 — `automation_task` Async + Streaming Progress (1-2 days)
**Makes long VRoid tasks observable in real time.**

Currently `automation_task` is synchronous and blocks until all steps complete or fail. For a 15-step VRoid export that takes 45 seconds, the MCP client sees nothing for 45 seconds then gets a result.

Refactor `task_engine.run_task()` to async, use `ctx.report_progress()` per step (FastMCP 3.2 sampling context), and optionally stream intermediate evidence via `ctx.info()`. The `automation_mission(plan)` already uses `ctx.report_progress()` — same pattern.

### F9 — VRoid Preset Click Grid Mapping (1 day)
**Eliminates the last hardcoded click coordinates.**

vroidstudio-mcp currently hardcodes `VROID_SAMPLE_MODEL_X/Y` for the sample picker. The proper fix: capture the sample picker region as a template, use `find_all` (F6 above) to locate all visible thumbnails, sort by position, click the Nth. This makes sample selection resolution-independent and works after VRoid UI updates.

Implement as a `shortcut_engine` operation `select_nth_preset(n, app="vroidstudio")` that uses template matching instead of hardcoded coordinates.

### F10 — Rename Completion: `cua-mcp` (1 day)
**The rename is 60% done. Finish it.**

Remaining steps:
1. Module rename `windows_computer_use_mcp` → `cua_mcp` (breaking — requires vroidstudio-mcp update)
2. All env vars use `cua_truthy`/`cua_getenv` (trajectory.py still uses raw `os.getenv`)
3. PyPI: publish `cua-mcp`, keep `windows-computer-use-mcp` as deprecated wrapper
4. Fleet: update vroidstudio-mcp imports, mcd port table, claude_desktop_config.json
5. Bump `app = FastMCP(name="cua-mcp", version=...)` in app.py

Pre-condition: F-bug #2 (tool registration) must be fixed first, otherwise the rename ships broken tools.

---

## Priority Matrix

| # | Item | Sev | Effort |
|---|------|-----|--------|
| Bug 1 | Version hardcoded in app.py | Critical | 15 min |
| Bug 2 | New tools never imported/registered | Critical | 1h |
| Bug 3 | mission.status stub | High | 1h |
| Bug 4 | VRoid stable region hardcoded | High | → F2 |
| Bug 5 | No real VRoid templates | High | → F1 |
| Bug 6 | shortcut_engine audit | High | 30 min |
| Bug 7-10 | Housekeeping (gitignore, bak files) | Medium | 1h |
| F1 | VRoid template capture | High | 1 day |
| F2 | Stable region calibration | High | 1 day |
| F3 | VRoid full export task template | High | 0.5 day |
| F4 | Evidence bundle base64 | Medium | 0.5 day |
| F5 | mission.plan non-sampling fallback | Medium | 0.5 day |
| F6 | Multi-match find_image | Medium | 1 day |
| F7 | Profile hot-reload + CLI | Medium | 0.5 day |
| F8 | async task + streaming progress | Low | 1-2 days |
| F9 | VRoid preset grid mapping | Low | 1 day |
| F10 | Rename completion | Low | 1 day |
| W1 | Targets page (operator console) | Medium | 2-3 days |

**Immediate unblock order: F1 (real templates) → F2 (region cal) → F3 (export task demo) → W1 (Targets page per [TARGETS_PAGE_SKETCH.md](TARGETS_PAGE_SKETCH.md))**. Core wiring is live; remaining gaps are calibration + operator UX.

---

### W1 — Targets Page: CUA Operator Console (2-3 days)
**Transforms web_sota from a debug tool into a real operator surface.**

The current webapp has a generic MCP Tools Hub (JSON form-fill for any tool) and a dashboard showing host metrics. Neither is useful during an active automation run. The Targets page gives the human operator a purpose-built console: one page per automation target, each with target-specific quick actions, a live step runner, and an evidence trail.

**Route:** `/targets` — new sidebar entry between Tools and Help.

**Design:** single page, horizontal tab strip at the top, one tab per target. Tab state is local (selected tab persists in `localStorage`). Shared state across all tabs: HITL approval status (polled from `automation_safety(status)`), last known window handles.

**Persistent HITL strip** across the top of the page (not buried in Help):
- Green/amber/red pill: Approved until HH:MM / Expired / Bypassed
- "Approve 5 min" button → calls `approve_automation(duration_minutes=5)`
- Countdown timer ticking down in real time
- Kill switch indicator badge

**Tab anatomy** — every target tab has the same four zones:

```
┌─ App Status ──────────────────────────────────────────────┐
│  [window title]  HWND: 14782  dispatch: foreground  [Find] │
└────────────────────────────────────────────────────────────┘
┌─ Quick Actions ────────────────────────────────────────────┐
│  [Launch]  [Focus]  [Screenshot]  [target-specific buttons] │
└────────────────────────────────────────────────────────────┘
┌─ Step Runner ──────────────────────────────────────────────┐
│  Template: [dropdown]   or  [Edit steps JSON]              │
│  Output dir: [input]         [▶ Run]  [✕ Cancel]           │
│  ── live progress ──────────────────────────── step 3/7 ── │
└────────────────────────────────────────────────────────────┘
┌─ Evidence ─────────────────────────────────────────────────┐
│  [before]  [after]  diff: 4.2%  step: shortcut:export_vrm  │
│  OCR: "Export as VRM"  status: ✓ success                   │
└────────────────────────────────────────────────────────────┘
```

**Tabs:**

*Notepad* — "does the CUA stack work at all" canary. Quick actions: Launch, Find window, Type text (inline input), Ctrl+S, Close. One template: `notepad_type_and_save`. If this tab can't type into Notepad, nothing else matters. Deliberately kept to ~4 quick actions with no complexity.

*LibreOffice Calc* — background dispatch target. Quick actions: Open file (path picker), Set cell (A1 + value inputs → UIA element + type step), Save, Export PDF. Template: `calc_set_and_save`. Shows background UIA path working without foreground. The "dispatch: background" badge should be green here (unlike VRoid where it's always foreground).

*VRoid Studio* — the hard target and flagship. Quick actions: Launch, Focus, New Project, Screenshot, Export VRM. Template dropdown populated from `automation_task(list_templates, app="vroidstudio")` — all 55 archetypes if vroidstudio-mcp is available, or cua-mcp's built-in VRoid templates. Evidence panel shows before/after export screenshot. **Stable region visualizer**: overlay the `(280,120,1640,980)` bounding box on the last screenshot as a semi-transparent rect — makes miscalibration immediately visible. Step progress shows current archetype step name and index.

*KiCad* — forward-looking EDA target. Quick actions: Open project (path), Run DRC, Export Gerbers, Export BOM. Template: `kicad_open_and_export_gerbers`. App profile: `dispatch=foreground`, `keyboard_backend=win32`. Demonstrates the pattern for any new EDA app (LTspice, Altium, etc.) — adding a new tab is just adding an `AppProfile` entry and a tab config object.

*Custom* — escape hatch + learning tool. App selector dropdown (`list_profiles()` result). Raw JSON textarea for steps array pre-filled with a working example. Output dir input. Run/Cancel. Results console. This is where you build a new target before it gets its own tab.

**Implementation notes for Cursor:**

- New file: `web_sota/src/pages/targets.tsx` — the page shell with tab strip and HITL bar
- New file: `web_sota/src/pages/targets/` directory with `notepad.tsx`, `libreoffice.tsx`, `vroid.tsx`, `kicad.tsx`, `custom.tsx`
- New file: `web_sota/src/hooks/useTaskRunner.ts` — shared hook wrapping `callMcpTool("automation_task", ...)` with polling for task status, progress state, and evidence accumulation
- New file: `web_sota/src/hooks/useHitl.ts` — polls `automation_safety(status)` every 10s, exposes `{ approved, expiresAt, approve, killSwitchActive }`
- New file: `web_sota/src/hooks/useWindowFind.ts` — wraps `automation_windows(find, title=...)`, returns `{ handle, found, refresh }`
- Extend `App.tsx`: add `<Route path="/targets" element={<Targets />} />`
- Extend sidebar: add Targets entry with a `Target` or `Crosshair` lucide icon
- The evidence panel reads screenshot paths from task session `evidence[]` and loads them via `/api/v1/download/{filename}` — this endpoint already exists in the backend

**What this is not:** not a second MCP client. The page fires `automation_task` calls over the REST bridge exactly like the Tools Hub does today, just with pre-built arguments and a purpose-built display. No new backend endpoints required beyond what already exists — except polling for task session status, which needs `GET /api/v1/tasks/{task_id}` or a `automation_task(status, task_id=...)` call on a timer.

**Prerequisite:** cua-mcp Bug 2 (tool registration) must be fixed before this page has anything real to call. Build the page against mock responses first if Bug 2 isn't fixed yet — the `useTaskRunner` hook can have a `MOCK_MODE` flag.

See `docs/TARGETS_PAGE_SKETCH.md` for full component structure and annotated code.

---

## Architecture Health

The design is sound. `task_engine` is the right abstraction — closed-loop, evidence-collecting, app-profile-aware. `assert_engine` + `snapshot_store` + `template_library` is a coherent vision stack. The CUA parity loop (`get_window_state` → `automation_elements(snapshot_id, element_index)` → `automation_assert(wait_stable)`) is exactly right.

The main structural risk is that the impressive architecture is partially disconnected — tools defined but not registered (Bug 2), templates declared but not captured (Bug 5), profile regions hardcoded (Bug 4). Fix the wiring first; the feature work will land on something that actually runs.
