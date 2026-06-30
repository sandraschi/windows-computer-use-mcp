"""Voice control integration for windows-computer-use-mcp.

Connects to speech-mcp for speech-to-text and maps natural-language
commands to automation tool calls. Designed for tray app integration.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

SPEECH_MCP_URL = os.getenv("SPEECH_MCP_URL", "http://127.0.0.1:10909")
VOICE_ENABLED = os.getenv("WINDOWS_COMPUTER_USE_MCP_VOICE", "").lower() in ("1", "true", "yes")

_COMMAND_MAP: dict[str, str] = {
    "click": "mouse",
    "tap": "mouse",
    "press": "keyboard",
    "type": "keyboard",
    "write": "keyboard",
    "screenshot": "visual",
    "screenshot region": "visual",
    "scroll": "mouse",
    "scroll down": "mouse",
    "scroll up": "mouse",
    "maximize": "windows",
    "minimize": "windows",
    "close": "windows",
    "focus": "windows",
    "list windows": "windows",
    "open": "launch",
    "launch": "launch",
    "start": "launch",
    "position": "mouse",
    "where": "mouse",
    "record": "visual",
    "stop recording": "visual",
    "macro": "macro",
    "replay": "macro",
    "mission": "mission",
    "describe": "visual",
    "find": "visual",
}


def _call_speech_mcp(action: str, **kwargs) -> dict[str, Any]:
    """Call speech-mcp's HTTP API.

    Args:
        action: API action (transcribe, speak, etc.)
        kwargs: Parameters.

    Returns:
        Response dict.
    """
    import httpx

    try:
        resp = httpx.post(
            f"{SPEECH_MCP_URL}/api/v1/{action}",
            json=kwargs,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("speech-mcp call failed: %s", e)
        return {"error": str(e)}


def is_available() -> bool:
    """Check if speech-mcp is reachable."""
    import httpx

    try:
        resp = httpx.get(f"{SPEECH_MCP_URL}/api/health", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False


def transcribe(audio_path: str | None = None, duration: int = 5) -> str:
    """Transcribe audio from microphone or file.

    Args:
        audio_path: Optional WAV file path.
        duration: Recording duration in seconds (when no file).

    Returns:
        Transcribed text.
    """
    if audio_path:
        result = _call_speech_mcp("transcribe", file_path=audio_path)
    else:
        result = _call_speech_mcp("transcribe", record_duration=duration)
    return result.get("text", "")


def speak(text: str, voice: str = "default") -> bool:
    """Speak text through speech-mcp TTS.

    Args:
        text: Text to speak.
        voice: Voice name.

    Returns:
        True if successful.
    """
    result = _call_speech_mcp("speak", text=text, voice_id=voice)
    return "error" not in result


def parse_command(transcript: str) -> dict[str, Any] | None:
    """Parse a natural-language command into a tool call.

    Handles patterns like:
    - "click save" -> {"tool": "automation_elements", "operation": "click", "target": "save"}
    - "type hello world" -> {"tool": "automation_keyboard", "operation": "type_text", "text": "hello world"}
    - "screenshot" -> {"tool": "automation_visual", "operation": "screenshot"}
    - "scroll down 3" -> {"tool": "automation_mouse", "operation": "scroll", "amount": 3}

    Args:
        transcript: Recognized speech text.

    Returns:
        Tool call dict or None if unrecognized.
    """
    text = transcript.strip().lower()

    # Click patterns: "click X" or "tap X" or "double click X"
    m = re.match(r"(?:click|tap)\s+(.+?)(?:\s+double)?$", text)
    if m:
        target = m.group(1).strip()
        if "double" in text:
            return {"tool": "automation_elements", "operation": "double_click", "target": target}
        return {"tool": "automation_elements", "operation": "click", "target": target}

    # Type patterns: "type X" or "write X"
    m = re.match(r"(?:type|write|say)\s+(.+)$", text)
    if m:
        return {"tool": "automation_keyboard", "operation": "type_text", "text": m.group(1).strip()}

    # Press key: "press enter", "press escape"
    m = re.match(r"press\s+(\w+)$", text)
    if m:
        return {"tool": "automation_keyboard", "operation": "press_key", "key": m.group(1)}

    # Screenshot
    if text in ("screenshot", "take screenshot", "capture screen"):
        return {"tool": "automation_visual", "operation": "screenshot"}

    # Describe region
    if text in ("describe", "describe screen", "what do you see", "what's on screen"):
        return {"tool": "automation_visual", "operation": "describe_region"}

    # Scroll patterns
    m = re.match(r"scroll\s+(up|down)\s*(\d+)?", text)
    if m:
        direction = -1 if m.group(1) == "up" else 1
        amount = int(m.group(2)) if m.group(2) else 3
        return {"tool": "automation_mouse", "operation": "scroll", "amount": amount * direction}

    # Window commands
    m = re.match(r"(maximize|minimize|close|focus)\s+(.+)$", text)
    if m:
        return {"tool": "automation_windows", "operation": m.group(1), "title": m.group(2).strip()}

    if text in ("list windows", "show windows", "what's open"):
        return {"tool": "automation_windows", "operation": "list"}

    # Position
    if text in ("where", "position", "cursor position", "mouse position"):
        return {"tool": "automation_mouse", "operation": "position"}

    # Record
    if text in ("record", "start recording"):
        return {"tool": "automation_visual", "operation": "record", "duration": 10}
    if text in ("stop recording", "stop record"):
        return {"tool": "automation_visual", "operation": "record", "duration": 0}

    # Open/launch
    m = re.match(r"(?:open|launch|start)\s+(.+)$", text)
    if m:
        return {"tool": "automation_system", "operation": "start_app", "app": m.group(1).strip()}

    return None


# ---------------------------------------------------------------------------
# Voice listener thread (for tray app integration)
# ---------------------------------------------------------------------------


class VoiceListener:
    """Background thread that listens for voice commands via speech-mcp.

    Calls the provided callback with parsed tool commands.
    """

    def __init__(self, callback: Callable[[dict[str, Any]], None] | None = None):
        self._callback = callback
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self, duration: int = 5) -> bool:
        """Start a one-shot listen cycle.

        Args:
            duration: Recording duration in seconds.

        Returns:
            True if listen started.
        """
        if not is_available():
            logger.warning("speech-mcp not available")
            return False

        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, args=(duration,), daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._running = False

    @property
    def is_listening(self) -> bool:
        return self._running and (self._thread is not None and self._thread.is_alive())

    def _listen_loop(self, duration: int):
        text = transcribe(duration=duration)
        if not text:
            logger.info("No speech detected")
            if self._callback:
                self._callback({"status": "no_speech", "transcript": ""})
            self._running = False
            return

        logger.info("Transcript: %s", text)
        cmd = parse_command(text)
        if cmd:
            logger.info("Parsed command: %s", cmd)
            if self._callback:
                self._callback({"status": "parsed", "transcript": text, "command": cmd})
        else:
            logger.info("Unrecognized: %s", text)
            if self._callback:
                self._callback({"status": "unrecognized", "transcript": text})
        self._running = False
