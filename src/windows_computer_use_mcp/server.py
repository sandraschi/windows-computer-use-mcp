"""ASGI entry: REST API (`/api/v1/...`) + FastMCP streamable HTTP (`/mcp`).

Uvicorn target: ``windows_computer_use_mcp.server:app``
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from windows_computer_use_mcp.api import api_router
from windows_computer_use_mcp.app import app as mcp_app

# FastMCP HTTP app only registers ``/mcp``; mount it after REST routes so ``/api/v1/*`` resolves.
_mcp_http = mcp_app.http_app()

app = FastAPI(title="windows-computer-use-mcp", version="0.5.4")

_cors_origins = [
    "http://127.0.0.1:10788",
    "http://localhost:10788",
    "http://127.0.0.1:10706",
    "http://localhost:10706",
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
app.include_router(api_router)
app.mount("/", _mcp_http)
