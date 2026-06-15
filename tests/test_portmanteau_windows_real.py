"""Real window tests for the portmanteau window management tools.
These tests require real windows and will be skipped unless PYWINAUTO_TEST_REAL_WINDOWS=1 is set.
"""

import os
import subprocess
import sys
import time

import pytest

# Check if we should run real window tests (set PYWINAUTO_TEST_REAL_WINDOWS=1 to enable)
REAL_WINDOW_TESTS = os.environ.get("PYWINAUTO_TEST_REAL_WINDOWS", "").lower() in (
    "1",
    "true",
    "yes",
)
SKIP_REAL_TESTS = not REAL_WINDOW_TESTS or not sys.platform.startswith("win")


@pytest.mark.requires_hardware
@pytest.mark.destructive
class TestPortmanteauWindowsReal:
    """Real window tests for the automation_windows portmanteau tool.

    These tests will be skipped unless PYWINAUTO_TEST_REAL_WINDOWS=1 is set.
    """

    test_process = None
    test_window_handle = None
    test_window_started = False

    @classmethod
    def setup_class(cls):
        """Start a test window for real testing if enabled."""
        if not REAL_WINDOW_TESTS:
            return

        try:
            # Start Notepad for real window testing
            cls.test_process = subprocess.Popen(["notepad.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)
            time.sleep(2)  # Give it time to start

            # Get the window handle
            from pywinauto import Desktop

            desktop = Desktop(backend="uia")
            window = desktop.window(title="Untitled - Notepad")
            if window.exists():
                cls.test_window_handle = window.handle
                cls.test_window_started = True
                print(f"Test window started with handle: {cls.test_window_handle}")
            else:
                print("Warning: Failed to find test window")

        except Exception as e:
            print(f"Warning: Failed to start test window: {e}")
            cls.test_process = None

    @classmethod
    def teardown_class(cls):
        """Clean up test windows."""
        if cls.test_process:
            try:
                cls.test_process.terminate()
                try:
                    cls.test_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    cls.test_process.kill()
            except Exception as e:
                print(f"Error cleaning up test process: {e}")
            cls.test_process = None
            cls.test_window_handle = None
            cls.test_window_started = False

    def _get_test_window_handle(self):
        """Get the test window handle if available."""
        if not self.test_window_started or not self.test_window_handle:
            pytest.skip("No real window available for testing")

        from pywinauto import Desktop

        try:
            desktop = Desktop(backend="uia")
            window = desktop.window(handle=self.test_window_handle)
            if window.exists():
                return self.test_window_handle
        except Exception as e:
            print(f"Error verifying window: {e}")

        pytest.skip("Test window no longer available")

    @pytest.mark.skipif(SKIP_REAL_TESTS, reason="Real window tests not enabled or not on Windows")
    def test_real_window_activation(self):
        """Test activating a real Notepad window."""
        from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows

        handle = self._get_test_window_handle()

        # Test activation
        result = automation_windows("activate", handle=handle)
        assert result["status"] == "success", f"Activation failed: {result.get('error', 'Unknown error')}"
        assert result["has_focus"] is True, "Window should have focus after activation"

        # Verify the window is actually active
        from pywinauto import Desktop

        desktop = Desktop(backend="uia")
        active_window = desktop.window(handle=handle)
        assert active_window.is_active(), "Window should be active after activation"

    @pytest.mark.skipif(SKIP_REAL_TESTS, reason="Real window tests not enabled or not on Windows")
    def test_real_minimized_window_activation(self):
        """Test restoring and activating a minimized window."""
        from pywinauto import Desktop

        from windows_computer_use_mcp.tools.portmanteau_windows import automation_windows

        handle = self._get_test_window_handle()
        desktop = Desktop(backend="uia")
        window = desktop.window(handle=handle)

        try:
            # Minimize the window first
            window.minimize()
            time.sleep(1)  # Give it time to minimize

            # Test activation
            result = automation_windows("activate", handle=handle)

            # Verify results
            assert result["status"] == "success"
            assert result["has_focus"] is True
            assert window.is_visible() is True
            assert window.is_minimized() is False

        finally:
            # Ensure window is restored for other tests
            window.restore()
