# Operator web UI (web_sota)

Vite + React dashboard for windows-computer-use-mcp. See root [README.md](../README.md) for the full stack.

## Routes

| Route | Page |
|---|---|
| `/` | Dashboard — CUA KPIs (windows, tools, safety gate, watchers) + host health |
| `/missions` | Missions — run/plan missions, replay macros, manage watchers (live bridge) |
| `/windows` | Window Manager |
| `/elements` | Element Inspector |
| `/crawler` | App Crawler (`analyze_winapp`) |
| `/tools` | Tools Hub — call any MCP tool raw |
| `/targets` | Per-app automation targets + HITL bar |
| `/chat` | Local LLM chat |
| `/biometrics` | Face/keylogger opt-in status |
| `/logs` | Logs |
| `/settings` | Settings (LLM, safety, onboarding) |
| `/help` | Help — CUA guide, 22-tool reference, safety layers |

## Dev

```powershell
npm install
npm run dev
```

Opens http://localhost:10788 (proxies API to :10789).

## Build

```powershell
npm run build   # outputs to dist/
npm run tauri:build  # or the desktop app
```

## Tauri desktop app

The `src-tauri/` subfolder wraps the built frontend + embedded Python backend into a single NSIS installer. See `src-tauri/tauri.conf.json`.
