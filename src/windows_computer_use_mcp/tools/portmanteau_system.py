"""System operations portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Instead of creating 7+ separate tools (one per system operation), this tool consolidates related
system operations into a single interface. This design:
- Prevents tool explosion (7+ tools → 1 tool) while maintaining full functionality
- Improves discoverability by grouping related operations together
- Follows FastMCP 2.13+ best practices for feature-rich MCP servers

SUPPORTED OPERATIONS:
- status, help, wait, info, wait_for_window, clipboard_get, clipboard_set, processes, start_app
"""

import logging
import os
import time
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import psutil
import pygetwindow as gw
import pywinauto
from pywinauto import Application

from windows_computer_use_mcp.host_metrics import collect_host_metrics
from windows_computer_use_mcp.safety import (
    is_face_tool_enabled,
)
from windows_computer_use_mcp.tools.models import SystemOperationRequest, ToolResult

try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_system")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_system: {e}")
    app = None

try:
    import pyperclip

    CLIPBOARD_AVAILABLE = True
except ImportError:
    CLIPBOARD_AVAILABLE = False


def _package_version() -> str:
    try:
        return version("pywinauto-mcp")
    except PackageNotFoundError:
        try:
            from windows_computer_use_mcp import __version__ as v

            return str(v)
        except Exception:
            return "unknown"


def _build_help_payload() -> dict[str, Any]:
    """Structured help for automation_system('help')."""
    face_on = is_face_tool_enabled()
    return {
        "server": "pywinauto-mcp",
        "version": _package_version(),
        "description": (
            "Windows UI automation via PyWinAuto (FastMCP). Desktop control is high-privilege; "
            "read docs/SAFETY.md before use."
        ),
        "face_tool_active": face_on,
        "operations": [
            "status",
            "help",
            "wait",
            "info",
            "wait_for_window",
            "clipboard_get",
            "clipboard_set",
            "processes",
            "start_app",
        ],
    }


