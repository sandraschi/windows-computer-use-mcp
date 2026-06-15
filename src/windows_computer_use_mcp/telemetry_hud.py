"""Visual Telemetry HUD for PyWinAuto MCP.

Provides a high-visibility overlay for mouse coordinates and keyboard input events
to facilitate UI discovery and automation calibration (SOTA 2026).
"""

import logging
import threading
import tkinter as tk
from collections import deque
from typing import Any

from pynput import keyboard, mouse

logger = logging.getLogger(__name__)


class TelemetryHUD:
    """A transparent 'Always on Top' HUD for UI automation telemetry."""

    def __init__(self, duration: float = 10.0, capture_keys: bool = True):
        self.duration = duration
        self.capture_keys = capture_keys
        self.root = None
        self.coord_label = None
        self.input_label = None
        self.input_buffer = deque(maxlen=20)
        self.running = False
        self._lock = threading.Lock()

    def _update_hud(self, x: int, y: int, key_char: str | None = None):
        """Updates the HUD labels with new telemetry data."""
        if not self.root:
            return

        def _sync_update():
            if self.coord_label:
                self.coord_label.config(text=f"Coords: ({x}, {y})")
            if self.capture_keys and key_char and self.input_label:
                with self._lock:
                    self.input_buffer.append(key_char)
                    buffer_str = "".join(self.input_buffer)
                self.input_label.config(text=f"Input: {buffer_str}")

        try:
            self.root.after(0, _sync_update)
        except Exception:
            logger.debug("Failed to sync HUD update (likely during shutdown)")
            pass

    def _on_move(self, x: int, y: int):
        self._update_hud(int(x), int(y))

    def _on_click(self, x: int, y: int, button: Any, pressed: bool):
        if pressed:
            self._update_hud(int(x), int(y), f"[{button.name.upper()}]")

    def _on_press(self, key: Any):
        try:
            char = key.char if hasattr(key, "char") and key.char else f"[{key.name}]"
        except AttributeError:
            char = f"[{key!s}]"

        self._update_hud(0, 0, char)

    def start(self):
        """Launches the HUD in the main thread (tkinter requirement)."""
        self.running = True
        self.root = tk.Tk()
        self.root.title("MCP Telemetry HUD")

        # Configure window: Always on top, no window decorations, semi-transparent
        self.root.attributes("-topmost", True)
        self.root.overrideredirect(True)
        self.root.attributes("-alpha", 0.8)
        self.root.configure(bg="#1e1e2e")  # Tokyo Night style dark background

        # Position HUD in the bottom right corner initially
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"250x100+{screen_w - 270}+{screen_h - 150}")

        # Dragging functionality so user can move it
        def start_move(event):
            self.root.x = event.x
            self.root.y = event.y

        def stop_move(event):
            self.root.x = None
            self.root.y = None

        def on_move(event):
            deltax = event.x - self.root.x
            deltay = event.y - self.root.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")

        self.root.bind("<Button-1>", start_move)
        self.root.bind("<ButtonRelease-1>", stop_move)
        self.root.bind("<B1-Motion>", on_move)

        # Labels
        header = tk.Label(
            self.root, text="AUTOMATION TELEMETRY", fg="#89b4fa", bg="#1e1e2e", font=("Consolas", 10, "bold")
        )
        header.pack(pady=(5, 2))

        self.coord_label = tk.Label(self.root, text="Coords: (0, 0)", fg="#cdd6f4", bg="#1e1e2e", font=("Consolas", 10))
        self.coord_label.pack()

        if self.capture_keys:
            self.input_label = tk.Label(
                self.root, text="Input: ", fg="#a6e3a1", bg="#1e1e2e", font=("Consolas", 9), wraplength=230
            )
            self.input_label.pack(pady=(2, 5))

        # Start pynput listeners in background threads
        mouse_listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click)
        mouse_listener.start()

        key_listener = None
        if self.capture_keys:
            key_listener = keyboard.Listener(on_press=self._on_press)
            key_listener.start()

        # Shutdown timer
        def shutdown():
            logger.info("Telemetry HUD duration expired. Closing.")
            self.running = False
            mouse_listener.stop()
            if key_listener:
                key_listener.stop()
            self.root.destroy()

        self.root.after(int(self.duration * 1000), shutdown)

        logger.info(f"Starting Telemetry HUD for {self.duration}s")
        self.root.mainloop()


def launch_hud(duration: float = 10.0, capture_keys: bool = True):
    """Convenience function to launch the HUD safely."""
    hud = TelemetryHUD(duration=duration, capture_keys=capture_keys)
    hud.start()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--capture-keys", action="store_true")
    args = parser.parse_args()

    launch_hud(duration=args.duration, capture_keys=args.capture_keys)
