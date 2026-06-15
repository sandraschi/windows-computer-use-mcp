# Documentation index

Hub for **windows-computer-use-mcp**. Root overview: [README.md](../README.md). Releases: [CHANGELOG.md](../CHANGELOG.md).

## Core

| Document | Description |
|----------|-------------|
| [PRD.md](PRD.md) | Product requirements |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System diagram and component map |
| [TOOLS.md](TOOLS.md) | Portmanteau MCP tools reference |
| [SAFETY.md](SAFETY.md) | HITL, kill switch, isolation, opt-in invasive tools |
| [TESTING.md](TESTING.md) | CI vs local pytest, hardware markers |
| [DEVELOPMENT.md](DEVELOPMENT.md) | Layout, justfile, CI parity |

## CUA

| Document | Description |
|----------|-------------|
| [MEMOPS_CUA.md](MEMOPS_CUA.md) | Fleet CUA doctrine |
| [CUA_PARITY.md](CUA_PARITY.md) | Parity vs other computer-use stacks |
| [AUTOMATION_ASSERT_SPEC.md](AUTOMATION_ASSERT_SPEC.md) | Assert tool spec |
| [ASSESSMENT_BY_CURSOR_2026-06-14_CUA_NSIS.md](ASSESSMENT_BY_CURSOR_2026-06-14_CUA_NSIS.md) | CUA-NSIS certification canary |

## Fleet cross-links

- **mcp-central-docs** — patterns/WINDOWS_COMPUTER_USE_MCP_SAFETY.md, fleet standards
- **Siblings:** [autohotkey-mcp](https://github.com/sandraschi/autohotkey-mcp), [virtualization-mcp](https://github.com/sandraschi/virtualization-mcp)

**Scope:** Native **desktop** UI only. **Website** automation belongs on a browser MCP (typically Playwright).
