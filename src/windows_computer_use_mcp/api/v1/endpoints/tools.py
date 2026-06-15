"""MCP Tools API endpoints for PyWinAutoMCP.

This module provides FastAPI routes for discovering and executing MCP tools
directly from the webapp, enabling real application control.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

# Use absolute import to match windows_computer_use_mcp structure
from windows_computer_use_mcp.app import app

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router with OpenAPI tags
router = APIRouter(tags=["tools"])


# Request/Response Models
class ToolParameter(BaseModel):
    """Information about a tool parameter."""

    name: str
    type: str
    description: str | None = None
    default: Any | None = None
    required: bool = True


class ToolInfo(BaseModel):
    """Information about an MCP tool."""

    name: str = Field(..., description="Unique tool name")
    description: str = Field(..., description="Human-readable description")
    parameters: list[ToolParameter] = Field(default_factory=list, description="List of tool parameters")


class ToolCallRequest(BaseModel):
    """Request model for calling an MCP tool."""

    name: str = Field(..., description="Name of the tool to call")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Arguments to pass to the tool")


class ToolCallResponse(BaseModel):
    """Response model for a tool call."""

    status: str = Field(..., description="Status of the tool call (success/error)")
    result: Any = Field(None, description="Result of the tool call")
    message: str | None = Field(None, description="Optional status message")


# API Endpoints
@router.get("/", response_model=list[ToolInfo])
async def list_tools() -> list[ToolInfo]:
    """List all registered MCP tools for this server.

    This enables the webapp to dynamically discover available functionality.
    """
    try:
        if not app:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="FastMCP app not initialized",
            )

        # FastMCP 2.13+: list_tools is async; _tool_manager may be absent.
        registered = await app.list_tools()

        tools: list[ToolInfo] = []
        for tool in registered:
            params: list[ToolParameter] = []
            raw = getattr(tool, "parameters", None) or {}
            if not isinstance(raw, dict):
                raw = {}
            schema = raw.get("properties") or {}
            required_list = set(raw.get("required") or [])

            for p_name, p_info in schema.items():
                if not isinstance(p_info, dict):
                    p_info = {}
                params.append(
                    ToolParameter(
                        name=p_name,
                        type=str(p_info.get("type", "any")),
                        description=p_info.get("description"),
                        default=p_info.get("default"),
                        required=p_name in required_list,
                    )
                )

            tools.append(
                ToolInfo(
                    name=str(getattr(tool, "name", "")),
                    description=str(getattr(tool, "description", "") or ""),
                    parameters=params,
                )
            )

        return tools

    except Exception as e:
        logger.error(f"Error listing tools: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tools: {e!s}",
        )


@router.post("/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest) -> ToolCallResponse:
    """Execute a registered MCP tool.

    This provides a direct bridge for the webapp to perform real-world actions.
    """
    try:
        if not app:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="FastMCP app not initialized",
            )

        logger.info(f"Calling tool via API: {request.name} with args: {request.arguments}")

        # Execute the tool using app.call_tool (FastMCP standard)
        result = await app.call_tool(request.name, request.arguments)

        return ToolCallResponse(status="success", result=result, message=f"Tool {request.name} executed successfully")

    except ValueError as e:
        # Usually tool not found or invalid arguments
        logger.warning(f"Validation error calling tool {request.name}: {e!s}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error calling tool {request.name}: {e!s}", exc_info=True)
        return ToolCallResponse(status="error", message=str(e))
