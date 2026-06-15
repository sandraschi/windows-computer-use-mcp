"""PyWinAuto MCP — Windows UI automation server (FastMCP).

Started and stopped by the MCP host (stdio or HTTP transport).
"""

import logging
import logging.config
import sys

from .transport import run_server

# Configure logging before other imports to ensure proper logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler("pywinauto-mcp.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)

# Import the FastMCP app instance
try:
    from windows_computer_use_mcp.app import OCR_AVAILABLE, app

    logger.info("Successfully imported FastMCP app instance")

    if app is None:
        logger.critical("FastMCP app instance is None - cannot continue")
        sys.exit(1)

    # Import portmanteau tools - this triggers their registration with FastMCP
    try:
        from windows_computer_use_mcp import tools  # noqa: F401

        logger.info("Successfully imported portmanteau tools")
        try:
            from windows_computer_use_mcp import prompts  # noqa: F401

            logger.info("Successfully imported MCP prompts")
        except Exception as e:
            logger.warning("Prompts not loaded: %s", e)
    except Exception as e:
        logger.error(f"Error importing tools: {e}")

    # MCP lifecycle hooks (FastMCP 2.13+ style)
    if hasattr(app, "on_startup"):

        @app.on_startup
        def on_startup() -> None:
            """Called when the MCP server starts."""
            logger.info("PyWinAuto MCP Portmanteau Edition starting...")
            logger.info(f"OCR available: {OCR_AVAILABLE}")

    if hasattr(app, "on_shutdown"):

        @app.on_shutdown
        def on_shutdown() -> None:
            """Called when the MCP server shuts down."""
            logger.info("PyWinAuto MCP server shutting down...")
            try:
                from windows_computer_use_mcp.keylogger_service import GlobalKeyloggerService

                GlobalKeyloggerService.get().stop()
            except Exception as e:
                logger.debug("Keylogger shutdown: %s", e)

    logger.info("MCP server initialized successfully")

except ImportError as e:
    logger.critical(f"Failed to import FastMCP app: {e}")
    sys.exit(1)
except Exception as e:
    logger.critical(f"Error initializing MCP server: {e}", exc_info=True)
    sys.exit(1)


def get_registered_tools() -> list[str]:
    """Helper function to get registered tools as a list."""
    try:
        # FastMCP 2.13+ tool access
        if hasattr(app, "_tool_manager") and hasattr(app._tool_manager, "tools"):
            return list(app._tool_manager.tools.keys())
        elif hasattr(app, "_tools"):
            return list(app._tools.keys())
        else:
            logger.warning("Could not determine how to list tools from FastMCP app")
            return []
    except Exception as e:
        logger.error(f"Error getting registered tools: {e}")
        return []


def main() -> None:
    """Run the PyWinAuto MCP server or print MCP config snippet."""
    if len(sys.argv) > 1 and sys.argv[1] == "mcp-config":
        from windows_computer_use_mcp.cli import print_mcp_config

        print_mcp_config()
        return
    try:
        logger.info("=" * 60)
        logger.info("PyWinAuto MCP - Portmanteau Edition v0.4.2")
        logger.info("=" * 60)
        logger.info("FastMCP version: 2.13.1")
        logger.info(f"OCR available: {OCR_AVAILABLE}")

        # List registered tools
        registered_tools = get_registered_tools()
        logger.info(
            f"Registered portmanteau tools ({len(registered_tools)}): {', '.join(registered_tools) if registered_tools else 'No tools registered'}"
        )

        # Expected tools
        expected_tools = [
            "approve_automation",
            "automation_safety",
            "automation_windows",
            "automation_elements",
            "automation_mouse",
            "automation_keyboard",
            "global_keylogger",
            "automation_visual",
            "automation_face",
            "automation_system",
            "get_desktop_state",
            "get_window_state",
            "cua_computer_use_screenshot",
        ]
        logger.info(f"Expected tools: {', '.join(expected_tools)}")

        # Run the MCP server
        run_server(app, server_name="windows-computer-use-mcp")

    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.critical(f"Server error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("PyWinAuto MCP server stopped")


if __name__ == "__main__":
    main()
