"""UI Element interaction portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Consolidates all element-level interactions (clicks, text input, discovery) into
a single interface. This reduces tool explosion, ensures consistent selection
logic across control types, and enables atomic UI manipulation sequences.
Follows FastMCP 3.1 SOTA standards for reliable desktop automation.
"""

import logging
import time
from typing import Any, cast

from pywinauto import Desktop
from pywinauto.base_wrapper import ElementNotVisible
from pywinauto.findwindows import ElementNotFoundError

try:
    from pywinauto.controls.uia_controls import ButtonWrapper, ComboBoxWrapper, EditWrapper
except ImportError:
    ButtonWrapper = EditWrapper = ComboBoxWrapper = None

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.dispatch import BACKGROUND_UNAVAILABLE, click_element, resolve_dispatch
from windows_computer_use_mcp.snapshot_store import get_snapshot_store
from windows_computer_use_mcp.tools.models import ElementOperationRequest, ToolResult
from windows_computer_use_mcp.trajectory import log_trajectory
from windows_computer_use_mcp.win32_mouse import (
    ButtonName,
    MouseFailSafeError,
    click,
    double_click,
    move_to,
    right_click,
)

logger = logging.getLogger(__name__)


def _verify_action_result(
    operation: str,
    request: ElementOperationRequest,
    window_handle: int,
    desktop: Any,
) -> dict | None:
    """After a mutating action, verify the outcome. Returns None if OK, or a dict with error info."""
    if not request.verify:
        return None

    try:
        window = desktop.window(handle=window_handle)
        selector = {}
        if request.control_id:
            selector["control_id"] = request.control_id
        if request.auto_id:
            selector["auto_id"] = request.auto_id
        if request.title:
            selector["title"] = request.title
        if request.control_type:
            selector["control_type"] = request.control_type

        if operation == "set_text" and request.verify_text:
            if not selector:
                return {"verify": "no_selector", "detail": "Cannot verify set_text without a selector."}
            elem = window.child_window(**selector)
            if not elem.exists(timeout=3.0):
                return {"verify": "element_gone", "detail": "Element disappeared after set_text."}
            actual = elem.window_text()
            if request.verify_text not in actual:
                return {"verify": "text_mismatch", "expected": request.verify_text, "actual": actual}

        elif operation in ("click", "double_click", "right_click"):
            if request.verify_text:
                from windows_computer_use_mcp.assert_engine import assert_text_in_image

                try:
                    from windows_computer_use_mcp.win32_window import get_window_bbox

                    bbox = get_window_bbox(window_handle)
                    region = (bbox.left, bbox.top, bbox.right, bbox.bottom)
                except Exception:
                    region = None

                ok, actual_text = assert_text_in_image(
                    image_path=None,
                    expected_text=request.verify_text,
                    exact_match=False,
                    window_handle=window_handle,
                )
                if not ok:
                    return {"verify": "text_not_found", "expected": request.verify_text, "actual": actual_text}

            else:
                time.sleep(0.5)
                if selector:
                    elem = window.child_window(**selector)
                    if not elem.exists(timeout=2.0):
                        return {"verify": "element_gone", "detail": "Clicked element no longer exists."}

    except Exception as e:
        logger.warning("verify_action_result failed: %s", e)
        return {"verify": "error", "detail": str(e)}

    return None


def _get_desktop():
    """Get a Desktop instance with proper error handling."""
    try:
        return Desktop(backend="uia")
    except Exception as e:
        logger.error(f"Failed to get Desktop instance: {e}")
        raise


