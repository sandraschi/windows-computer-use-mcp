# Documentation index

Hub for **windows-computer-use-mcp** — the fleet's Windows **computer use agent**. Root overview: [README.md](../README.md) (includes **Python stack** and **opt-in invasive tools**). Releases: [CHANGELOG.md](../CHANGELOG.md).

**Canonical map:** [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) — lists stale/archival folders (`notepadpp/`, old `COMPLETE_DOCUMENTATION_STRUCTURE.md`, etc.).

## Core

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Product requirements — CUA positioning, tools, web stack |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagram and component map |
| [TOOLS.md](TOOLS.md) | Portmanteau MCP tools reference |
| [SAFETY.md](SAFETY.md) | HITL, kill switch, isolation, dual-use, opt-in invasive tools |
| [OPERATOR_PROTOCOL.md](OPERATOR_PROTOCOL.md) | Foreground / focus during automation |
| [TESTING.md](TESTING.md) | CI vs local pytest, markers |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Layout, justfile, CI parity |
| [DESKTOP_APP.md](DESKTOP_APP.md) | Tauri operator installer architecture |

## Computer use (CUA)

| Document | Description |
|----------|-------------|
| [MEMOPS_CUA.md](MEMOPS_CUA.md) | Fleet doctrine — hands, not brain |
| [CUA_ROADMAP.md](CUA_ROADMAP.md) | Closed-loop assistant roadmap |
| [CUA_PARITY.md](CUA_PARITY.md) | Parity notes vs other computer-use stacks |
| [AUTOMATION_ASSERT_SPEC.md](AUTOMATION_ASSERT_SPEC.md) | Outcome verification / assert tool |
| [LLM_REPO_CONTEXT.md](LLM_REPO_CONTEXT.md) | Web chat repo-knowledge source pointer |

## Comparisons & scenarios

| Document | Description |
|----------|-------------|
| [AHK_VS_PYWINAUTO_COMPARISON.md](AHK_VS_PYWINAUTO_COMPARISON.md) | vs [autohotkey-mcp](https://github.com/sandraschi/autohotkey-mcp) |
| [USAGE_SCENARIOS.md](USAGE_SCENARIOS.md) | Example operator workflows |

## Sub-readmes (deep dives)

| Directory | Topic |
|-----------|--------|
| [mcp-technical/](mcp-technical/README.md) | Transport, production checklist, troubleshooting |
| [mcpb-packaging/](mcpb-packaging/README.md) | MCPB build and distribution |
| [development/](development/README.md) | Archived fleet imports → use [DEVELOPMENT.md](DEVELOPMENT.md) |
| [glama-platform/](glama-platform/README.md) | Glama.ai catalog metadata |
| [repository-protection/](repository-protection/README.md) | Branch protection and backups |

## Fleet cross-links

- **mcp-central-docs** — `patterns/WINDOWS_COMPUTER_USE_MCP_SAFETY.md`, `standards/testing-environment-aware.md`, `standards/MCPB_PACKAGING_STANDARDS.md`
- **Sibling:** [autohotkey-mcp](https://github.com/sandraschi/autohotkey-mcp) — AHK scriptlets (orthogonal to native UI here)

**Scope:** Native **desktop** UI only. **Website** automation belongs on a browser MCP (typically Playwright).
