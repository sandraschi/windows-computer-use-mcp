"""API package for PyWinAutoMCP.

This package contains all API routes and endpoints for the PyWinAutoMCP server.
"""

from fastapi import APIRouter

from windows_computer_use_mcp.api.llm import router as llm_router

# Import API routers
from windows_computer_use_mcp.api.v1 import api_router as v1_router

# Create the main API router
api_router = APIRouter()

# Include all API version routers
api_router.include_router(v1_router, prefix="/api/v1")
api_router.include_router(llm_router)
