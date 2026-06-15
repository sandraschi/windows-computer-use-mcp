"""Keyboard input portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Consolidates all keyboard interaction methods (typing, single strikes, hotkeys,
held modifiers) into a single interface. This reduces tool explosion, ensures
consistent input sequencing, and enables atomic keyboard sequences.
Follows FastMCP 3.1 SOTA standards for robust desktop automation.
"""

import logging
import time

from windows_computer_use_mcp.app import app
from windows_computer_use_mcp.keyboard_send import send_hotkey, send_press
from windows_computer_use_mcp.retry import with_retry
from windows_computer_use_mcp.tools.models import KeyboardOperationRequest, ToolResult

logger = logging.getLogger(__name__)


def _hold_keys(modifier: str, target: str) -> None:
    import pyautogui

    with pyautogui.hold(modifier):
        pyautogui.press(target)


if app is not None:

    @app.tool(
        name="automation_keyboard",
        description="""Comprehensive keyboard input and sequence simulation system.

WHAT IT DOES:
This tool provides a unified interface for simulating keyboard input. It supports
sequential typing ('type'), single key presses ('press'), complex multi-key
combinations ('hotkey'), and modifier-key holding ('hold').

WHEN TO USE:
- Use 'type' to enter text into boxes, editors, or command lines.
- Use 'press' for navigation keys (tab, enter, arrows, escape).
- Use 'hotkey' for application shortcuts (ctrl+c, alt+f4, win+r).
- Use 'hold' when you need to sustain a state (like Shift or Ctrl) while performing
  other UI actions.

RECOVERY AND TROUBLESHOOTING:
- If typing appears missing, the window might have lost focus. Use 'automation_windows'
  with 'focus' before sending keyboard input.
- For special keys like 'enter' or 'tab', ensure you are using the correct string
  identifier (pyautogui standard).

RETURNS:
A ToolResult object containing standardized outcome, message, and focus metadata.
""",
    )
    def automation_keyboard(request: KeyboardOperationRequest) -> ToolResult:
        """Unified keyboard input handler."""
        try:
            operation = request.operation
            timestamp = time.time()

            # Focus metadata
            focus_metadata = {
                "timestamp": timestamp,
                "engine": "pywinauto-mcp-sota-2026",
            }

            # === HITL SECURITY CHECK ===
            try:
                from windows_computer_use_mcp.app import approval_state

                if not approval_state.is_approved():
                    action_detail = ""
                    if operation == "type":
                        action_detail = f"Type: '{request.text}'"
                    elif operation == "press":
                        action_detail = f"Press: {request.key}"
                    elif operation == "hotkey":
                        action_detail = f"Hotkey: {'+'.join(request.keys) if request.keys else 'None'}"
                    elif operation == "hold":
                        action_detail = f"Hold sequence: {request.keys}"

                    return ToolResult(
                        status="error",
                        message=f"Blocked by HITL safety setting: keyboard action '{action_detail}' requires human approval. Call approve_automation(duration_minutes=5) first or set WINDOWS_COMPUTER_USE_MCP_BYPASS_HITL=1 for unattended runs.",
                        data={
                            "hitl_prompt": f"Approve keyboard action? [{action_detail}]",
                            "technical_details": request.model_dump(exclude_none=True),
                            "recovery": "Call approve_automation(5) to grant a 5-minute window.",
                        },
                    )
            except ImportError:
                pass

            # === SAFETY / DRY-RUN CHECK ===
            try:
                from windows_computer_use_mcp.safety import before_mutation

                gate = before_mutation(read_only=False)
                if not gate.get("allow"):
                    return ToolResult(status="blocked", message=gate.get("message", "Action blocked."))
                if gate.get("dry_run"):
                    return ToolResult(status="success", message=f"[DRY RUN] Would execute {operation}")
            except ImportError:
                pass

            # === TYPE OPERATION ===
            if operation == "type":
                if request.text is None:
                    return ToolResult(status="error", message="Parameter 'text' is required for typing.")
                import pyautogui

                with_retry(
                    lambda: pyautogui.write(request.text, interval=request.interval),
                    label="keyboard:type",
                )
                return ToolResult(
                    status="success",
                    message=f"Typed {len(request.text)} characters.",
                    data={"text_length": len(request.text), "focus_metadata": focus_metadata},
                )

            # === PRESS OPERATION ===
            elif operation == "press":
                if request.key is None:
                    return ToolResult(status="error", message="Parameter 'key' is required for press.")
                with_retry(
                    lambda: send_press(
                        request.key,
                        hwnd=request.window_handle,
                        presses=request.presses,
                        pause=request.pause,
                    ),
                    label="keyboard:press",
                )
                return ToolResult(status="success", message=f"Pressed '{request.key}' {request.presses} times.")

            # === HOTKEY OPERATION ===
            elif operation == "hotkey":
                if not request.keys:
                    return ToolResult(status="error", message="Parameter 'keys' (list) is required for hotkey.")
                with_retry(
                    lambda: send_hotkey(request.keys, hwnd=request.window_handle, pause=request.pause),
                    label="keyboard:hotkey",
                )
                return ToolResult(status="success", message=f"Triggered hotkey: {'+'.join(request.keys)}")

            # === HOLD OPERATION ===
            elif operation == "hold":
                if not request.keys or len(request.keys) < 2:
                    return ToolResult(status="error", message="'hold' requires at least a modifier and a trigger key.")
                modifier = request.keys[0]
                target = request.keys[-1]
                import pyautogui

                with_retry(
                    lambda: _hold_keys(modifier, target),
                    label="keyboard:hold",
                )
                return ToolResult(status="success", message=f"Executed held operation: {modifier} + {target}")

            return ToolResult(status="error", message=f"Unknown operation: {operation}")

        except Exception as e:
            logger.error(f"Automation keyboard tool error: {e}")
            return ToolResult(
                status="error",
                message=str(e),
                recovery_tip="Check if the target application is responsive and has focus.",
            )

else:
    logger.warning("Keyboard tool not available - missing app instance")


__all__ = ["automation_keyboard"]
