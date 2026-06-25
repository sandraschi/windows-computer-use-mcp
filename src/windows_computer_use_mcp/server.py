"""ASGI entry: REST API (`/api/v1/...`) + FastMCP streamable HTTP (`/mcp`).

Uvicorn target: ``windows_computer_use_mcp.server:app``

CLI (uvicorn-based HTTP with full REST API):
    python -m windows_computer_use_mcp.server [--port PORT]

Legacy CLI (pure FastMCP, no REST):
    python -m windows_computer_use_mcp.main --http --port PORT
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from windows_computer_use_mcp.api import api_router
from windows_computer_use_mcp.app import app as mcp_app

# FastMCP HTTP app serves the MCP protocol on /mcp
_mcp_http = mcp_app.http_app()

app = FastAPI(title="windows-computer-use-mcp", version="0.5.4")

_cors_origins = [
    "http://127.0.0.1:10788",
    "http://localhost:10788",
    "http://goliath:10788",
    "http://127.0.0.1:10706",
    "http://localhost:10706",
    "http://goliath:10706",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "tauri://localhost",
]
_tauri_desktop = os.environ.get("PYWINAUTO_TAURI", "").lower() in ("1", "true", "yes")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=r"https?://tauri\.localhost(:\d+)?" if _tauri_desktop else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API router — serves /api/v1/health, /api/v1/diagnostics, etc.
app.include_router(api_router)

# FastMCP streamable HTTP endpoint — serves MCP protocol on /mcp
app.mount("/mcp", _mcp_http)

# Legacy: also mount at root for backward compat (MCP clients that expect /)
app.mount("/", _mcp_http)


def main() -> None:
    """Start the FastAPI ASGI server with uvicorn (REST + MCP on /mcp)."""
    import uvicorn

    port = int(os.environ.get("MCP_PORT", os.environ.get("PORT", "10789")))
    host = os.environ.get("MCP_HOST", os.environ.get("HOST", "127.0.0.1"))
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
