# CUA-MCP Roadmap

Computer Use Agent MCP — Windows GUI automation with verification-first design.

Formerly `windows-computer-use-mcp`. Nobody knows what pywinauto is; this server is a **computer use agent** for Windows apps that lack an API.

---

## Rename decision

| Option | Pros | Cons |
|--------|------|------|
| **cua-mcp** (recommended) | Short; matches `cua_computer_use_screenshot`; aligns with industry "computer use" term | Acronym needs one-line expansion in README |
| computer-use-mcp | Self-explanatory | Long; awkward in fleet port tables |
| windows-computer-use-mcp (current) | Describes implementation detail | Sounds like a Python wrapper, not an agent |

**Decision:** Rename repo and display name to **cua-mcp**.

**Transition plan:**
1. v0.4.x: display name + docs say CUA-MCP; PyPI package stays `windows-computer-use-mcp`
2. v0.5.x: publish `cua-mcp` on PyPI; `windows-computer-use-mcp` becomes deprecated alias
3. v1.0.x: env vars `CUA_MCP_*` (fallback to `WINDOWS_COMPUTER_USE_MCP_*`); module `windows_computer_use_mcp` → `cua_mcp`

---

## Current state audit (v0.4.3)

### What exists today

| Category | Tools / modules |
|----------|-----------------|
| **Core portmanteau** | `automation_windows`, `automation_elements`, `automation_mouse`, `automation_keyboard`, `automation_visual`, `automation_assert`, `automation_system`, `automation_mission` |
| **State capture** | `get_desktop_state`, `get_window_state` (set-of-mark annotated screenshots) |
| **CUA compat** | `cua_computer_use_screenshot` |
| **Safety** | `approve_automation`, `automation_safety`, HITL on mouse/keyboard |
| **Opt-in** | `automation_face`, `global_keylogger` |
| **Input stacks** | Mouse: Win32 (`win32_mouse.py`). Keyboard: PyAutoGUI (global). Elements: PyWinAuto UIA + background `PostMessage` |
| **Vision** | PIL capture, Tesseract OCR, OpenCV template match (`find_image`), set-of-mark annotator |
| **Verification** | `automation_assert` (v0.4.3): hash, diff, wait_stable, assert_changed/unchanged, assert_template, assert_text |

### Recommended agent loop (CUA parity)

```
1. automation_windows(find)     → HWND
2. get_window_state(som)        → snapshot_id + element_index
3. automation_elements(click)     → act (prefer snapshot targeting)
   OR automation_keyboard(hotkey) → shortcut-first when possible
4. automation_assert(wait_stable) → UI settled
5. automation_assert(assert_*)    → verify outcome
6. on failure: evidence bundle    → before/after/diff PNGs for host LLM
```

### Known gaps and weaknesses

| Gap | Impact | Phase |
|-----|--------|-------|
| No screenshot diff/compare in `automation_visual` | Agents had to eyeball captures | **Fixed** — use `automation_assert` |
| `RETRY_ATTEMPTS` / `RETRY_DELAY` in config, never wired | Every consumer rolls own retry | Phase 2 |
| Split input stacks (Win32 mouse, PyAutoGUI keyboard) | Focus-loss bugs in VRoid, LibreOffice | Phase 3 |
| `automation_elements` mutators skip HITL + `before_mutation` | Safety inconsistency | Phase 7 |
| `SnapshotStore` in-memory, max 32, no TTL invalidation | Stale element_index clicks | Phase 7 |
| Background `PostMessage` clicks fail on Unity/GPU/canvas apps | VRoid needs foreground dispatch | Document + default per app |
| `automation_mission` record/replay stubbed | No built-in trajectory replay | Phase 8 |
| `find_image` returns single best match only | Misses duplicate icons | Phase 9 |
| `highlight_duration` unused; highlight saves file only | No transient on-screen confirm | Low priority |
| Docs drift (`compare` op listed but missing, keyboard `release` unimplemented) | Agent confusion | Ongoing cleanup |
| No server-side LLM vision | By design — host model analyzes `screenshot_base64` | Tier 3 below |

---

## Status

| Phase | Item | Status |
|-------|------|--------|
| 0 | Rename planning (this doc) | done |
| 1 | `automation_assert` tool | done |
| 2 | Wire `RETRY_ATTEMPTS` into mutating ops | done |
| 3 | Win32 keyboard to HWND (replace PyAutoGUI global send) | done |
| 4 | `automation_dialog` (save/open/export flows) | done |
| 5 | `automation_shortcut` with per-app registries (VRoid first) | done |
| 6 | Package rename `cua-mcp` / `cua_mcp` | partial (`cua_env.py` aliases) |
| 7 | Architecture hardening (HITL, snapshots, foreground defaults) | partial (elements HITL) |
| 8 | `automation_mission` record/replay + trajectory | partial (JSONL replay) |
| 9 | Vision polish (multi-match, evidence bundles, region masks) | partial (`evidence_bundle`) |

