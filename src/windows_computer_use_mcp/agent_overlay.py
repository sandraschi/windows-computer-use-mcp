"""Virtual agent cursor overlay (click-through marker, does not move physical cursor)."""

from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)

_overlay_lock = threading.Lock()
_active_overlay: AgentCursorOverlay | None = None


class AgentCursorOverlay:
    """Small always-on-top marker at screen coordinates."""

    def __init__(self, x: int, y: int, *, duration_sec: float = 1.5, label: str = "agent"):
        self.x = x
        self.y = y
        self.duration_sec = duration_sec
        self.label = label
        self._thread: threading.Thread | None = None

    def show_async(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        try:
            import tkinter as tk

            root = tk.Tk()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.attributes("-alpha", 0.75)
            size = 28
            root.geometry(f"{size}x{size}+{self.x}+{self.y}")
            canvas = tk.Canvas(root, width=size, height=size, highlightthickness=0, bg="#1e1e2e")
            canvas.pack()
            canvas.create_oval(4, 4, size - 4, size - 4, outline="#f59e0b", width=2)
            canvas.create_text(size // 2, size // 2, text="A", fill="#fbbf24", font=("Segoe UI", 9, "bold"))
            root.after(int(self.duration_sec * 1000), root.destroy)
            root.mainloop()
        except Exception as exc:
            logger.debug("Agent overlay unavailable: %s", exc)


def show_agent_cursor(x: int, y: int, *, duration_sec: float = 1.5) -> None:
    """Show overlay marker when windows_computer_use_mcp_AGENT_OVERLAY=1."""
    import os

    if os.getenv("windows_computer_use_mcp_AGENT_OVERLAY", "").strip().lower() not in ("1", "true", "yes", "on"):
        return
    global _active_overlay
    with _overlay_lock:
        overlay = AgentCursorOverlay(x, y, duration_sec=duration_sec)
        _active_overlay = overlay
    overlay.show_async()
    time.sleep(0.05)
