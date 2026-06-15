# Architecture

Windows **computer use agent** — MCP host drives portmanteau tools; server actuates the real desktop.

```
┌─────────────────┐     stdio / HTTP      ┌──────────────────────────┐
│  MCP host       │ ◄──────────────────► │  windows-computer-use-mcp│
│  (Cursor,       │      /mcp             │  FastMCP 3.2 + FastAPI    │
│   Claude, …)    │                       │  port 10789              │
└─────────────────┘                       └───────────┬──────────────┘
                                                        │
                        ┌───────────────────────────────┼───────────────────────────────┐
                        ▼                               ▼                               ▼
                 win32_mouse / UIA              pywinauto / PyAutoGUI            OCR / OpenCV
                        │                               │                               │
                        └───────────────────────────────┴───────────────────────────────┘
                                                        │
                                                        ▼
                                              Windows desktop session
```

## Components

| Layer | Path | Role |
|-------|------|------|
| MCP surface | `src/windows_computer_use_mcp/app.py`, `tools/` | Portmanteau tool registration |
| Transport | `src/windows_computer_use_mcp/transport.py`, `server.py` | stdio + ASGI `/mcp` + REST `/api/v1` |
| Input | `src/windows_computer_use_mcp/win32_mouse.py` | DPI-aware pointer injection |
| Safety | `src/windows_computer_use_mcp/safety*.py` | HITL, kill switch, rate limits |
| Web operator | `web_sota/` | Vite UI on **10788** → proxy **10789** |
| Desktop app | `web_sota/src-tauri/` | Tauri operator + PyInstaller sidecar |

## Fleet position

- **Hands, not brain** — see [MEMOPS_CUA.md](MEMOPS_CUA.md)
- Isolation: [virtualization-mcp](https://github.com/sandraschi/virtualization-mcp)
- Sibling: [autohotkey-mcp](https://github.com/sandraschi/autohotkey-mcp) (AHK scriptlets)
- Browser DOM: use a Playwright MCP (orthogonal stack)

## Packaging

| Channel | Doc |
|---------|-----|
| `uv` / PyPI | [INSTALL.md](../INSTALL.md) |
| MCPB | [mcpb/README.md](../mcpb/README.md) |
| Desktop installer | [DESKTOP_APP.md](DESKTOP_APP.md) |
