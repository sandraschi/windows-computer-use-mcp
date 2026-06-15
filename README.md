# windows-computer-use-mcp

<p align="center">
  <a href="https://github.com/sandraschi/windows-computer-use-mcp"><img src="https://img.shields.io/github/stars/sandraschi/windows-computer-use-mcp?style=flat-square" alt="Stars"></a>
  <a href="https://github.com/sandraschi/windows-computer-use-mcp/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
</p>

**Windows Computer Use for AI Agents** — click, screenshot, type, drag, OCR, and verify native Windows UI via MCP. The missing hands for your agentic workflows.

> **Exhibit A: 100 Tauri/NSIS installers, one unattended run, $2 in LLM costs.**
> Install → screenshot → verify → report — zero human intervention. That's the gap this fills.

Built on [pywinauto](https://github.com/pywinauto/pywinauto). Exposed as a clean FastMCP server.

Pair with **[virtualization-mcp](https://github.com/sandraschi/virtualization-mcp)** for Windows Sandbox / VM isolation. Read **[docs/SAFETY.md](docs/SAFETY.md)** before production use.

> 📖 **[INSTALL.md](INSTALL.md)** — desktop installer, `uv` setup, MCP client config

---

## What It Can Do

- **Window Management** — find, activate, maximize, minimize, position, close
- **Mouse Control** — click, double-click, right-click, drag, scroll, hover, precise coordinates
- **Keyboard Input** — type text, send key combinations, shortcuts
- **UI Element Interaction** — click controls, read/set text, verify states, wait for elements
- **Visual Intelligence** — screenshots, OCR text extraction, image recognition
- **Closed-Loop Tasks** — multi-step automation with retry, refocus recovery, evidence trails
- **Face Recognition** — optional plugin for webcam-based verification workflows

---

## Quick Start

```powershell
git clone https://github.com/sandraschi/windows-computer-use-mcp.git
cd windows-computer-use-mcp
just bootstrap
just serve
```

**MCP (stdio)** — add to Cursor / Claude Desktop:

```json
{
  "mcpServers": {
    "windows-computer-use": {
      "command": "uv",
      "args": ["--directory", "<PATH-TO-CLONE>", "run", "windows-computer-use-mcp"]
    }
  }
}
```

**Optional web operator UI:** `.\start.ps1` → http://127.0.0.1:10788 (proxies API on **10789**).

**Demos:** `just demo` — mouse dance, Notepad grid, typewriter (see [examples/README.md](examples/README.md)).

---

## Works With

- **Claude Desktop** (MCP native)
- **DeepSeek** via OpenCode/API
- **Any FastMCP-compatible agent**

---

## Python stack (py- modules)

| Package | Role in this project |
|---------|----------------------|
| **[pywinauto](https://github.com/pywinauto/pywinauto)** | **Core** — attach to HWNDs, walk UIA/Win32 control trees, click/type/read elements (`automation_windows`, `automation_elements`). |
| **pywin32** | Low-level Win32 COM/API (session, processes, DPI helpers) used alongside pywinauto. |
| **pygetwindow** | Window titles/rectangles for discovery and layout. |
| **pyautogui** | Fallback screen-level pointer/screenshot helpers where UIA is not enough. |
| **pynput** | Injects and **optionally** listens to keyboard/mouse at the session level; powers normal `automation_keyboard` simulation and the **opt-in** `global_keylogger` hook. |
| **pyperclip** | Clipboard read/write for `automation_system`. |
| **opencv-python-headless** | Screenshots, camera index probe, template match paths in `automation_visual` / biometrics preview. |
| **pytesseract** | OCR in `automation_visual` (needs Tesseract installed on the host). |
| **face_recognition** + **dlib** | **Optional extra only** (`uv sync --extra face`) for `automation_face` — not installed in the default desktop bundle. |

Other important non-`py` deps: **FastMCP** (MCP server), **FastAPI** + **uvicorn** (REST + `/mcp` HTTP), **Pillow**, **numpy**, **httpx**.

---

## Optional invasive features (off by default)

**Default install:** window/element/mouse/keyboard/visual automation only. No ambient monitoring.

| Feature | Shipped in code? | Default? | Enable |
|---------|------------------|----------|--------|
| **`automation_face`** | Yes — local webcam capture/match | **Off** — tool not registered | `WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1` + `uv sync --extra face` ([SAFETY.md §5](docs/SAFETY.md)) |
| **`global_keylogger`** | Yes — session keyboard hook | **Off** — tool not registered | `WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER=1` ([SAFETY.md §6](docs/SAFETY.md)) |

**Keylogger is not stealth spyware.** It is an explicit MCP tool: disabled unless you set the env flag, requires **HITL approval** to `start`, stores events in a **bounded in-memory buffer** (not hidden files), and the server **stops the hook on shutdown**. Use only on machines you own for debugging shortcut/focus issues — not for credential harvesting.

**Face recognition is not a background plan-only sketch** — the tool is implemented but **opt-in** like the keylogger. The operator UI **Biometrics** page is a control panel when you enable it; it does not run face matching unless you opt in and call the tool.

---

## Documentation

| Doc | Content |
|-----|---------|
| [INSTALL.md](INSTALL.md) | Desktop app, `uv`, MCP client config |
| [docs/README.md](docs/README.md) | Full documentation hub |
| [docs/SAFETY.md](docs/SAFETY.md) | HITL, kill switch, opt-in features |
| [docs/TOOLS.md](docs/TOOLS.md) | Portmanteau tool reference |
| [tests/README.md](tests/README.md) | Test suite guide and e2e setup |
| [examples/README.md](examples/README.md) | Runnable demos |
| [mcpb/README.md](mcpb/README.md) | MCPB bundle packaging |
| [skills/desktop-automation-protocol/SKILL.md](skills/desktop-automation-protocol/SKILL.md) | Cursor agent skill |
| [CHANGELOG.md](CHANGELOG.md) | Release history |

An MCP prompt is also registered: `desktop_automation_operator_protocol` (see `src/windows_computer_use_mcp/prompts.py`).

---

## Ports

| Port | Service |
|------|---------|
| **10788** | Frontend — Vite operator UI (`web_sota`) |
| **10789** | Backend — FastAPI `/api/v1/*` + FastMCP HTTP `/mcp` |

Stdio MCP has no port (host-launched process).

---

## Tech Stack

- **MCP:** Python 3.12+, FastMCP 3.2+, portmanteau tools (windows, elements, mouse, keyboard, visual, assert, dialog, shortcut, task, system)
- **Input:** `win32_mouse` (DPI-aware), optional Win32 keyboard (`CUA_MCP_KEYBOARD=win32`)
- **Web:** Vite + React operator dashboard, local LLM proxy (Ollama / LM Studio)
- **Desktop:** Tauri 2 operator app (optional installer)
- **Quality:** Ruff, Biome, pytest (environment-aware), `just` recipes

---

## Related

| Tool | What it does | When to use |
|------|-------------|-------------|
| **windows-computer-use-mcp (here)** | **Computer use agent** — structured native UI automation via UIA element tree, screenshots, OCR | You need to **inspect controls, click buttons, read text** from apps with accessibility trees. |
| [autohotkey-mcp](https://github.com/sandraschi/autohotkey-mcp) | AHK scriptlet depot — list, run, stop, generate `.ahk` scripts | You need **raw keyboard/mouse recording** via AHK's built-in recorder. |
| [virtualization-mcp](https://github.com/sandraschi/virtualization-mcp) | Sandbox / VM isolation | You need to isolate automation in a disposable VM. |
| [windows-operations-mcp](https://github.com/sandraschi/windows-operations-mcp) | Deep Windows control plane (registry, services, accounts) | System-level ops, not GUI. |

Fleet standards: [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs).

**Browser vs desktop:** This server drives **Win32 / UI Automation**. For HTML/DOM and websites, use a **Playwright browser MCP** alongside this one.

---

## License

MIT — Copyright (c) 2026 Sandra Schipal.
