# Operator web UI (web_sota)

Vite + React dashboard for windows-computer-use-mcp. See root [README.md](../README.md) for the full stack.

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
