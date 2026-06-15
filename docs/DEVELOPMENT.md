# Development

**Version:** `pyproject.toml` → `[project] version` (currently 0.5.x).

## Quick start

```powershell
uv sync
just install          # same as uv sync
just start            # web_sota + API (10788 / 10789)
just dev              # API only with reload
```

## Quality gate (matches CI)

```powershell
uv run ruff check src tests
uv run pytest tests -q -m "not e2e and not slow"
```

With `CI=true`, hardware and destructive tests are skipped automatically — see [TESTING.md](TESTING.md).

## Layout

| Path | Purpose |
|------|---------|
| `src/windows_computer_use_mcp/` | FastMCP server, portmanteau tools, safety gates |
| `web_sota/` | Vite operator UI + FastAPI routes |
| `web_sota/src-tauri/` | Tauri 2 desktop shell (port **10789** backend) |
| `mcpb/` | Claude Desktop bundle staging |
| `tests/` | pytest (unit + optional hardware/e2e) |
| `examples/` | Local demos (`just demo`, `just paint-demo`) |

## Common recipes

```powershell
just --list
just mcpb-pack
just demo
```

Tauri installer: `uv sync --extra desktop`, then `npm run tauri:build` from `web_sota/` (see [DESKTOP_APP.md](DESKTOP_APP.md)).

## Fleet references

- **mcp-central-docs** — `standards/testing-environment-aware.md`, `patterns/WINDOWS_COMPUTER_USE_MCP_SAFETY.md`, `standards/MCPB_PACKAGING_STANDARDS.md`
- **Sibling:** [autohotkey-mcp](https://github.com/sandraschi/autohotkey-mcp) — hotkey scriptlets, not native UIA

## Historical dev notes

Fleet-imported contributor dumps (notepadpp-mcp era) live under [development/archive/](development/archive/README.md) — **do not** treat as current guidance.
