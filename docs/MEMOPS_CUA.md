---
title: CUA-MCP — computer use doctrine (2026-06-08)
status: active
tags: [cua, memops, windows-computer-use-mcp, vroidstudio, fleet, automation, gui]
related:
  - docs/CUA_ROADMAP.md
  - docs/CUA_ASSISTANT_TODO.md
  - integrations/vroidstudio/
---

# CUA-MCP — MemOps note

## One-line thesis

**cua-mcp is the fleet's hands, not the brain** — verified Windows GUI actuator with shortcut-first design; true "computer use assistant" requires a closed-loop task runner + outcome verification.

## Naming

| Public | Internal (until v1.0) | Port |
|--------|------------------------|------|
| **cua-mcp** | `windows-computer-use-mcp` / `windows_computer_use_mcp` | 10789 |

Nobody knows pywinauto. Use **CUA-MCP (Computer Use Agent)** in docs and fleet tables.

## What it is today (v0.5.x)

- Portmanteau tools: windows, elements, mouse, keyboard, visual, **assert**, **dialog**, **shortcut**, **task**
- Set-of-mark `get_window_state` for CUA-shaped loops
- VRoid semantic shortcuts (F1–F8, Ctrl+N/S/O, dialogs)
- dHash stability + evidence bundles on assert failure
- Win32 keyboard focus when `CUA_MCP_KEYBOARD=win32`
- Retry via `CUA_MCP_RETRY_ATTEMPTS`

## What it is NOT

- Not a vision model — screenshots go to host LLM
- Not reliable on Unity/GPU apps without foreground + calibration
- Not a replacement for VRoid Hub download (avatar-mcp path is safer)

## Fleet role

```
cua-mcp (10789)           ← hands: click, shortcut, dialog, assert
  → vroidstudio-mcp (10881) ← VRoid-specific step templates / archetypes
    → avatar-mcp (10793)    ← orchestration brain
```

**Golden rule:** Hub download when possible; cua-mcp only when user edited in VRoid Studio.

## Design principles (non-negotiable)

1. **Shortcut-first** — clicks only for sample tile + preset thumbnails (VRoid)
2. **Assert everything** — no blind act-then-hope
3. **Outcome over pixels** — file exists beats 1% screen diff
4. **Evidence on failure** — before/after/diff for host LLM review
5. **Honest foreground** — Unity apps need focus; document per app

## Gap closure priority

1. **`automation_task`** — closed-loop runner (T1.1)
2. Outcome asserts — file/process (T1.2)
3. ~~vroidstudio → task delegation (T1.6)~~ done v0.3.4
4. **system-admin-mcp preflight** — process find, RAM/disk depletion (T1.8)
5. Template libraries per app version (T2.3)
6. Full rename to `cua-mcp` PyPI (T5.1)

Track: [CUA_ASSISTANT_TODO.md](CUA_ASSISTANT_TODO.md)

## Env cheatsheet

```powershell
$env:CUA_MCP_URL = "http://127.0.0.1:10789"
$env:CUA_MCP_KEYBOARD = "win32"
$env:CUA_MCP_RETRY_ATTEMPTS = "3"
$env:WINDOWS_COMPUTER_USE_MCP_DISPATCH = "foreground"   # VRoid / Unity
$env:SYSTEM_ADMIN_MCP_URL = "http://127.0.0.1:10861"
$env:VROID_USE_CUA_TASK = "1"
$env:VROID_USE_SYSADMIN_PREFLIGHT = "1"
```

## Fleet crossconnect (system-admin-mcp)

Before long `automation_task` runs, cua-mcp / vroidstudio can call **system-admin-mcp** for:

- `list_processes` — VRoid Studio already running?
- `get_performance_metrics` — RAM/CPU headroom
- `get_top_resource_processes` — what's starving the host?

vroidstudio runs async preflight (`preflight.py`); cua-mcp task steps support `kind: preflight` for inline checks.

## Relations

- implements [[FLEET_VRM_PIPELINE]] VRoid Studio leg (best-effort)
- blocks [[vroidstudio-mcp]] reliability until cua-mcp task runner ships
- unblocks [[avatar-mcp]] `quick_gal_export` when calibrated
- pairs with [[virtualization-mcp]] for sandbox isolation (not wired)

## MemOps hygiene

After cua-mcp milestone: update this note + `CUA_ASSISTANT_TODO.md` checkboxes. Ingest to advanced-memory if fleet journal active.
