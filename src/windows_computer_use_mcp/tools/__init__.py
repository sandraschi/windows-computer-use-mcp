"""PyWinAuto MCP Tools Package - Portmanteau Edition.

This package registers **seven** core portmanteau tools plus **get_desktop_state**.
**automation_face** is optional (off by default); see `docs/SAFETY.md` §5 and `windows_computer_use_mcp_ENABLE_FACE`.
**global_keylogger** is optional (off by default); set `windows_computer_use_mcp_ENABLE_KEYLOGGER=1` (high-risk).

PORTMANTEAU TOOL ARCHITECTURE:
Instead of 60+ individual tools, this package consolidates related operations
into comprehensive portmanteau tools:

1. automation_windows   - Window management (11 operations)
2. automation_elements  - UI element interaction (14 operations)
3. automation_mouse     - Mouse control (9 operations)
4. automation_keyboard  - Keyboard input (4 operations)
5. automation_visual    - Screenshots/OCR/image recognition (4 operations)
6. automation_assert    - UI verification: hash, diff, wait_stable, asserts (8 operations)
7. automation_dialog    - File dialog path entry (3 operations)
8. automation_shortcut  - Semantic app shortcuts (3 operations)
9. automation_task      - Closed-loop task runner (4 operations)
10. automation_face     - Face recognition (5 operations) — **opt-in** (`windows_computer_use_mcp_ENABLE_FACE=1` + face extra)
8. automation_system    - System utilities (7 operations)
8. get_desktop_state    - Comprehensive desktop UI discovery (standalone)
9. get_window_state     - Per-window snapshot (Cua-shaped; snapshot_id + element_index)

This design:
- Prevents tool explosion while maintaining full functionality
- Improves discoverability by grouping related operations
- Reduces cognitive load when working with automation tasks
- Follows FastMCP 2.13+ best practices
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

# Import the app instance from the app module
try:
    from windows_computer_use_mcp.app import app

    logger.info("Successfully imported FastMCP app instance")
except ImportError as e:
    logger.error(f"Failed to import FastMCP app: {e}")
    app = None

try:
    from windows_computer_use_mcp.safety import (
        ENV_ENABLE_FACE,
        ENV_ENABLE_KEYLOGGER,
        is_face_tool_enabled,
        is_keylogger_tool_enabled,
    )
except ImportError:
    ENV_ENABLE_FACE = "windows_computer_use_mcp_ENABLE_FACE"
    ENV_ENABLE_KEYLOGGER = "windows_computer_use_mcp_ENABLE_KEYLOGGER"

    def is_face_tool_enabled() -> bool:
        return False

    def is_keylogger_tool_enabled() -> bool:
        return False


# List of portmanteau tool modules to import (face is opt-in: see docs/SAFETY.md §5)
PORTMANTEAU_MODULES = [
    "portmanteau_windows",  # Window management
    "portmanteau_elements",  # UI element interaction
    "portmanteau_mouse",  # Mouse control
    "portmanteau_keyboard",  # Keyboard input
    "portmanteau_visual",  # Visual/screenshot/OCR
    "portmanteau_assert",  # UI verification and stability
    "portmanteau_dialog",  # File dialog path entry
    "portmanteau_shortcut",  # Semantic app shortcuts
    "portmanteau_task",  # Closed-loop task runner
    "portmanteau_system",  # System utilities
    "portmanteau_mission",  # Agentic Missions (Sampling)
    "portmanteau_macro",  # Session recording / macros
    "portmanteau_smart",  # Smart discovery and intent-based click
    "portmanteau_analyze",  # WinApp analysis: crawl, discover, portfolio
    "desktop_state",  # Desktop state capture (standalone)
    "window_state",  # Per-window capture (Cua parity)
    "computer_use_compat",  # Claude CU window screenshot alias
]
if is_face_tool_enabled():
    # Insert before system so ordering matches historical "face before system" lists
    idx = PORTMANTEAU_MODULES.index("portmanteau_system")
    PORTMANTEAU_MODULES.insert(idx, "portmanteau_face")
    logger.info("Face tool enabled (%s=1): will load portmanteau_face", ENV_ENABLE_FACE)
else:
    logger.info(
        "automation_face not registered (opt-in). Set %s=1 and install the face extra to enable.",
        ENV_ENABLE_FACE,
    )

if is_keylogger_tool_enabled():
    _kidx = PORTMANTEAU_MODULES.index("portmanteau_keyboard") + 1
    PORTMANTEAU_MODULES.insert(_kidx, "portmanteau_keylogger")
    logger.info("Keylogger tool enabled (%s=1): will load portmanteau_keylogger", ENV_ENABLE_KEYLOGGER)
else:
    logger.info(
        "global_keylogger not registered (opt-in). Set %s=1 to enable.",
        ENV_ENABLE_KEYLOGGER,
    )

# Import all portmanteau tool modules - this will trigger their registration with FastMCP
if app is not None:
    for module_name in PORTMANTEAU_MODULES:
        try:
            __import__(f"{__name__}.{module_name}", fromlist=["*"])
            logger.info(f"Successfully imported {module_name}")
        except ImportError as e:
            logger.error(f"Failed to import {module_name}: {e}")
        except Exception as e:
            logger.error(f"Error initializing {module_name}: {e}")

# Export the main components
__all__ = [
    "app",
    "desktop_state",
    "portmanteau_analyze",
    "portmanteau_elements",
    "portmanteau_face",
    "portmanteau_keyboard",
    "portmanteau_mouse",
    "portmanteau_system",
    "portmanteau_visual",
    "portmanteau_windows",
]
