# CUA Assistant — Gap closure TODO

Target: evolve cua-mcp from **verified GUI actuator** to **computer use assistant**.

See [MEMOPS_CUA.md](MEMOPS_CUA.md) for fleet doctrine. Highest leverage: **`automation_task`** closed loop.

---

## Tier 1 — MVP assistant (in progress)

| ID | Feature | Status | Module |
|----|---------|--------|--------|
| T1.1 | **`automation_task` runner** — observe→act→verify→recover loop | done (v0.5.0) | `task_engine.py`, `portmanteau_task.py` |
| T1.2 | **Outcome verification** — `file_exists`, `file_min_kb` | done | `task_engine.assert_outcome` |
| T1.3 | **App profiles** — foreground policy, default HWND title | done | `app_profiles.py` |
| T1.4 | **Evidence trail** per step (screenshot paths, results) | done | `TaskSession.evidence` |
| T1.5 | **Recovery strategies** — `retry`, `refocus_retry`, `abort` | done | step `on_fail` field |
| T1.6 | Wire vroidstudio archetypes → `automation_task` | done (vroidstudio v0.3.4) | `task_steps.py`, `automation.py` |
| T1.7 | Snapshot invalidation on UI hash change | done | `snapshot_store.py` |
| T1.8 | **system-admin-mcp crossconnect** — process find, resource preflight | done | `sysadmin_client.py`, `sysadmin_preflight.py`, vroid `preflight.py` |

## Tier 2 — Perception & grounding

| ID | Feature | Status | Notes |
|----|---------|--------|-------|
| T2.1 | Structured perception bundle for host LLM | partial | `evidence_bundle` on assert |
| T2.2 | Auto re-snapshot after every mutating step | done (v0.5.2) | `task_engine._invalidate_snapshots_after_mutation` |
| T2.3 | Template library per app version | done (v0.5.3) | `template_library.py`, `templates/vroidstudio/` |
| T2.4 | Region masks in app profiles (not env-only) | done (v0.5.3) | `app_profiles.RegionMask`, `task_engine._step_region` |
| T2.5 | `find_image` multi-match | todo | `portmanteau_visual` |
| T2.6 | Color spot assert at region | todo | `automation_assert` |

## Tier 3 — Full assistant

| ID | Feature | Status | Notes |
|----|---------|--------|-------|
| T3.1 | Goal → decomposed steps (LLM planner inside cua-mcp) | todo | optional VLM |
| T3.2 | Cross-app workflow session (fleet handoff) | todo | avatar-mcp integration |
| T3.3 | Natural language `run_task(goal=...)` | todo | host or local planner |
| T3.4 | Operator console / live status | spec ready | [TARGETS_PAGE_SKETCH.md](TARGETS_PAGE_SKETCH.md) — `/targets` page (W1) |
| T3.5 | Full audit replay (video + screenshots) | todo | extend trajectory |
| T3.6 | Human coexistence — pause on user input | todo | pynput hook |
| T3.7 | No-warp virtual input | todo | research |

## Tier 4 — App coverage

| ID | App | Status |
|----|-----|--------|
| T4.1 | VRoid Studio | shortcuts + dialog + task steps |
| T4.2 | LibreOffice | e2e exists; needs profile |
| T4.3 | Generic Win32 dialog | partial (`automation_dialog`) |
| T4.4 | Electron / Qt | todo — vision-first |

## Tier 5 — Rename & packaging

| ID | Item | Status |
|----|------|--------|
| T5.1 | PyPI `cua-mcp` alias | todo |
| T5.2 | Module `cua_mcp` | todo v1.0 |
| T5.3 | Fleet docs + port table rename | todo |

---

## Step schema (`automation_task`)

```json
{
  "kind": "shortcut | dialog | focus | wait_stable | assert_file | screenshot | click | preflight",
  "app": "vroidstudio",
  "action": "export_vrm",
  "path": "D:\\out\\model.vrm",
  "window_title": "VRoid Studio",
  "on_fail": "retry | refocus_retry | abort",
  "verify_stable": true
}
```

## Definition of done (deserves the name)

- [x] Agent can call **one tool** with a step list; cua-mcp runs the full loop
- [x] Failures return **evidence trail** (screenshots + recovery attempts)
- [x] Outcomes verified by **filesystem/process**, not pixels alone
- [x] VRoid export works end-to-end via task profile without manual tool chaining (T1.6)
- [x] Preflight checks disk/memory/process via system-admin-mcp before task run (T1.8)
