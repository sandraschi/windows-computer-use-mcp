# Desktop operator app (Tauri + MCP sidecar)

The `web_sota` operator UI ships as a Windows desktop app. Tauri hosts the Vite build; the Python MCP server runs as a **bundled sidecar** on `127.0.0.1:10789`.

Fleet standard reference: [tauri_godot_sota.md](https://github.com/sandraschi/mcp-central-docs/blob/main/standards/rules/tauri_godot_sota.md) (sidecar model, installer MCP registration).

## What the user installs

Double-click **one installer** (NSIS or MSI). That installs **one app to launch:**

| What users see | What it is |
|----------------|------------|
| `windows-computer-use-operator.exe` | **The product.** Tauri + WebView + embedded React UI + embedded Python backend |

No second exe in the install folder. The PyInstaller backend is bundled as an app **resource**, copied on first launch to `%LOCALAPPDATA%\com.sandraschi.windows-computer-use-mcp\cache\`, spawned as a child process, and killed when you quit.

No Python, `uv`, or git clone on the target machine. WebView2 bootstrapper is bundled when missing.

## Architecture

```
windows-computer-use-operator.exe          (single user-facing binary)
  ├── web_sota/dist                 (embedded React UI)
  └── resources/windows-computer-use-backend.exe   (embedded, not a sibling shortcut)
        └── copied to app cache on launch
              └── uvicorn 127.0.0.1:10789
                    ├── /api/v1/…   REST (operator UI)
                    └── /mcp          MCP (Cursor / Claude)
```

**Normal use:** run `windows-computer-use-operator.exe` only.

**Debugging without Tauri:** build the backend with `npm run sidecar:build`, then run `web_sota\src-tauri\resources\windows-computer-use-backend.exe` (or the dev copy under `binaries/`).

## MCP clients (Cursor / Claude Desktop)

The operator app **does not** replace Cursor or Claude. It exposes MCP at:

`http://127.0.0.1:10789/mcp`

While the operator is running, AI clients can call pywinauto tools over that URL.

### Installer (NSIS)

After file copy, the NSIS installer shows an optional dialog:

- **Register in Cursor** → merges into `%USERPROFILE%\.cursor\mcp.json`
- **Register in Claude Desktop** → merges into `%APPDATA%\Claude\claude_desktop_config.json`

Script: `web_sota/scripts/install-mcp-clients.ps1` (also bundled under `$INSTDIR\resources\`).

MSI installs skip this hook; use first-run UI in the app (Settings → MCP clients).

### First-run UI

On first launch in Tauri, a setup dialog offers the same registration. Re-open from **Settings → Show first-run MCP setup again**.

Manual entry (if needed):

```json
{
  "mcpServers": {
    "windows-computer-use-mcp": {
      "url": "http://127.0.0.1:10789/mcp"
    }
  }
}
```

**Important:** MCP is available only while the operator (or a standalone backend process) is listening on port 10789.

## Prerequisites (build machine)

- Node 20+
- Rust stable (`%USERPROFILE%\.cargo\bin` on PATH)
- WebView2 (runtime on end-user machines)
- `uv` + Python 3.12 for sidecar freeze

## One-time setup

```powershell
cd D:\Dev\repos\windows-computer-use-mcp\web_sota
npm install
npm run icons:generate
npm run test:e2e:install
```

## Dev (browser stack)

```powershell
cd web_sota
.\start.ps1
```

## Dev (Tauri shell)

```powershell
cd web_sota
npm run sidecar:build
npm run tauri:dev
```

## Production installer

```powershell
$env:Path = "$env:USERPROFILE\.cargo\bin;" + $env:Path
cd web_sota
npm run tauri:build
```

Artifacts: `web_sota/src-tauri/target/release/bundle/` (MSI + NSIS).

Register MCP clients manually after MSI, or from the app on first launch.

## Backend only (debug, no Tauri window)

```powershell
cd web_sota
npm run sidecar:build
.\src-tauri\resources\windows-computer-use-backend.exe
```

## CI

See `docs/TESTING.md` for Vitest, Playwright, and optional `build-tauri`.
