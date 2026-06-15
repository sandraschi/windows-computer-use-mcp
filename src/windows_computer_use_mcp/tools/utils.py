"""Common utilities and error handling for PyWinAuto MCP tools."""

import functools
import logging
import time
from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime
from typing import Any, TypeVar

from pydantic import BaseModel, Field
from pywinauto import Desktop

# Initialize logger
logger = logging.getLogger(__name__)

# Type variable for generic function typing
F = TypeVar("F", bound=Callable[..., Any])


class ErrorResponse(BaseModel):
    """Standard error response format."""

    success: bool = Field(False, description="Indicates if the operation was successful")
    error: str = Field(..., description="Error message")
    error_type: str = Field(..., description="Type of error that occurred")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SuccessResponse(BaseModel):
    """Standard success response format."""

    success: bool = Field(True, description="Indicates if the operation was successful")
    data: dict[str, Any] = Field(default_factory=dict, description="Response data")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


def handle_errors[F: Callable[..., Any]](func: F) -> Callable[..., dict[str, Any]]:
    """Decorator to handle errors and standardize responses.

    Args:
        func: The function to wrap

    Returns:
        Wrapped function with error handling

    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        try:
            result = func(*args, **kwargs)

            # If the function already returned a response, return it as-is
            if isinstance(result, dict) and "success" in result:
                return result

            # Otherwise, wrap the result in a success response
            return SuccessResponse(data={"result": result}).dict()

        except Exception as e:
            error_type = e.__class__.__name__
            error_msg = str(e) or "An unknown error occurred"

            # Log the error with full traceback
            # Avoid 'args' key conflict in LogRecord
            log_extra = {
                "error_type": error_type,
                "function": func.__name__,
                "func_args": str(args),
                "kwargs": {k: v for k, v in kwargs.items() if k not in ["password", "api_key"]},
            }
            logger.error(f"Error in {func.__name__}: {error_msg}", exc_info=True, extra=log_extra)

            # Return a standardized error response
            return ErrorResponse(error=error_msg, error_type=error_type).dict()

    return wrapper


def log_execution[F: Callable[..., Any]](func: F) -> Callable[..., Any]:
    """Decorator to log function execution details.

    Args:
        func: The function to wrap

    Returns:
        Wrapped function with execution logging

    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        logger.info(
            f"Starting execution of {func.__name__}",
            extra={
                "function": func.__name__,
                "args": args,
                "kwargs": {k: v for k, v in kwargs.items() if k not in ["password", "api_key"]},
            },
        )

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            logger.info(
                f"Completed {func.__name__} in {duration:.2f} seconds",
                extra={"function": func.__name__, "duration_seconds": duration, "success": True},
            )

            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Error in {func.__name__} after {duration:.2f} seconds: {e!s}",
                exc_info=True,
                extra={
                    "function": func.__name__,
                    "duration_seconds": duration,
                    "success": False,
                    "error": str(e),
                    "error_type": e.__class__.__name__,
                },
            )
            raise

    return wrapper


def register_tool(
    name: str | None = None,
    description: str = "",
    category: str = "general",
    requires_auth: bool = True,
    rate_limited: bool = True,
):
    """Decorator to register a function as a tool with FastMCP.

    This is a compatibility layer that works with FastMCP 2.12's auto-discovery.
    The actual registration happens when the module is imported and the decorator runs.

    Args:
        name: Tool name (defaults to function name)
        description: Tool description
        category: Tool category for organization
        requires_auth: Whether the tool requires authentication
        rate_limited: Whether the tool is rate-limited

    Returns:
        The original function with metadata attached

    """

    def decorator(func: F) -> F:
        # Set function attributes for auto-discovery
        func._is_tool = True
        func._tool_name = name or func.__name__
        func._tool_description = description or func.__doc__ or ""
        func._tool_category = category

        # Apply standard decorators
        wrapped = handle_errors(log_execution(func))

        # Copy function attributes
        wrapped.__name__ = func.__name__
        wrapped.__doc__ = func.__doc__
        wrapped.__module__ = func.__module__
        wrapped._is_tool = func._is_tool
        wrapped._tool_name = func._tool_name
        wrapped._tool_description = func._tool_description
        wrapped._tool_category = func._tool_category

        return wrapped

    return decorator


@contextmanager
def timer(operation: str):
    """Context manager to time a block of code.

    Args:
        operation: Description of the operation being timed

    """
    start_time = time.time()
    logger.debug(f"Starting {operation}")

    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.debug(f"Completed {operation} in {duration:.2f} seconds")


def validate_window_handle(handle: int) -> bool:
    """Validate if a window handle is valid.

    Args:
        handle: Window handle to validate

    Returns:
        bool: True if the handle is valid, False otherwise

    """
    # Desktop imported at top-level

    try:
        window = Desktop(backend="uia").window(handle=handle)
        return window.exists()
    except Exception:
        return False


def get_desktop():
    """Get a Desktop instance with proper error handling."""
    # Desktop imported at top-level

    try:
        return Desktop(backend="uia")
    except Exception as e:
        logger.error(f"Failed to initialize Desktop: {e}", exc_info=True)
        raise RuntimeError("Failed to initialize Windows Desktop automation") from e
