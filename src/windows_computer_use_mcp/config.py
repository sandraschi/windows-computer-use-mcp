"""Configuration settings for PyWinAuto MCP."""

from pathlib import Path

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import validator


class Settings(BaseSettings):
    """Application settings."""

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    RELOAD: bool = False
    WORKERS: int = 1

    # PyWinAuto Settings
    TIMEOUT: float = 10.0  # Default timeout in seconds for operations
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: float = 1.0

    # Screenshot Settings
    SCREENSHOT_DIR: Path = Path("./screenshots")
    SCREENSHOT_FORMAT: str = "png"

    # OCR Settings
    TESSERACT_CMD: str | None = None  # Path to tesseract executable if not in PATH
    TESSERACT_LANG: str = "eng"  # Default language for OCR
    TESSERACT_CONFIG: str = "--psm 6 --oem 3"  # Default Tesseract config

    # MCP Settings
    MCP_NAME: str = "windows-computer-use-mcp"
    MCP_VERSION: str = "0.1.0"
    MCP_DESCRIPTION: str = "MCP server for Windows UI automation using PyWinAuto with OCR capabilities"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("SCREENSHOT_DIR", pre=True)
    def create_screenshot_dir(self, v):
        """Create screenshot directory if it doesn't exist."""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
settings = Settings()
