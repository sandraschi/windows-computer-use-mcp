# PRD — windows-computer-use-mcp (Computer Use Agent)

## 1. Overview

**windows-computer-use-mcp** is the fleet's Windows **computer use agent** — a [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes **portmanteau tools** so AI clients can operate the **real desktop**: discover windows, interact with UI Automation elements, inject mouse/keyboard, capture screenshots/OCR, run shortcuts, handle dialogs, and **verify outcomes** (assert).

**Positioning:** *Hands, not brain.* The host LLM plans; this server executes and reports structured evidence. Closed-loop task running is roadmap ([CUA_ROADMAP.md](CUA_ROADMAP.md)); today operators combine MCP tools + HITL.

**Non-goals:** Not a browser DOM agent (use Playwright MCP). Not an isolation boundary — pair with **`virtualization-mcp`** for Sandbox/VM. See [SAFETY.md](SAFETY.md).

**Package name:** `windows-computer-use-mcp` / `windows_computer_use_mcp`. Public fleet label: **Windows Computer Use MCP**.

## 2. Goals

| Goal | Detail |
|------|--------|
| **Computer use** | Reliable Windows GUI actuation with structured tool results for agent loops |
| **Tool efficiency** | Portmanteau tools limit tool explosion and token load |
| **Framework** | **FastMCP 3.2+** — stdio + HTTP `/mcp`; async tools; docstring-first descriptions |
| **Safety** | HITL via `approve_automation`, kill switch, rate limits, dry-run; invasive tools opt-in only |
| **Verification** | `automation_assert`, set-of-mark state, evidence on failure |
| **Operator UX** | Optional **`web_sota`** + Tauri **operator app** — tools hub, HITL, local LLM chat |
| **Testability** | Environment-aware pytest per **mcp-central-docs** — [TESTING.md](TESTING.md) |
| **Distribution** | PyPI (`uvx`), MCPB bundle, desktop installer |

## 3. Key product surfaces

### 3.1 MCP tools (core)

| Tool | Purpose |
|------|---------|
| `automation_windows` | Window lifecycle — find, focus, move, resize, close |
| `automation_elements` | UIA element ops — click, text, tree |
| `automation_mouse` | Pointer — click, drag, scroll, telemetry HUD |
| `automation_keyboard` | Keys, hotkeys, typing |
| `automation_visual` | Screenshot, OCR, image match |
| `automation_assert` | Outcome verification (CUA loops) |
| `automation_dialog` | Native dialog handling |
| `automation_shortcut` | App-specific shortcut tables (e.g. VRoid) |
| `automation_task` | Multi-step task helpers |
| `automation_system` | Help, clipboard, processes, `start_app` |
| `get_desktop_state` / `get_window_state` | Discovery, set-of-mark |
| `approve_automation`, `automation_safety` | HITL and counters |

**Opt-in only (not registered in default / desktop bundle):**

- `automation_face` — implemented local webcam tool; `WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1` + `face` extra ([SAFETY.md](SAFETY.md) §5)
- `global_keylogger` — implemented session debug hook; non-stealth, HITL-gated; `WINDOWS_COMPUTER_USE_MCP_ENABLE_KEYLOGGER=1` ([SAFETY.md](SAFETY.md) §6)

### 3.2 HTTP / ASGI

- FastAPI **`/api/v1/*`** — health, tools, windows, LLM proxy, cameras, safety
- FastMCP **`http_app()`** mounted at **`/mcp`**
- CORS for local `web_sota` dev ports and Tauri webview (`PYWINAUTO_TAURI=1`)

### 3.3 Web operator (`web_sota`)

- Vite UI; **`start.ps1`** — frontend **10788**, backend **10789**
- Routes: Overview, Windows, Elements, Tools Hub, Local LLM (`/chat`), Help, Biometrics, Settings
- Local LLM: Ollama / LM Studio via OpenAI-compatible proxy (`PYWINAUTO_LLM_BASE_URL`)

### 3.4 Desktop operator app

- Tauri 2 + PyInstaller sidecar — see [DESKTOP_APP.md](DESKTOP_APP.md), [INSTALL.md](../INSTALL.md)
- Bundled backend; optional Cursor/Claude registration on first launch

## 4. Technical standards

- **Python 3.12+**, **Windows 10/11** for production automation
- **Ruff** lint/format; `win32_mouse` for DPI-aware pointer injection
- **Env:** `CUA_MCP_KEYBOARD=win32`, `CUA_MCP_RETRY_ATTEMPTS`, standard safety keys (see README / SAFETY)
- **Testing:** `requires_hardware`, `destructive` markers; CI skips hardware probes

## 5. Success metrics (directional)

- Tool calls return structured **`success` / `error`** with recoverable guidance
- First connection documented for MCP clients ([INSTALL.md](../INSTALL.md), [mcpb/README.md](../mcpb/README.md))
- Docs stay aligned with implemented tools and env vars
- Assert/evidence paths support agent retry loops

## 6. References

| Doc | Purpose |
|-----|---------|
| [SAFETY.md](SAFETY.md) | Isolation, opt-in invasive tools |
| [MEMOPS_CUA.md](MEMOPS_CUA.md) | Fleet CUA doctrine |
| [OPERATOR_PROTOCOL.md](OPERATOR_PROTOCOL.md) | Focus during automation |
| [TESTING.md](TESTING.md) | CI vs local |
| **mcp-central-docs** | `patterns/WINDOWS_COMPUTER_USE_MCP_SAFETY.md`, packaging standards |

---

*PRD v0.5.x — computer use agent positioning, assert/dialog/shortcut/task tools, operator app — 2026.*
