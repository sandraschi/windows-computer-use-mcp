"""UI Element Walker - Traverse Windows UI Automation tree and extract elements."""

import os
import threading

from pywinauto import Desktop

ENV_LOOSE_UIA = "windows_computer_use_mcp_LOOSE_UIA"


class UIElementWalker:
    """Walk Windows UI Automation tree and extract elements."""

    INTERACTIVE_TYPES = {
        "Button",
        "Edit",
        "ComboBox",
        "ListItem",
        "MenuItem",
        "TabItem",
        "Hyperlink",
        "CheckBox",
        "RadioButton",
        "Slider",
        "ScrollBar",
        "DataItem",
        "Link",
        "Pane",
        "Custom",
        "Document",
        "Table",
        "Tree",
        "TreeItem",
        "Group",
        "SplitButton",
        "Spinner",
        "MenuBar",
    }

    INFORMATIVE_TYPES = {"Text", "StatusBar", "TitleBar", "ToolBar", "Header", "Window"}

    def __init__(self, max_depth: int = 10, element_timeout: float = 0.5):
        self.max_depth = max_depth
        self.element_timeout = element_timeout  # Timeout per element in seconds
        self.elements = []

    def walk(self, root_element=None) -> list[dict]:
        """Walk UI tree and extract element information."""
        if root_element is None:
            root_element = Desktop(backend="uia")

        self.elements = []
        self._recurse(root_element, depth=0)
        return self.elements

    def walk_window(self, window_handle: int) -> list[dict]:
        """Walk UI tree scoped to one top-level window (HWND)."""
        desktop = Desktop(backend="uia")
        window = desktop.window(handle=window_handle)
        if not window.exists(timeout=2):
            raise ValueError(f"Window handle {window_handle} not found")
        self.elements = []
        try:
            for desc in window.descendants():
                try:
                    info = self._extract_element_info(desc)
                    if info and self._should_include(info):
                        info["id"] = len(self.elements)
                        self.elements.append(info)
                        if len(self.elements) >= 500:
                            break
                except Exception:
                    pass
        except Exception:
            self._recurse(window, depth=0)
        if not self.elements:
            self._recurse(window, depth=0)
        return self.elements

    def _recurse(self, element, depth: int):
        """Recursively walk UI tree."""
        if depth > self.max_depth:
            return

        try:
            # Extract element properties
            info = self._extract_element_info(element)

            if info and self._should_include(info):
                info["id"] = len(self.elements)
                self.elements.append(info)

            # Handle Desktop object specially - use windows() instead of children()
            if hasattr(element, "windows") and callable(element.windows):
                # This is a Desktop object
                children = element.windows()
            else:
                # This is a regular UI element
                children = element.children()

            # Recurse children
            for child in children:
                self._recurse(child, depth + 1)

        except Exception:
            # Skip problematic elements
            pass

    def _extract_element_info(self, element) -> dict | None:
        """Extract all relevant properties from element with timeout."""
        result = [None]  # Use list to modify from thread

        def extract_with_timeout():
            try:
                # Get bounding rectangle
                rect = element.rectangle()

                # Get parent window
                parent_window = self._get_parent_window(element)

                # Handle control type for different backends
                if hasattr(element, "element_info") and hasattr(element.element_info, "control_type"):
                    # UIA backend
                    control_type = element.element_info.control_type
                else:
                    # Win32 backend or fallback
                    control_type = getattr(element, "control_type", "Unknown")

                info = {
                    "type": control_type,
                    "name": element.window_text(),
                    "app": parent_window.window_text() if parent_window else "Desktop",
                    "bounds": {
                        "x": rect.left,
                        "y": rect.top,
                        "width": rect.width(),
                        "height": rect.height(),
                    },
                    "is_visible": element.is_visible(),
                    "is_enabled": element.is_enabled(),
                    "shortcut": getattr(element, "access_key", ""),
                    "class_name": element.class_name(),
                }

                result[0] = info

            except Exception:
                # Skip problematic elements
                pass

        # Run extraction in a separate thread with timeout
        thread = threading.Thread(target=extract_with_timeout)
        thread.daemon = True
        thread.start()
        thread.join(timeout=self.element_timeout)

        return result[0]

    def _get_parent_window(self, element):
        """Find parent top-level window."""
        current = element
        while current:
            try:
                if current.control_type == "Window":
                    return current
                current = current.parent()
            except:
                break
        return None

    def _should_include(self, info: dict) -> bool:
        """Determine if element should be included."""
        # Must be visible
        if not info.get("is_visible"):
            return False

        # Must have valid bounds
        if info["bounds"]["width"] <= 0 or info["bounds"]["height"] <= 0:
            return False

        # Must be interactive or informative
        elem_type = info.get("type", "")
        if elem_type in self.INTERACTIVE_TYPES or elem_type in self.INFORMATIVE_TYPES:
            return True
        if _loose_uia_enabled():
            name = (info.get("name") or "").strip()
            if name and info["bounds"]["width"] >= 8 and info["bounds"]["height"] >= 8:
                return True
        return False


def _loose_uia_enabled() -> bool:
    return os.getenv(ENV_LOOSE_UIA, "").strip().lower() in ("1", "true", "yes", "on")
