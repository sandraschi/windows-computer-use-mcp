"""Configuration management for PyWinAutoMCP.

This module provides configuration loading and management for the PyWinAutoMCP server.
"""

import logging
import os
from typing import Any

import yaml

# Default configuration
DEFAULT_CONFIG = {
    "log_level": "INFO",
    "plugins": {
        "ocr": {
            "enabled": True,
            "tesseract_cmd": "tesseract",  # Default to system PATH
            "tesseract_config": "--oem 3 --psm 6",
        }
    },
}

# Environment variable for config file path
CONFIG_FILE_ENV_VAR = "windows_computer_use_mcp_CONFIG"

# Default config file locations
DEFAULT_CONFIG_PATHS = [
    os.path.join(os.getcwd(), "config.yaml"),
    os.path.join(os.path.expanduser("~"), ".config", "windows-computer-use-mcp", "config.yaml"),
    "/etc/windows-computer-use-mcp/config.yaml",
]


def find_config_file() -> str | None:
    """Find the configuration file.

    Returns:
        Optional[str]: Path to the config file if found, None otherwise

    """
    # Check environment variable first
    env_path = os.environ.get(CONFIG_FILE_ENV_VAR)
    if env_path and os.path.isfile(env_path):
        return env_path

    # Check default locations
    for path in DEFAULT_CONFIG_PATHS:
        if os.path.isfile(path):
            return path

    return None


def load_config_file(path: str) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to the YAML config file

    Returns:
        Dict[str, Any]: Loaded configuration

    Raises:
        ValueError: If the config file is invalid

    """
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file: {e!s}") from e
    except Exception as e:
        raise ValueError(f"Failed to load config file: {e!s}") from e


def get_config(config_path: str | None = None) -> dict[str, Any]:
    """Get the application configuration.

    Args:
        config_path: Optional path to the config file. If not provided,
                    will search in default locations.

    Returns:
        Dict[str, Any]: Merged configuration

    """
    # Start with default config
    config = DEFAULT_CONFIG.copy()

    # Find and load config file if path not provided
    if config_path is None:
        config_path = find_config_file()

    # Load config from file if found
    if config_path and os.path.isfile(config_path):
        try:
            file_config = load_config_file(config_path)
            # Merge with defaults
            config.update(file_config)
        except Exception as e:
            logging.warning(f"Failed to load config from {config_path}: {e!s}")

    # Apply environment variable overrides
    for key, value in os.environ.items():
        if key.startswith("windows_computer_use_mcp_"):
            # Convert windows_computer_use_mcp_PLUGINS_OCR_TESSERACT_CMD to plugins.ocr.tesseract_cmd
            parts = key.lower().split("_")
            if len(parts) >= 4 and parts[0] == "pywinauto" and parts[1] == "mcp":
                # Skip the first 2 parts (pywinauto, mcp)
                parts = parts[2:]

                # Find or create the config section
                current = config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Set the value
                current[parts[-1]] = value

    return config
