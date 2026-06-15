"""Windows Automation API endpoints for PyWinAutoMCP.

This module provides FastAPI routes for core Windows automation functionality,
including window management, element interaction, and input simulation.
"""

import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from pywinauto.application import Application
from pywinauto.findwindows import ElementNotFoundError, find_window

# Configure logging
logger = logging.getLogger(__name__)

# Initialize router with OpenAPI tags
router = APIRouter(tags=["windows"])


# Request/Response Models
class WindowInfo(BaseModel):
    """Information about a window."""

    handle: int = Field(..., description="Window handle")
    title: str = Field(..., description="Window title")
    class_name: str = Field(..., description="Window class name")
    is_visible: bool = Field(..., description="Whether the window is visible")
    is_enabled: bool = Field(..., description="Whether the window is enabled")
    rectangle: dict[str, int] = Field(..., description="Window rectangle (left, top, right, bottom)")
    process_id: int = Field(..., description="Process ID of the window")


class ElementInfo(BaseModel):
    """Information about a UI element."""

    element_type: str = Field(..., description="Type of the UI element")
    name: str = Field(..., description="Name of the element")
    automation_id: str = Field(..., description="Automation ID of the element")
    is_enabled: bool = Field(..., description="Whether the element is enabled")
    is_visible: bool = Field(..., description="Whether the element is visible")
    rectangle: dict[str, int] = Field(..., description="Element rectangle (left, top, right, bottom)")


class ClickRequest(BaseModel):
    """Request model for clicking an element."""

    window_handle: int = Field(..., description="Handle of the window containing the element")
    element_name: str | None = Field(None, description="Name of the element to click")
    element_id: str | None = Field(None, description="Automation ID of the element to click")
    button: str = Field("left", description="Mouse button to use (left, right, middle)")
    double: bool = Field(False, description="Whether to perform a double-click")


class TypeRequest(BaseModel):
    """Request model for typing text."""

    window_handle: int = Field(..., description="Handle of the window to type into")
    text: str = Field(..., description="Text to type")
    element_name: str | None = Field(None, description="Name of the element to type into")
    element_id: str | None = Field(None, description="Automation ID of the element to type into")


# Helper Functions
def _get_window_info(window) -> WindowInfo:
    """Convert a Pywinauto window object to a WindowInfo model."""
    rect = window.rectangle()
    return WindowInfo(
        handle=window.handle,
        title=window.window_text(),
        class_name=window.class_name(),
        is_visible=window.is_visible(),
        is_enabled=window.is_enabled(),
        rectangle={"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom},
        process_id=window.process_id(),
    )


# API Endpoints
@router.get("/find", response_model=list[WindowInfo])
async def find_windows(
    title: str | None = Query(None, description="Window title or part of it (case-insensitive)"),
    class_name: str | None = Query(None, description="Window class name (case-sensitive)"),
    process_id: int | None = Query(None, description="Process ID of the window"),
) -> list[WindowInfo]:
    """Find windows matching the specified criteria.

    Returns a list of windows that match the given title, class name, or process ID.
    At least one search parameter must be provided.
    """
    if not any([title, class_name, process_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one search parameter (title, class_name, or process_id) must be provided",
        )

    try:
        # Build search criteria
        criteria = {}
        if title:
            criteria["title_re"] = ".*" + title + ".*"
        if class_name:
            criteria["class_name"] = class_name
        if process_id:
            criteria["process"] = process_id

        # Find windows
        windows = find_window(**criteria)
        if not windows:
            return []

        # Convert to list if a single window was found
        if not isinstance(windows, list):
            windows = [windows]

        # Get window info for each window
        app = Application().connect(handle=windows[0].handle)
        return [_get_window_info(app.window(handle=w.handle)) for w in windows]

    except ElementNotFoundError:
        return []
    except Exception as e:
        logger.error(f"Error finding windows: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error finding windows: {e!s}",
        )


@router.get("/{window_handle}", response_model=WindowInfo)
async def get_window_info(window_handle: int) -> WindowInfo:
    """Get detailed information about a specific window.

    Args:
        window_handle: Handle of the window to get information about

    Returns:
        WindowInfo: Detailed information about the window

    """
    try:
        app = Application().connect(handle=window_handle)
        window = app.window(handle=window_handle)
        return _get_window_info(window)
    except Exception as e:
        logger.error(f"Error getting window info: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Window not found or error accessing window: {e!s}",
        )


@router.post("/click", status_code=status.HTTP_200_OK)
async def click_element(request: ClickRequest) -> dict[str, str]:
    """Click an element in a window.

    The element can be identified by its name or automation ID.
    """
    if not request.element_name and not request.element_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either element_name or element_id must be provided",
        )

    try:
        app = Application().connect(handle=request.window_handle)
        window = app.window(handle=request.window_handle)

        # Find the element
        element = None
        if request.element_name:
            element = window.child_window(title=request.element_name, control_type="*")
        elif request.element_id:
            element = window.child_window(auto_id=request.element_id, control_type="*")

        if not element.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Element not found in the specified window",
            )

        # Perform the click
        if request.double:
            element.double_click(button=request.button)
        else:
            element.click(button=request.button)

        return {
            "status": "success",
            "message": f"Clicked element: {request.element_name or request.element_id}",
        }

    except Exception as e:
        logger.error(f"Error clicking element: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error clicking element: {e!s}",
        )


