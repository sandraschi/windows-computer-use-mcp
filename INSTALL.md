# Installation

## Desktop app (recommended for most users)

**Windows only.** One installer — no Python, `uv`, or git required on the target machine.

1. Download **`Windows Computer Use Operator_*_x64-setup.exe`** from [GitHub Releases](https://github.com/sandraschi/windows-computer-use-mcp/releases) (or build locally below).
2. Run the installer. The NSIS setup may offer to register the MCP server in **Cursor** and **Claude Desktop**.
3. Launch **Windows Computer Use Operator** from the Start menu.

That opens `windows-computer-use-operator.exe`, which:

- Shows the operator web UI (Targets, tools hub, HITL, etc.)
- Starts the bundled MCP/REST backend on `http://127.0.0.1:10789`
- Exposes MCP at `http://127.0.0.1:10789/mcp` for Cursor/Claude while the app is running

You only double-click the **operator** app. The Python backend is embedded inside it (extracted to local app cache on launch — not a second install shortcut).

**First launch:** a setup dialog can register Cursor/Claude. Re-open from **Settings** in the app. MSI installs skip the installer dialog — use that in-app flow instead.

Full architecture: **[docs/DESKTOP_APP.md](docs/DESKTOP_APP.md)** · Fleet Tauri standard: `mcp-central-docs/standards/rules/tauri_godot_sota.md`

### Build the desktop installer (maintainers)

```powershell
winget install Rustlang.Rustup    # if needed; ensure %USERPROFILE%\.cargo\bin on PATH
cd D:\Dev\repos\windows-computer-use-mcp\web_sota
npm install
npm run icons:generate            # once
npm run tauri:build
```

Artifacts:

- `web_sota/src-tauri/target/release/bundle/nsis/Windows Computer Use Operator_*_x64-setup.exe`
- `web_sota/src-tauri/target/release/bundle/msi/Windows Computer Use Operator_*_x64_en-US.msi`

Requires Node 20+, Rust stable, `uv` + Python 3.12 for the PyInstaller sidecar freeze.

---

## Developer quick start (`just`)

For hacking on the repo, CI, or MCP **stdio** from source:

```powershell
winget install Casey.Just    # Windows
git clone https://github.com/sandraschi/windows-computer-use-mcp
cd windows-computer-use-mcp
just
```

```powershell
just bootstrap   # install all dependencies
just serve       # MCP + REST backend (10789)
just web         # browser UI via web_sota (10788)
```

Browser stack without Tauri: `web_sota/start.ps1` (frontend **10788**, backend **10789**).

Tauri dev shell (native window + sidecar):

```powershell
cd web_sota
npm run sidecar:build
npm run tauri:dev
```

> **Why not `pip install`?** MCP servers bundle webapps, configs, and tooling a flat PyPI wheel can't ship. `just` / the desktop installer give you the full stack.

---

## Traditional setup (no `just`)

1. Install [Python 3.12+](https://python.org) and [uv](https://docs.astral.sh/uv/)
2. Clone and enter the repo:
   ```powershell
    git clone https://github.com/sandraschi/windows-computer-use-mcp
    cd windows-computer-use-mcp
   ```
3. Install dependencies:
   ```powershell
   uv sync --all-extras
   ```
4. Start the server:
   ```powershell
   # stdio (Cursor / Claude spawn the process)
   uv run python -m pywinauto_mcp

   # HTTP (browser UI or streamable MCP URL)
   uv run uvicorn pywinauto_mcp.server:app --host 127.0.0.1 --port 10789
   ```
5. Optional browser UI:
   ```powershell
   cd web_sota
   npm install
   npm run dev
   ```
   Open `http://localhost:10788` (API proxied to **10789**).

### MCP client config (source / HTTP)

**stdio** (from source):

```json
{
  "mcpServers": {
    "windows-computer-use": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/windows-computer-use-mcp", "run", "python", "-m", "pywinauto_mcp"]
    }
  }
}
```

**HTTP** (desktop app or `uvicorn` running):

```json
{
  "mcpServers": {
    "windows-computer-use": {
      "url": "http://127.0.0.1:10789/mcp"
    }
  }
}
```

Paths: Cursor → `%USERPROFILE%\.cursor\mcp.json` · Claude → `%APPDATA%\Claude\claude_desktop_config.json`

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Desktop app: MCP tools missing in IDE | Keep **Windows Computer Use Operator** running; re-register in **Settings** |
| Desktop build: `rustc` not found | Add `%USERPROFILE%\.cargo\bin` to PATH |
| Sidecar build fails on `charset_normalizer` | See `scripts/pyinstaller_hooks/` override in repo; recreate `.venv` if needed |
| `just` not found | `winget install Casey.Just` |
| Port conflict | `just kill-all` (fleet ports 10700–11000) |
| Dependencies out of sync | `uv sync --all-extras` |
| Something else | [Open a GitHub issue](https://github.com/sandraschi/windows-computer-use-mcp/issues) |

---

*See [README.md](README.md) for features, safety, and tool overview.*
