"""Global low-level keyboard hook (Windows session) via pynput.

Captures key events system-wide for the current user session. Intended for
authorized automation and debugging only — see docs/SAFETY.md and
``windows_computer_use_mcp_ENABLE_KEYLOGGER``.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)


def _key_to_record(key: Any, event: str) -> dict[str, Any]:
    """Normalize a pynput key event to a JSON-serializable dict."""
    now = time.time()
    char: str | None = None
    key_name: str | None = None
    vk: int | None = None
    try:
        if getattr(key, "vk", None) is not None:
            vk = int(key.vk)
    except (TypeError, ValueError):
        vk = None
    try:
        if getattr(key, "char", None):
            char = key.char
        elif getattr(key, "name", None):
            key_name = str(key.name)
        else:
            key_name = repr(key)
    except Exception:
        key_name = repr(key)
    return {"t": now, "event": event, "char": char, "key": key_name, "vk": vk}


class GlobalKeyloggerService:
    """Singleton-style global keyboard listener with a bounded ring buffer."""

    _instance: GlobalKeyloggerService | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._listener: Any = None
        self._buffer: deque[dict[str, Any]] = deque(maxlen=5000)
        self._max_buffer = 5000
        self._capture_release = False
        self._started_at: float | None = None

    @classmethod
    def get(cls) -> GlobalKeyloggerService:
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _on_press(self, key: Any) -> None:
        try:
            rec = _key_to_record(key, "press")
            with self._lock:
                self._buffer.append(rec)
        except Exception as e:
            logger.debug("keylogger on_press error: %s", e)

    def _on_release(self, key: Any) -> None:
        if not self._capture_release:
            return
        try:
            rec = _key_to_record(key, "release")
            with self._lock:
                self._buffer.append(rec)
        except Exception as e:
            logger.debug("keylogger on_release error: %s", e)

    def start(self, *, max_buffer: int = 5000, include_release: bool = False) -> dict[str, Any]:
        from pynput import keyboard

        with self._lock:
            if self._listener is not None:
                return {
                    "ok": False,
                    "code": "already_running",
                    "message": "Keylogger is already active; call stop first.",
                }
            self._max_buffer = max(1, min(int(max_buffer), 100_000))
            self._buffer = deque(maxlen=self._max_buffer)
            self._capture_release = include_release
            self._started_at = time.time()
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release if include_release else None,
            )
            self._listener.start()
        logger.info(
            "Global keylogger started (max_buffer=%s, include_release=%s)",
            self._max_buffer,
            include_release,
        )
        return {
            "ok": True,
            "max_buffer": self._max_buffer,
            "include_release": include_release,
            "started_at": self._started_at,
        }

    def stop(self) -> dict[str, Any]:
        with self._lock:
            lst = self._listener
            self._listener = None
            self._started_at = None
        if lst is not None:
            try:
                lst.stop()
            except Exception as e:
                logger.warning("keylogger listener stop: %s", e)
            try:
                lst.join(timeout=3.0)
            except Exception as e:
                logger.debug("keylogger listener join: %s", e)
        logger.info("Global keylogger stopped")
        return {"ok": True}

    def status(self) -> dict[str, Any]:
        with self._lock:
            running = self._listener is not None
            n = len(self._buffer)
            max_b = self._max_buffer
            started = self._started_at
            cap_rel = self._capture_release
        return {
            "running": running,
            "events_in_buffer": n,
            "max_buffer": max_b,
            "started_at": started,
            "include_release": cap_rel,
        }

    def read(self, *, limit: int = 100, flush: bool = False) -> dict[str, Any]:
        """Return the most recent ``limit`` events (oldest-first within the batch)."""
        limit = max(1, min(int(limit), 10_000))
        with self._lock:
            if not self._buffer:
                return {"events": [], "count": 0, "buffer_remaining": 0}
            lst = list(self._buffer)
            take = lst[-limit:]
            if flush:
                keep = lst[: -len(take)] if len(take) < len(lst) else []
                self._buffer.clear()
                self._buffer.extend(keep)
            remaining = len(self._buffer)
        return {"events": take, "count": len(take), "buffer_remaining": remaining}

    def clear(self) -> dict[str, Any]:
        with self._lock:
            self._buffer.clear()
        return {"ok": True}


__all__ = ["GlobalKeyloggerService"]