def _get_element_info(element) -> dict[str, Any]:
    """Extract relevant information from a UI element."""
    info = {}
    try:
        info = {
            "class_name": element.class_name(),
            "text": element.window_text(),
            "control_id": element.control_id() if hasattr(element, "control_id") else None,
            "process_id": element.process_id(),
            "is_visible": element.is_visible(),
            "is_enabled": element.is_enabled(),
            "handle": element.handle,
        }

        if hasattr(element, "automation_id"):
            info["automation_id"] = element.automation_id()

        if hasattr(element, "element_info"):
            info["name"] = element.element_info.name
            info["control_type"] = str(element.element_info.control_type)

        try:
            rect = element.rectangle()
            info["rect"] = {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.width(),
                "height": rect.height(),
            }
            info["x"] = rect.left
            info["y"] = rect.top
            info["width"] = rect.width()
            info["height"] = rect.height()
        except Exception:
            pass

        # Element type detection
        if ButtonWrapper and isinstance(element, ButtonWrapper):
            info["element_type"] = "button"
        elif EditWrapper and isinstance(element, EditWrapper):
            info["element_type"] = "edit"
            try:
                info["is_readonly"] = element.is_read_only()
            except Exception:
                pass
        elif ComboBoxWrapper and isinstance(element, ComboBoxWrapper):
            info["element_type"] = "combobox"
            try:
                info["items"] = element.item_texts()
                info["selected_index"] = element.selected_index()
                info["selected_text"] = element.selected_text()
            except Exception:
                pass

    except Exception as e:
        logger.warning(f"Error getting element info: {e}")

    return info


def _operate_snapshot_element(
    request: ElementOperationRequest, snap_elem: dict, desktop
) -> ToolResult:
    """Resolve snapshot element_index to a control or coordinate click."""
    operation = request.operation
    window_handle = request.window_handle
    dispatch = resolve_dispatch(request.dispatch)
    bounds = snap_elem.get("bounds") or {}
    name = snap_elem.get("name") or ""
    class_name = snap_elem.get("class_name")
    control_type = snap_elem.get("type")

    selector: dict = {}
    if class_name:
        selector["class_name"] = class_name
    if name:
        selector["title"] = name
    if control_type:
        selector["control_type"] = control_type

    try:
        window = desktop.window(handle=window_handle)
        element = None
        if selector:
            try:
                element = window.child_window(**selector)
                if not element.exists(timeout=min(request.timeout, 3.0)):
                    element = None
            except Exception:
                element = None

            if operation in ("click", "double_click", "right_click") and element is not None:
                meta = click_element(
                    element,
                    dispatch=dispatch,
                    button=request.button,
                    double=(operation == "double_click"),
                    window_handle=window_handle,
                )
                if request.verify:
                    verify_info = _verify_action_result(operation, request, window_handle, desktop)
                    if verify_info:
                        meta["verify"] = verify_info
            log_trajectory(
                "element_click",
                snapshot_id=request.snapshot_id,
                element_index=request.element_index,
                operation=operation,
                dispatch=dispatch,
                meta=meta,
            )
            if meta.get("code") == BACKGROUND_UNAVAILABLE:
                return ToolResult(
                    status="blocked",
                    message="Background click unavailable for this control.",
                    data=meta,
                    recovery_tip='Retry with dispatch="foreground" if the app requires focus.',
                )
            if operation == "right_click" and meta.get("method") not in ("postmessage",):
                try:
                    element.click(button="right")
                except Exception:
                    pass
            return ToolResult(
                status="success",
                message=f"Snapshot {operation} via {meta.get('method')} ({meta.get('dispatch')})",
                data={"element_index": request.element_index, **meta},
            )

        x = bounds.get("x", 0) + bounds.get("width", 0) // 2
        y = bounds.get("y", 0) + bounds.get("height", 0) // 2
        btn = cast(ButtonName, request.button)
        if operation == "click":
            click(int(x), int(y), button=btn, clicks=1)
        elif operation == "double_click":
            double_click(int(x), int(y), button=btn)
        elif operation == "right_click":
            right_click(int(x), int(y))
        elif operation == "hover":
            move_to(int(x), int(y), duration=0.3)
            time.sleep(request.duration)
            return ToolResult(status="success", message="Hovered snapshot element.", data={"x": x, "y": y})
        elif operation == "set_text" and element is not None and request.text is not None:
            element.set_focus()
            element.set_text(request.text)
            verify_info = _verify_action_result(operation, request, window_handle, desktop)
            if verify_info:
                return ToolResult(
                    status="blocked",
                    message=f"set_text on snapshot element but verification failed: {verify_info.get('detail', '')}",
                    data={"verify": verify_info},
                )
            return ToolResult(status="success", message="Text set on snapshot element.")
        else:
            return ToolResult(
                status="error",
                message=f"Operation '{operation}' not supported via snapshot for this element.",
                recovery_tip="Use click/hover/set_text or refresh snapshot with capture_mode=som.",
            )
        return ToolResult(
            status="success",
            message=f"Snapshot {operation} at ({x},{y})",
            data={"x": x, "y": y, "dispatch": dispatch, "coordinate_fallback": True},
        )
    except MouseFailSafeError as e:
        return ToolResult(status="blocked", message=str(e))
    except Exception as e:
        return ToolResult(status="error", message=f"Snapshot operation failed: {e!s}")


