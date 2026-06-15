# windows-computer-use-mcp

<p align="center">
  <a href="https://github.com/sandraschi/windows-computer-use-mcp"><img src="https://img.shields.io/github/stars/sandraschi/windows-computer-use-mcp?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/sandraschi/windows-computer-use-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://fastmcp.com"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

**Windows Computer Use for AI Agents** — click, screenshot, type, drag, OCR, and verify native Windows UI via MCP. The missing hands for your agentic workflows.

> **Exhibit A: 100 Tauri/NSIS installers, one unattended run, $2 in LLM costs.**
> Install → screenshot → verify → report — zero human intervention.

Built on [pywinauto](https://github.com/pywinauto/pywinauto). Read **[docs/SAFETY.md](docs/SAFETY.md)** before production use.

- [Quick Start](#quick-start)
- [Features](#features)
- [Documentation](#documentation)
- [Ports](#ports)
- [License](#license)

---

## Quick Start

| Method | Command / Config |
|--------|-----------------|
| **MCP stdio** (Cursor, Claude Desktop) | `{ "mcpServers": { "windows-computer-use": { "command": "uv", "args": ["--directory", "<PATH>", "run", "windows-computer-use-mcp"] } } }` |
| **HTTP streamable** (any MCP HTTP client) | `{ "mcpServers": { "windows-computer-use": { "url": "http://127.0.0.1:10789/mcp" } } }` |
| **Web operator UI** | `.\start.ps1` → http://127.0.0.1:10788 |
| **Desktop app** (NSIS installer) | Download from [Releases](https://github.com/sandraschi/windows-computer-use-mcp/releases) — zero deps |

See **[INSTALL.md](INSTALL.md)** for detailed setup. Run `just demo` for examples.

---

## Features

- **Window Management** — find, activate, maximize, minimize, position, close
- **Mouse & Keyboard** — click, drag, type, hotkeys, app shortcuts
- **UI Elements** — inspect, click, read text, verify state via UIA / Win32
- **Visual Intelligence** — screenshots, OCR, template matching
- **Autonomous Missions** — give it a goal, it plans and executes with retry + verification
- **Macro Recording** — record any UI sequence, replay, verify outcomes
- **Multi-App Workflows** — chain actions across Notepad, Calc, Paint, or any Windows app
- **Telemetry** — every action logged to SQLite; query failure patterns by tool
- **Adaptive Location** — auto-cascades through title/auto_id/control_id/class/OCR to find elements
- **Face Recognition** — optional, off by default

---

## Documentation

| Doc | Content |
|-----|---------|
| [INSTALL.md](INSTALL.md) | Setup: desktop app, uv, MCP config |
| [docs/README.md](docs/README.md) | Full documentation hub |
| [docs/py-stack.md](docs/py-stack.md) | Python dependency deep dive |
| [docs/SAFETY.md](docs/SAFETY.md) | HITL, kill switch, opt-in features |
| [docs/TOOLS.md](docs/TOOLS.md) | Portmanteau tool reference |
| [tests/README.md](tests/README.md) | Test suite guide and e2e setup |
| [examples/README.md](examples/README.md) | Runnable demos |
| [mcpb/README.md](mcpb/README.md) | MCPB bundle packaging |
| [web_sota/README.md](web_sota/README.md) | Operator UI build/dev guide |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

---

## Ports

| Port | Service |
|------|---------|
| **10788** | Frontend — Vite operator UI |
| **10789** | Backend — FastAPI + FastMCP HTTP | 
| stdio | MCP transport (port-free) |

---

## Related

| Repo | What it does |
|------|-------------|
| **[autohotkey-mcp](https://github.com/sandraschi/autohotkey-mcp)** | Raw input recording/replay via AHK |
| **[virtualization-mcp](https://github.com/sandraschi/virtualization-mcp)** | Sandbox / VM isolation |
| **[windows-operations-mcp](https://github.com/sandraschi/windows-operations-mcp)** | Registry, services, accounts |

Fleet standards: [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs).

---

## License

MIT — Copyright (c) 2026 Sandra Schipal.
