"""FastMCP application instance for PyWinAuto MCP - Portmanteau Edition.

This module creates the FastMCP app instance to avoid circular imports
between main.py and the tools modules.

FastMCP 3.4+ compliant (Agentic Sampling).
"""

import logging
import os
import time

logger = logging.getLogger(__name__)

try:
    from fastmcp import FastMCP

    logger.info("Successfully imported FastMCP")

    def _package_version() -> str:
        try:
            from importlib.metadata import version

            return version("windows-computer-use-mcp")
        except Exception:
            try:
                from windows_computer_use_mcp import __version__

                return __version__
            except Exception:
                return "0.0.0"

    app = FastMCP(
        name="windows-computer-use-mcp",
        version=_package_version(),
    )

    logger.info("FastMCP 3.4+ app instance created successfully")

except ImportError as e:
    logger.critical(f"Failed to import FastMCP: {e}")
    logger.critical("Please install FastMCP 3.4+ using: pip install fastmcp>=3.4.0")
    app = None
except Exception as e:
    logger.critical(f"Error creating FastMCP app: {e}", exc_info=True)
    app = None

# Check OCR dependencies
try:
    import pytesseract  # noqa: F401
    from PIL import Image, ImageGrab  # noqa: F401

    OCR_AVAILABLE = True
    logger.info("OCR dependencies available")
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("OCR dependencies not available")


# --- HITL SECURITY LAYER ---


class ApprovalState:
    """Manages the Human-in-the-Loop (HITL) approval window for UI automation."""

    def __init__(self):
        self.safe_window_until: float = 0.0

    def is_approved(self) -> bool:
        """Checks if the current action is within a safe approval window or if safety is bypassed."""
        # SOTA 2026: Bypass logic with safety oversight
        bypass_hitl = os.getenv("windows_computer_use_mcp_BYPASS_HITL") in ("1", "true", "yes")
        if bypass_hitl:
            logger.warning("HITL BYPASS ACTIVE: Operating without human approval.")
            # Disable failsafe for bypass mode to ensure demo completion even with minor jitters
            import pyautogui

            pyautogui.FAILSAFE = False
            return True
        return time.time() < self.safe_window_until

    def set_safe_window(self, duration_minutes: float):
        """Sets a safe window for the next N minutes."""
        self.safe_window_until = time.time() + (duration_minutes * 60)

    def clear(self):
        """Clears the approval window immediately."""
        self.safe_window_until = 0.0


# Global approval state instance
approval_state = ApprovalState()


@app.tool()
def approve_automation(duration_minutes: float = 5.0) -> dict:
    """Approve UI automation actions for a specified duration to prevent repetitive prompts.

    Args:
        duration_minutes: Number of minutes to allow automated actions (default 5.0).

    """
    approval_state.set_safe_window(duration_minutes)
    until_str = time.strftime("%H:%M:%S", time.localtime(approval_state.safe_window_until))
    return {
        "status": "success",
        "message": f"UI automation approved until {until_str} ({duration_minutes} minutes)",
        "safe_window_until": approval_state.safe_window_until,
    }


@app.tool()
def automation_safety(
    operation: str = "status",
) -> dict:
    """Inspect or reset server-side safety limits (rate, kill switch, dry-run). Not a substitute for HITL.

    Operations:
    - status: Counters + env flags (windows_computer_use_mcp_KILL_SWITCH, DRY_RUN, MAX_ACTIONS_PER_MINUTE, ENABLE_FACE).
    - reset_counters: Clear rolling window counters (does not disable kill switch).

    See README "Safety" and mcp-central-docs patterns/windows_computer_use_mcp_SAFETY.md.
    """
    from windows_computer_use_mcp.safety import (
        ENV_DRY_RUN,
        ENV_ENABLE_FACE,
        ENV_ENABLE_KEYLOGGER,
        ENV_KILL_SWITCH,
        ENV_MAX_PER_MINUTE,
        get_gate,
        is_face_tool_enabled,
        is_keylogger_tool_enabled,
    )

    gate = get_gate()
    op = (operation or "status").lower().strip()
    if op == "reset_counters":
        gate.reset_window()
        return {
            "status": "success",
            "message": "Rolling action window cleared.",
            "snapshot": gate.snapshot(),
        }
    if op == "status":
        snap = gate.snapshot()
        return {
            "status": "success",
            "snapshot": snap,
            "env": {
                ENV_KILL_SWITCH: os.getenv(ENV_KILL_SWITCH),
                ENV_DRY_RUN: os.getenv(ENV_DRY_RUN),
                ENV_MAX_PER_MINUTE: os.getenv(ENV_MAX_PER_MINUTE),
                ENV_ENABLE_FACE: os.getenv(ENV_ENABLE_FACE),
                ENV_ENABLE_KEYLOGGER: os.getenv(ENV_ENABLE_KEYLOGGER),
            },
            "face_tool_opt_in": is_face_tool_enabled(),
            "keylogger_tool_opt_in": is_keylogger_tool_enabled(),
            "hitl": {"safe_window_until": approval_state.safe_window_until},
        }
    return {
        "status": "error",
        "error": f"Unknown operation: {operation}. Use status or reset_counters.",
    }


# --- SOTA PROMPTS ---


@app.prompt()
def desktop_automation_runbook(app_name: str, task: str) -> str:
    """Standard runbook for automating a desktop application.

    Args:
        app_name: Name of the application to automate.
        task: Description of the goal to achieve.
    """
    return f"""You are a Windows UI automation expert using windows-computer-use-mcp.
Target Application: {app_name}
Goal: {task}

Protocol:
1. Call `automation_windows("find", title="{app_name}")` to locate the window.
2. Call `get_desktop_state()` to analyze the element hierarchy.
3. Call `approve_automation(duration_minutes=5)` before performing any clicks or typing.
4. Execute the automation mission step-by-step, verifying state after each action.
5. If focus is lost, re-activate the window using `automation_windows("focus", handle=HWND)`.

Wait for the application to be ready before each interaction."""


@app.prompt()
def safety_audit_protocol() -> str:
    """Protocol for auditing the server's current safety configuration."""
    return """Review the output of `automation_safety("status")`.
Verify:
1. `DRY_RUN` is appropriately set for the environment.
2. `windows_computer_use_mcp_KILL_SWITCH` is accessible.
3. Rate limits are within safe OS operational boundaries (<= 20 actions/min)."""


# --- SOTA RESOURCES ---


@app.resource("resource://automation/current_state")
def get_current_automation_state() -> str:
    """Dynamic resource providing a snapshot of the current desktop automation environment."""
    return f"""PyWinAuto MCP v0.4.2
HITL Status: {"Active" if approval_state.is_approved() else "Locked"}
OCR Available: {OCR_AVAILABLE}
Timestamp: {time.ctime()}
"""
