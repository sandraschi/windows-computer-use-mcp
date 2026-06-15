# windows-computer-use-mcp — Claude Code Guide

## Overview
Windows UI automation (PyWinAuto): desktop control — read docs/SAFETY.md; pair with virtualization-mcp for Sandbox/VM isolation. FastMCP 3.2.0 agentic sampling.

## Entry Points
- `uv run windows-computer-use-mcp` → `windows_computer_use_mcp.main:main`

## Standards
- FastMCP 3.2+ portmanteau tool pattern — tools use `operation` enum param
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `AGENTS.md` — OpenAI Codex agent context (if present)