@router.post("/type", status_code=status.HTTP_200_OK)
async def type_text(request: TypeRequest) -> dict[str, str]:
    """Type text into a window or a specific element.

    If no element is specified, the text will be sent to the window with focus.
    """
    try:
        app = Application().connect(handle=request.window_handle)
        window = app.window(handle=request.window_handle)

        # If an element is specified, type into it
        if request.element_name or request.element_id:
            if request.element_name:
                element = window.child_window(title=request.element_name, control_type="*")
            else:
                element = window.child_window(auto_id=request.element_id, control_type="*")

            if not element.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Element not found in the specified window",
                )

            element.type_keys(request.text, with_spaces=True)
        else:
            # Otherwise, type into the window
            window.type_keys(request.text, with_spaces=True)

        return {
            "status": "success",
            "message": f"Typed text into {'element' if request.element_name or request.element_id else 'window'}",
        }

    except Exception as e:
        logger.error(f"Error typing text: {e!s}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error typing text: {e!s}")


@router.get("/{window_handle}/elements", response_model=list[ElementInfo])
async def get_window_elements(window_handle: int) -> list[ElementInfo]:
    """Get all child elements of a window.

    This endpoint returns a list of all UI elements in the specified window.
    """
    try:
        app = Application().connect(handle=window_handle)
        window = app.window(handle=window_handle)

        elements = []
        for child in window.children():
            try:
                rect = child.rectangle()
                elements.append(
                    ElementInfo(
                        element_type=child.friendly_class_name(),
                        name=child.window_text(),
                        automation_id=child.element_info.automation_id or "",
                        is_enabled=child.is_enabled(),
                        is_visible=child.is_visible(),
                        rectangle={
                            "left": rect.left,
                            "top": rect.top,
                            "right": rect.right,
                            "bottom": rect.bottom,
                        },
                    )
                )
            except Exception as e:
                logger.warning(f"Error processing child element: {e!s}")
                continue

        return elements

    except Exception as e:
        logger.error(f"Error getting window elements: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting window elements: {e!s}",
        )


@router.post("/{window_handle}/close", status_code=status.HTTP_200_OK)
async def close_window(window_handle: int) -> dict[str, str]:
    """Close a window by its handle.

    This sends a close message to the window, which is the same as clicking the X button.
    The window may prompt the user to save changes before closing.
    """
    try:
        app = Application().connect(handle=window_handle)
        window = app.window(handle=window_handle)
        window.close()
        return {"status": "success", "message": f"Closed window with handle {window_handle}"}
    except Exception as e:
        logger.error(f"Error closing window: {e!s}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error closing window: {e!s}",
        )
