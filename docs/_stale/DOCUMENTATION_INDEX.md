# Documentation index (canonical)

**Start here:** [docs/README.md](README.md) — curated hub for **windows-computer-use-mcp**.

Root overview and install: [README.md](../README.md), [INSTALL.md](../INSTALL.md).

---

## Core (read these)

| Doc | Purpose |
|-----|---------|
| [PRD.md](PRD.md) | Product scope — computer use agent, surfaces, non-goals |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Components, ports, fleet role |
| [TOOLS.md](TOOLS.md) | Portmanteau MCP tools |
| [SAFETY.md](SAFETY.md) | HITL, kill switch, **opt-in** face & keylogger |
| [OPERATOR_PROTOCOL.md](OPERATOR_PROTOCOL.md) | Foreground focus during automation |
| [TESTING.md](TESTING.md) | pytest, CI, hardware markers |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Contributor quick start, layout, justfile |
| [DESKTOP_APP.md](DESKTOP_APP.md) | Tauri operator + PyInstaller sidecar |

## Computer use (CUA)

| Doc | Purpose |
|-----|---------|
| [MEMOPS_CUA.md](MEMOPS_CUA.md) | Fleet doctrine |
| [CUA_ROADMAP.md](CUA_ROADMAP.md) | Closed-loop roadmap |
| [CUA_PARITY.md](CUA_PARITY.md) | Parity notes |
| [AUTOMATION_ASSERT_SPEC.md](AUTOMATION_ASSERT_SPEC.md) | Outcome verification |

## Packaging & ops

| Doc | Purpose |
|-----|---------|
| [mcp-technical/README.md](mcp-technical/README.md) | MCP transport, production checklist |
| [mcpb-packaging/README.md](mcpb-packaging/README.md) | MCPB bundle |
| [../mcpb/README.md](../mcpb/README.md) | Claude Desktop `.mcpb` |

## Scenarios & comparisons

| Doc | Purpose |
|-----|---------|
| [USAGE_SCENARIOS.md](USAGE_SCENARIOS.md) | Example workflows (check opt-in tools) |
| [AHK_VS_PYWINAUTO_COMPARISON.md](AHK_VS_PYWINAUTO_COMPARISON.md) | vs autohotkey-mcp |

---

## Stale or archival material

These paths were copied from other fleet repos or are historical — **do not treat as windows-computer-use-mcp source of truth:**

- [COMPLETE_DOCUMENTATION_STRUCTURE.md](COMPLETE_DOCUMENTATION_STRUCTURE.md) — superseded by this file
- [ORGANIZATION_SUMMARY.md](ORGANIZATION_SUMMARY.md) — Oct 2025 org log; references `notepadpp-mcp`
- [development/](development/README.md) — **archived** notepadpp-mcp imports; canonical: [DEVELOPMENT.md](DEVELOPMENT.md)
- [notepadpp/](notepadpp/README.md) — **Notepad++ editor reference** (automation *target* notes), not this server's API
- [glama-platform/](glama-platform/README.md) — catalog metadata archive
- [serena/](serena/) — unrelated tooling notes

When in doubt, prefer [README.md](../README.md) → [docs/README.md](README.md) → [TOOLS.md](TOOLS.md) / [SAFETY.md](SAFETY.md).