---

## Build priority (ordered by payoff)

| # | Item | Effort | Payoff |
|---|------|--------|--------|
| 1 | `automation_assert` | ~2 days | **Done.** Every consumer gets wait_stable + diff + asserts |
| 2 | Win32 keyboard to HWND | ~2 days | Kills focus bugs — biggest reliability win after asserts |
| 3 | `automation_dialog` | ~2 days | Fixes export/save/open brittleness (vroidstudio's worst steps) |
| 4 | `automation_shortcut` + VRoid registry | ~3 days | Eliminates most coordinate clicks |
| 5 | Region masks + template library per app | ongoing | Calibrate once per app version |
| 6 | Wire `RETRY_ATTEMPTS` | ~1 day | Stop consumers reimplementing retry loops |
| 7 | Package rename | ~1 day | Brand clarity |

**Do not do:** Port working automation into the old mocked-alpha SOTA `core/tools/` structure. Working code > dead scaffolding.

---

## Phase details

### Phase 1 — automation_assert (done)

See [AUTOMATION_ASSERT_SPEC.md](AUTOMATION_ASSERT_SPEC.md).

Moves verification out of consumer repos (e.g. vroidstudio-mcp's SHA256 `_wait_stable`) into cua-mcp as a first-class tool.

### Phase 2 — Retry wiring

`RETRY_ATTEMPTS` and `RETRY_DELAY` exist in `config.py` but are unused. Every mutating op should follow:

```
attempt → act → wait_stable → assert → backoff retry
```

vroidstudio-mcp already does this locally in `AutomationEngine._execute_step` — generalize into cua-mcp decorator or helper.

### Phase 3 — Win32 keyboard to HWND

| Current pain | Fix |
|--------------|-----|
| PyAutoGUI sends keys globally | `SendInput` / `PostMessage` targeted at HWND |
| No post-shortcut verify | Shortcut registry declares `expect_state` per action |
| Focus lost mid-flow | `automation_windows(focus)` + assert foreground HWND before every mutation |

### Phase 4 — automation_dialog

Generalize vroidstudio's brittle `export_dialog` / `open_file` / `save_file` steps:

```
automation_dialog(
  operation="save_as",
  path="D:\\exports\\model.vrm",
  hwnd=...,
  verify_template="save_dialog_title.png"
)
```

- Focus dialog → path field → type or clipboard paste (`^v` fallback)
- Confirm → wait for dialog close
- Optional: assert file exists on disk

### Phase 5 — automation_shortcut

Semantic shortcuts per app — generic `automation_keyboard(hotkey)` is blind:

```python
automation_shortcut(
  app="vroidstudio",
  action="export_vrm",
  verify="export_dialog_open"
)
```

**VRoid rule (shortcut-first):** F1–F6 editors, F7 photo booth, F8 export, Ctrl+N/S/O, Enter/Esc dialogs. **Clicks only for:** sample model tile + preset thumbnails.

Shortcut registry should declare `expect_state` and auto-call `automation_assert(wait_stable)` after send.

### Phase 6 — Package rename

1. PyPI: publish `cua-mcp`, keep `windows-computer-use-mcp` as deprecated alias
2. Env vars: `CUA_MCP_*` with fallback to `WINDOWS_COMPUTER_USE_MCP_*`
3. Module: `windows_computer_use_mcp` → `cua_mcp` (breaking; major version bump)
4. Fleet: update avatar-mcp, vroidstudio-mcp, mcp-central-docs, port 10789 references

### Phase 7 — Architecture hardening

1. **Unify input stack** — one DPI-aware Win32 path for mouse + keyboard
2. **HITL on all mutators** — `automation_elements` clicks currently skip safety gates
3. **Snapshot invalidation** — auto-bump `snapshot_id` when window hash changes
4. **Foreground honesty** — Unity/GPU apps (VRoid) default `dispatch="foreground"`; document per-app matrix
5. **Trajectory replay** — connect stubbed `automation_mission` to real record/replay

### Phase 8 — Mission record/replay

`automation_mission` `record`/`replay` are stubbed. vroidstudio's 55 archetypes are essentially replay scripts — connect them via trajectory JSONL (`trajectory.py`).

### Phase 9 — Vision polish

See screenshot analysis tiers below. Add evidence bundle return type.

---

## Screenshot analysis — three tiers

### Tier 1 — No LLM (implement in cua-mcp)

- Perceptual hash (dHash) — tolerates minor animation/GPU noise (**done** in `automation_assert`)
- Region masks — hash/diff editor panel only, ignore status bar and spinning previews
- SSIM diff with heatmap output (**partial** — pixel diff + heatmap in `automation_assert.diff`)
- Template library per app: `vroid/export_dialog.png`, `vroid/sample_picker.png`

### Tier 2 — Cheap vision (mostly exists, extend)

- OCR assert on dialog titles — `assert_text` (**done**)
- Color spot check at known region — **todo**
- `find_image` multi-match — **todo** (currently single best match)
- `assert_template` with confidence threshold — **done**

### Tier 3 — Agent loop (by design, not server-side)

Return structured evidence bundle for host LLM review:

```json
{
  "before_b64": "...",
  "after_b64": "...",
  "diff_b64": "...",
  "som_snapshot_id": "...",
  "changed_pct": 4.2,
  "ocr_text": "Export VRM",
  "recovery_tip": "..."
}
```

Do not embed vision models in cua-mcp. The MCP host (Claude, Cursor) analyzes images.

---

## Design principles

1. **Shortcut-first** — clicks are last resort
2. **Assert everything** — no blind act-then-hope
3. **Region masks** — hash/diff editor panels, ignore chrome and animation
4. **Evidence bundles** — return before/after/diff images for agent review
5. **Honest foreground** — Unity/GPU apps need `dispatch="foreground"`
6. **Best-effort, not production** — GUI automation is inherently brittle

---

## Realistic expectations

Even with full roadmap implemented, cua-mcp remains a **best-effort layer** for apps with no API:

| Risk | Cause |
|------|-------|
| VRoid updates break template coords | UI layout changes |
| Multi-monitor DPI shifts clicks | DPI awareness gaps |
| Unity rendering makes screenshots non-deterministic | GPU compositing, animations |
| Export dialogs vary by locale | OCR/template mismatch |
| pywinauto UIA tree incomplete on custom-drawn controls | Falls back to vision/coords |

### Fleet strategy

| Path | When to use |
|------|-------------|
| **avatar-mcp `hub_download`** | Published VRoid Hub model — reliable |
| **vroidstudio-mcp `quick_gal_export`** | Custom edit in VRoid Studio — best-effort |
| **avatar-mcp `hub_stage_file`** | Booth/creature VRM — skip vroidstudio entirely |

cua-mcp is the **"I edited it in Studio and need an export"** button, not a reliable production pipeline.

---

## Consumers

| Repo | Port | Role |
|------|------|------|
| windows-computer-use-mcp / cua-mcp | 10789 | Windows GUI agent (this repo) |
| vroidstudio-mcp | 10881 | VRoid shortcut layer on top of cua-mcp |
| avatar-mcp | 10793 | Fleet orchestration |
| blender-mcp | 10849 | Downstream VRM processing |

Pipeline:

```
cua-mcp (10789)
  → vroidstudio-mcp (10881)  quick_gal_export
    → avatar-mcp (10793)       avatar_pipeline
      → blender-mcp (10849)
```

### vroidstudio consumer migration

Replace local `_wait_stable` / `_verify_change` with `automation_assert` calls. See [AUTOMATION_ASSERT_SPEC.md](AUTOMATION_ASSERT_SPEC.md) § Consumer migration.

Calibration env vars (host running vroidstudio-mcp):

```powershell
$env:VROID_SAMPLE_MODEL_X = "640"
$env:VROID_SAMPLE_MODEL_Y = "420"
$env:VROID_UI_SCALE_X = "1.0"
$env:VROID_UI_SCALE_Y = "1.0"
```

Use `automation_visual(screenshot)` or `automation_assert(hash_region)` to verify layout after VRoid updates.

---

## What we deliberately skipped

- **Path B (SOTA scaffolding merge):** The old mocked-alpha `core/tools/transport.py` tree on GitHub was packaging around fake tools. vroidstudio v0.3.0 real automation was promoted instead. Do not port working code back into that structure unless `prefab-ui` / MCPB dashboard integration is urgently needed.

---

## References

- [AUTOMATION_ASSERT_SPEC.md](AUTOMATION_ASSERT_SPEC.md) — assert tool API
- [docs/CUA_PARITY.md](CUA_PARITY.md) — Claude computer-use parity notes
- [docs/SAFETY.md](SAFETY.md) — HITL, kill switch, rate limits
- [docs/OFFICE_BACKGROUND_MATRIX.md](OFFICE_BACKGROUND_MATRIX.md) — foreground vs background dispatch
- mcp-central-docs: `integrations/vroidstudio/`, `docs/avatars/FLEET_VRM_PIPELINE.md`