if app is not None:

    @app.tool(
        name="automation_system",
        description="""Industrialized Windows system utility and synchronization tool.

WHAT IT DOES:
This tool provides low-level system utilities including application launching, process monitoring, clipboard manipulation, and advanced synchronization primitives (e.g., waiting for windows to appear). It acts as the 'glue' for complex automation sequences.

WHEN TO USE:
- Use 'status' for real-time health checks of the MCP server.
- Use 'info' to collect detailed host telemetry (CPU, RAM, GPU).
- Use 'wait' or 'wait_for_window' to synchronize automation steps with OS state.
- Use 'clipboard_get/set' for data transfer between the agent and local applications.
- Use 'processes' and 'start_app' for lifecycle management of Windows software.

RECOVERY:
If 'wait_for_window' times out, verify the 'title' exists or increase 'timeout'. If 'clipboard' operations fail, ensure the 'pyperclip' dependancy is installed and no other app is locking the clipboard.
""",
    )
    def automation_system(request: SystemOperationRequest) -> ToolResult:
        """System helpers: diagnostics, help text, wait, clipboard, process list, start app."""
        try:
            timestamp = time.time()
            operation = request.operation
            seconds = request.seconds
            title = request.title
            timeout = request.timeout
            exact_match = request.exact_match
            text = request.text
            app_path = request.app_path
            work_dir = request.work_dir
            filter_str = request.filter

            system_metadata = {
                "timestamp": timestamp,
                "platform": "windows",
                "identity": "pywinauto-mcp",
            }

            # === STATUS OPERATION ===
            if operation == "status":
                return ToolResult(
                    status="success",
                    message="System status OK.",
                    data={
                        "ready": True,
                        "pywinauto_version": pywinauto.__version__,
                        "system_metadata": system_metadata,
                    },
                )

            # === HELP OPERATION ===
            elif operation == "help":
                help_info = _build_help_payload()
                return ToolResult(status="success", message="System help retrieved.", data=help_info)

            elif operation == "wait":
                if seconds is None:
                    return ToolResult(
                        status="error",
                        message="seconds parameter is required",
                        recovery_tip="Provide the number of seconds to wait.",
                    )
                time.sleep(seconds)
                return ToolResult(
                    status="success",
                    message=f"Waited for {seconds} seconds.",
                    data={"waited_seconds": seconds, "system_metadata": system_metadata},
                )

            elif operation == "telemetry":
                from windows_computer_use_mcp.telemetry import get_failure_patterns, get_stats

                stats = get_stats()
                failures = get_failure_patterns(limit=20)
                return ToolResult(
                    status="success",
                    message=f"Telemetry: {stats.get('total_actions', 0)} actions logged.",
                    data={"stats": stats, "recent_failures": failures},
                )

            elif operation == "analyze_failures":
                from windows_computer_use_mcp.telemetry import analyze_failures

                result = analyze_failures(days=request.timeout or 7)
                cluster_count = result.get("cluster_count", 0)
                return ToolResult(
                    status="success",
                    message=f"Analyzed {cluster_count} failure clusters.",
                    data=result,
                )

            elif operation == "issue_draft":
                from windows_computer_use_mcp.telemetry import generate_issue_draft

                draft = generate_issue_draft(days=int(request.timeout or 7))
                if not draft.get("title"):
                    return ToolResult(status="success", message="No failures to report.", data=draft)
                return ToolResult(
                    status="success",
                    message=f"Issue draft generated: {draft['title'][:80]}",
                    data=draft,
                )

            elif operation == "weekly_report":
                from windows_computer_use_mcp.telemetry import weekly_report

                report = weekly_report()
                return ToolResult(
                    status="success",
                    message=f"Weekly report: {report['total_actions']} actions, {report['fail_rate_pct']}% failure rate.",
                    data=report,
                )

            elif operation == "voice_listen":
                from windows_computer_use_mcp.voice_control import VoiceListener, is_available

                if not is_available():
                    return ToolResult(
                        status="error",
                        message="speech-mcp not reachable at 127.0.0.1:10909.",
                        recovery_tip="Start speech-mcp first or check SPEECH_MCP_URL.",
                    )
                listener = VoiceListener()
                ok = listener.start(duration=int(request.timeout or 5))
                if ok:
                    time.sleep(0.5)
                    return ToolResult(
                        status="success",
                        message="Voice listener started. Will transcribe for up to 5s.",
                        data={"listening": True, "duration": request.timeout or 5},
                    )
                return ToolResult(status="error", message="Voice listener failed to start.")

            elif operation == "voice_status":
                from windows_computer_use_mcp.voice_control import is_available

                return ToolResult(
                    status="success",
                    message="Voice control status.",
                    data={
                        "speech_mcp_available": is_available(),
                        "enabled": os.environ.get("WINDOWS_COMPUTER_USE_MCP_VOICE", "0") in ("1", "true"),
                    },
                )

            elif operation == "info":
                stats = collect_host_metrics()
                return ToolResult(
                    status="success",
                    message="System info collected.",
                    data={"info": stats, "system_metadata": system_metadata},
                )

            elif operation == "wait_for_window":
                if not title:
                    return ToolResult(
                        status="error",
                        message="title parameter is required",
                        recovery_tip="Provide the window title to wait for.",
                    )
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        if exact_match:
                            windows = gw.getWindowsWithTitle(title)
                            window = windows[0] if windows else None
                        else:
                            windows = [w for w in gw.getAllWindows() if title.lower() in w.title.lower()]
                            window = windows[0] if windows else None
                        if window:
                            return ToolResult(
                                status="success",
                                message=f"Window '{title}' found.",
                                data={
                                    "window_title": window.title,
                                    "window_handle": window._hWnd,
                                    "system_metadata": system_metadata,
                                },
                            )
                    except Exception as e:
                        logger.warning(f"Error finding window: {e}")
                    time.sleep(0.5)
                return ToolResult(
                    status="error",
                    message=f"Window '{title}' not found within {timeout}s.",
                    recovery_tip="Check if the window title is correct or increase timeout.",
                )

            elif operation == "clipboard_get":
                if not CLIPBOARD_AVAILABLE:
                    return ToolResult(
                        status="error",
                        message="pyperclip not available.",
                        recovery_tip="Install with: pip install pyperclip",
                    )
                content = pyperclip.paste()
                return ToolResult(
                    status="success",
                    message="Clipboard content retrieved.",
                    data={"content": content, "system_metadata": system_metadata},
                )

            elif operation == "clipboard_set":
                if not CLIPBOARD_AVAILABLE:
                    return ToolResult(
                        status="error",
                        message="pyperclip not available.",
                        recovery_tip="Install with: pip install pyperclip",
                    )
                if text is None:
                    return ToolResult(
                        status="error",
                        message="'text' parameter is required.",
                        recovery_tip="Provide the text string to copy.",
                    )
                pyperclip.copy(text)
                return ToolResult(
                    status="success",
                    message="Text copied to clipboard.",
                    data={"characters_copied": len(text), "system_metadata": system_metadata},
                )

            elif operation == "processes":
                process_list = []
                for proc in psutil.process_iter(["pid", "name", "username", "status", "cpu_percent", "memory_percent"]):
                    try:
                        info = proc.info
                        if filter_str and filter_str.lower() not in info["name"].lower():
                            continue
                        process_list.append(info)
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue
                return ToolResult(
                    status="success",
                    message=f"Found {len(process_list)} processes.",
                    data={"processes": process_list, "system_metadata": system_metadata},
                )

            elif operation == "start_app":
                if not app_path:
                    return ToolResult(
                        status="error",
                        message="app_path parameter is required.",
                        recovery_tip="Provide the path to the application.",
                    )
                try:
                    app_instance = Application().start(app_path, work_dir=work_dir)
                    return ToolResult(
                        status="success",
                        message=f"Started {app_path}.",
                        data={"process_id": app_instance.process, "system_metadata": system_metadata},
                    )
                except Exception as e:
                    return ToolResult(
                        status="error", message=f"Failed to start: {e}", recovery_tip="Check path and permissions."
                    )

            else:
                return ToolResult(
                    status="error",
                    message=f"Unknown operation: {operation}",
                    recovery_tip="Use a valid operation: status, help, wait, info, wait_for_window, clipboard_get, clipboard_set, processes, start_app",
                )

        except Exception as e:
            return ToolResult(status="error", message=str(e), recovery_tip="Check system logs for details.")


__all__ = ["automation_system"]
