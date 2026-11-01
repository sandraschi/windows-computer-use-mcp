# Onboarding - windows-computer-use-mcp

## What this is for

**Toolkit for building CUA agents on Windows (plus a built-in mission agent),
and dangerous by nature.** Primitives an AI calls to find windows, click/type,
screenshot/OCR, and run multi-step missions over native Windows UI. It does
**not** replace a sandbox, a screen reader, or a test runner - it drives the
real desktop you point it at, with human-in-the-loop approval for mutating
actions.

> Every click and keystroke hits the live session and can change or delete
> real data. Start with read-only probes, keep HITL on, and use dry-run or a
> VM sandbox (virtualization-mcp) for anything untrusted. Read
> [SAFETY.md](SAFETY.md) before production use.

## Cost and accounts (money / CC)

| Question | Answer |
|----------|--------|
| Do I need an account? | No |
| Free tier? | Yes - fully local, free forever |
| Credit card required? | No |
| Ongoing cost? | Free (optional cloud LLM for missions is yours, not ours) |
| Who bills? | Nobody |

## Prerequisites outside this repo

- Windows 10/11 host (the automation target is the local desktop)
- No wrappee app to install: pywinauto/UIA ships as a Python dependency
- Optional: Tesseract OCR binary for `automation_visual` OCR ops; Ollama on
  `:11434` for local-LLM missions

## First-timer setup steps

1. Complete [INSTALL.md](../INSTALL.md) (installer or `start.ps1`).
2. Start the backend: `start.ps1 -BackendOnly`, wait for `/api/v1/health` 200.
3. Approve automation for your session: `approve_automation(duration_minutes=30)`.
4. List windows: `automation_windows` with `operation=list` - you should see
   your real desktop windows.
5. Try a read-only probe first: `automation_visual` screenshot, or
   `get_desktop_state`, before any click/type.

## Pitfalls

- Mutating actions need HITL approval (or `WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1`
  for unattended runs) - clicks without approval return an approval prompt, not data.
- HWNDs go stale when windows close: re-run `list`/`find` after a miss.
- Focus stealers (chat apps, updaters) break missions: prefer `automation_mission`
  over raw click sequences; it refocuses before each step.
- Do not run missions against a locked screen or RDP-minimized session - UIA
  needs a live desktop.
- Keylogger/face tools are opt-in and off by default; enabling them has obvious
  privacy implications on a shared host.

## Sanity check

- `GET /api/v1/health` returns `{"status": "ok"}`.
- `automation_system` with `operation=status` returns success.
- `automation_windows` with `operation=list` returns your real windows.
- Settings page shows the backend badge green; the red onboarding button below
  the Dashboard hero disappears once health is reachable.

## Declared doubles

- Without a live backend the Dashboard shows declared MOCK KPIs (MOCK badge,
  `Joe Mocky`/`Sandra Mockinger` actors, dashed rose borders) - see
  `web_sota/src/lib/mockOnboarding.ts`. All mocks clear the moment health
  reports reachable; there is no toggle to keep them.
