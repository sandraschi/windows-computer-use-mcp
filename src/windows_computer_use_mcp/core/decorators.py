"""Decorators for PyWinAuto MCP tools and functions."""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

# Type variable for generic function typing
F = TypeVar("F", bound=Callable[..., Any])


def tool(
    name: str | None = None,
    description: str | None = None,
    category: str = "general",
    input_model: Any | None = None,
    output_model: Any | None = None,
) -> Callable[[F], F]:
    """Decorator to mark a function as a tool that can be called via MCP.

    Args:
        name: Tool name (defaults to function name)
        description: Tool description
        category: Tool category for organization
        input_model: Pydantic model for input validation
        output_model: Pydantic model for output validation

    """

    def decorator(func: F) -> F:
        # Set tool metadata as function attributes
        func._is_tool = True
        func._tool_name = name or func.__name__
        func._tool_description = description or func.__doc__ or ""
        func._tool_category = category
        func._input_model = input_model
        func._output_model = output_model

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


def stateful(requires_state: bool = True) -> Callable[[F], F]:
    """Decorator to mark a tool as requiring state management.

    Args:
        requires_state: Whether the tool requires state

    """

    def decorator(func: F) -> F:
        func._requires_state = requires_state
        return func

    return decorator
