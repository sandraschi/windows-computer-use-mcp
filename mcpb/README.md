# windows-computer-use-mcp — MCPB bundle root

Pack root for **`mcpb pack`** (Claude Desktop **`.mcpb`**). Ships the Windows **computer use agent** MCP server.

## Fleet standard

Follow **[MCPB_PACKAGING_STANDARDS](https://github.com/sandraschi/mcp-central-docs/blob/master/standards/MCPB_PACKAGING_STANDARDS.md)** and **[PACKAGING_STANDARDS §5](https://github.com/sandraschi/mcp-central-docs/blob/master/standards/PACKAGING_STANDARDS.md#5-python-mcp-repo-uv-justfile-llmstxt-glama-mcpb-pack)**:

- `manifest.json` (v0.2), `assets/` (icon when present)
- **Do not** use `mcpb init` / `mcpb create` (forbidden by fleet standard)
- **`glama.json`** stays at **repository root** only
- Install Python deps from the **repository** with **`uv sync`** after clone — see [INSTALL.md](../INSTALL.md)

## manifest.json

| Field | Value |
|-------|--------|
| `name` | `windows-computer-use-mcp` |
| `version` | Matches `pyproject.toml` (currently **0.5.3**) |
| `entry_point` | `src/windows_computer_use_mcp/main.py` |
| `description` | Windows computer use agent — read [docs/SAFETY.md](../docs/SAFETY.md) first |

## Build

From repository root (PowerShell):

```powershell
.\scripts\build-mcpb-package.ps1 -NoSign
```

Output: `dist\windows-computer-use-mcp.mcpb`

Requires MCPB CLI: `npm install -g @anthropic-ai/mcpb` (or `just mcpb-pack`)

## Install (end user)

1. Build or download `windows-computer-use-mcp.mcpb`
2. Drag into Claude Desktop **Settings → MCP → Install from file**
3. On Windows, approve desktop automation only on machines you control
4. Read [docs/SAFETY.md](../docs/SAFETY.md) — HITL defaults apply to mouse/keyboard

## Deep guide

Full build troubleshooting: [docs/mcpb-packaging/MCPB_BUILDING_GUIDE.md](../docs/mcpb-packaging/MCPB_BUILDING_GUIDE.md)