if app is not None:

    @app.tool(
        name="automation_elements",
        description="""Comprehensive UI element interaction and inspection system.

WHAT IT DOES:
This tool provides granular control over individual UI elements (buttons, text fields,
lists, etc.) within a target window. It handles complex selection logic based on
Control IDs, Automation IDs, titles, or relative coordinates, and executes actions
like clicking, typing, and visibility verification.

WHEN TO USE:
- Use 'list' to browse the element tree of a window to find interactable controls.
- Use 'click' or 'double_click' to trigger UI actions on specific buttons or items.
- Use 'set_text' to fill out forms, enter search queries, or update field values.
- Use 'wait' or 'exists' when automating dynamic UIs where elements take time to load.
- Use 'info' to audit a control's properties (enabled state, read-only status, etc.).

RECOVERY AND TROUBLESHOOTING:
- 'ElementNotFoundError': The selection criteria (control_id, title) may be incorrect or
  the element might be nested deeper than expected. Use 'list' with a higher 'max_depth'
  to verify the exact hierarchy.
- 'ElementNotVisible': The element exists but is hidden or scrolled out of view.
  Try 'activate' on the parent window first, or use mouse tools to scroll.
- Ambiguous targets: If multiple elements match your criteria, PyWinAuto might fail.
  Be as specific as possible by combining 'control_type' and 'title'.

RETURNS:
A ToolResult object containing standardized outcome, message, and element data.
""",
    )
    def automation_elements(request: ElementOperationRequest) -> ToolResult:
        """Unified UI element interaction handler."""
        try:
            operation = request.operation
            window_handle = request.window_handle
            time.time()
            desktop = _get_desktop()

            _MUTATING = {
                "click",
                "double_click",
                "right_click",
                "set_text",
            }
            if operation in _MUTATING:
                try:
                    from windows_computer_use_mcp.safety import before_mutation

                    gate = before_mutation(read_only=False)
                    if not gate.get("allow"):
                        return ToolResult(status="blocked", message=gate.get("message", "Action blocked."))
                    if gate.get("dry_run"):
                        return ToolResult(status="success", message=f"[DRY RUN] Would execute {operation}")
                except ImportError:
                    pass

            # === SNAPSHOT INDEX (Cua-style) ===
            if request.snapshot_id is not None and request.element_index is not None:
                snap = get_snapshot_store().get(request.snapshot_id)
                if snap is None:
                    return ToolResult(
                        status="error",
                        message=f"Unknown snapshot_id: {request.snapshot_id}",
                        recovery_tip="Call get_window_state again to refresh snapshot_id.",
                    )
                if snap.window_handle != window_handle:
                    return ToolResult(
                        status="error",
                        message="window_handle does not match snapshot window_handle.",
                        recovery_tip=f"Use window_handle={snap.window_handle} for this snapshot.",
                    )
                snap_elem = get_snapshot_store().resolve_element(
                    request.snapshot_id, request.element_index
                )
                if snap_elem is None:
                    return ToolResult(
                        status="error",
                        message=f"element_index {request.element_index} not in snapshot.",
                        recovery_tip="Re-run get_window_state and use an index from elements[].",
                    )
                return _operate_snapshot_element(request, snap_elem, desktop)

            # === LIST OPERATION ===
            if operation == "list":
                try:
                    window = desktop.window(handle=window_handle)
                except Exception:
                    return ToolResult(
                        status="error",
                        message=f"Window with handle {window_handle} not found.",
                        recovery_tip="Use 'automation_windows' to list active windows and verify the handle.",
                    )

                def get_children_recursive(elem, depth=0):
                    if depth > request.max_depth:
                        return []
                    elements = []
                    try:
                        for child in elem.children():
                            elem_info = _get_element_info(child)
                            elem_info["children"] = get_children_recursive(child, depth + 1)
                            elements.append(elem_info)
                    except Exception:
                        pass
                    return elements

                elements = get_children_recursive(window)
                return ToolResult(
                    status="success",
                    message=f"Discovered {len(elements)} top-level elements.",
                    data={"window_handle": window_handle, "elements": elements},
                )

            # === SELECTOR CONSTRUCTION ===
            selector = {}
            if request.control_id:
                selector["control_id"] = request.control_id
            if request.auto_id:
                selector["auto_id"] = request.auto_id
            if request.title:
                selector["title"] = request.title
            if request.control_type:
                selector["control_type"] = request.control_type
            if request.class_name:
                selector["class_name"] = request.class_name

            # === COORDINATE FALLBACK ===
            if not selector and (request.x is not None and request.y is not None):
                try:
                    window = desktop.window(handle=window_handle)
                    x, y = request.x, request.y
                    if not request.absolute:
                        rect = window.rectangle()
                        x += rect.left
                        y += rect.top

                    btn = cast(ButtonName, request.button)
                    if operation == "click":
                        click(int(x), int(y), button=btn, clicks=1)
                    elif operation == "double_click":
                        double_click(int(x), int(y), button=btn)
                    elif operation == "right_click":
                        right_click(int(x), int(y))
                    elif operation == "hover":
                        move_to(int(x), int(y), duration=0.3)
                        time.sleep(request.duration)
                    else:
                        return ToolResult(
                            status="error",
                            message=f"Operation '{operation}' cannot be performed by coordinates alone.",
                            recovery_tip="Use a selector (control_id, title) to identify the specific element.",
                        )

                    verify_info = _verify_action_result(operation, request, window_handle, desktop)
                    if verify_info:
                        return ToolResult(
                            status="blocked",
                            message=f"{operation} at ({x},{y}) but verification failed: {verify_info.get('detail', '')}",
                            data={"verify": verify_info},
                        )
                    return ToolResult(
                        status="success",
                        message=f"Performed {operation} at ({x}, {y})",
                        data={"x": x, "y": y, "absolute": True},
                    )
                except MouseFailSafeError as e:
                    return ToolResult(status="blocked", message=str(e))
                except Exception as e:
                    return ToolResult(status="error", message=f"Coordinate operation failed: {e}")

            # === SELECTOR-BASED OPERATIONS ===
            if not selector:
                return ToolResult(
                    status="error",
                    message="Missing selection criteria (control_id, auto_id, title) or coordinates (x, y).",
                    recovery_tip="Provide an identifier for the element or specific coordinates.",
                )

            try:
                window = desktop.window(handle=window_handle)
                element = window.child_window(**selector)

                # Check existence with timeout
                if not element.exists(timeout=request.timeout):
                    return ToolResult(
                        status="error",
                        message=f"Element not found using criteria: {selector}",
                        recovery_tip="Increase 'timeout' or verify the selectors using the 'list' operation.",
                    )

                if operation == "exists":
                    return ToolResult(status="success", message="Element exists.", data={"exists": True})

                if operation == "wait":
                    return ToolResult(status="success", message="Element appeared.", data=_get_element_info(element))

                if operation in ["click", "double_click", "right_click"]:
                    if operation == "click":
                        element.click(button=request.button)
                    elif operation == "double_click":
                        element.double_click(button=request.button)
                    elif operation == "right_click":
                        element.click(button="right")
                    verify_info = _verify_action_result(operation, request, window_handle, desktop)
                    if verify_info:
                        return ToolResult(
                            status="blocked",
                            message=f"{operation} executed but verification failed: {verify_info.get('detail', '')}",
                            data={"verify": verify_info},
                        )
                    return ToolResult(status="success", message=f"Executed {operation} on control.")

                elif operation == "hover":
                    rect = element.rectangle()
                    cx, cy = rect.left + (rect.width() // 2), rect.top + (rect.height() // 2)
                    move_to(cx, cy, duration=0.3)
                    time.sleep(request.duration)
                    return ToolResult(status="success", message="Hovered over control.")

                elif operation == "info":
                    return ToolResult(status="success", message="Metadata retrieved.", data=_get_element_info(element))

                elif operation == "get_text":
                    val = element.window_text()
                    return ToolResult(status="success", message=f"Retrieved text: {val}", data={"text": val})

                elif operation == "set_text":
                    if request.text is None:
                        return ToolResult(status="error", message="Parameter 'text' is required for 'set_text'.")
                    try:
                        element.set_text(request.text)
                        method = "direct"
                    except Exception:
                        element.set_focus()
                        element.type_keys("^a{DELETE}")
                        element.type_keys(request.text, with_spaces=True)
                        method = "type_keys"
                    verify_info = _verify_action_result(operation, request, window_handle, desktop)
                    if verify_info:
                        return ToolResult(
                            status="blocked",
                            message=f"set_text executed but verification failed: {verify_info.get('detail', '')}",
                            data={"verify": verify_info},
                        )
                    return ToolResult(status="success", message=f"Text set via {method}.", data={"method": method})

                elif operation == "rect":
                    rect = element.rectangle()
                    return ToolResult(
                        status="success",
                        message="Coordinates retrieved.",
                        data={
                            "left": rect.left,
                            "top": rect.top,
                            "right": rect.right,
                            "bottom": rect.bottom,
                            "width": rect.width(),
                            "height": rect.height(),
                        },
                    )

                elif operation == "visible":
                    res = element.is_visible()
                    return ToolResult(status="success", message=f"Visible: {res}", data={"visible": res})

                elif operation == "enabled":
                    res = element.is_enabled()
                    return ToolResult(status="success", message=f"Enabled: {res}", data={"enabled": res})

                elif operation == "verify_text":
                    if request.expected_text is None:
                        return ToolResult(status="error", message="'expected_text' is required.")
                    actual = element.window_text()
                    match = (
                        (actual == request.expected_text)
                        if request.exact_match
                        else (request.expected_text.lower() in actual.lower())
                    )
                    return ToolResult(
                        status="success" if match else "error",
                        message="Text verification " + ("passed" if match else "failed"),
                        data={"expected": request.expected_text, "actual": actual},
                    )

                return ToolResult(status="error", message=f"Unknown operation: {operation}")

            except ElementNotFoundError:
                return ToolResult(status="error", message="Element not found (after existence check).")
            except ElementNotVisible:
                return ToolResult(
                    status="error", message="Element not visible.", recovery_tip="Try activating the window first."
                )
            except MouseFailSafeError as e:
                return ToolResult(
                    status="blocked",
                    message=str(e),
                    recovery_tip="Cursor hit upper-left failsafe; use windows_computer_use_mcp_BYPASS_HITL=1 for trusted runs.",
                )
            except Exception as e:
                return ToolResult(status="error", message=f"Element operation failed: {e}")

        except Exception as e:
            logger.error(f"Automation elements tool error: {e}")
            return ToolResult(status="error", message=str(e), recovery_tip="Check if the window handle is still valid.")

else:
    logger.warning("Elements tool not available - missing app instance")


__all__ = ["automation_elements"]
