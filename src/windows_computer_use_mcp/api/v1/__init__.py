"""API v1 Router for PyWinAutoMCP.

This module contains all API routes for version 1 of the PyWinAutoMCP API.
"""

from fastapi import APIRouter

# Import all endpoint modules
from windows_computer_use_mcp.api.v1.endpoints import (
    cameras,
    diagnostics,
    evidence,
    health,
    llm,
    safety,
    system,
    tools,
    windows,
)

# Create the API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(safety.router, prefix="/safety", tags=["safety"])
api_router.include_router(windows.router, prefix="/windows", tags=["windows"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])
api_router.include_router(diagnostics.router, tags=["diagnostics"])
api_router.include_router(evidence.router, tags=["evidence"])
