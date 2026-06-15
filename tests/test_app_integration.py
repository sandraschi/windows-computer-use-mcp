import pytest

# Trigger tool registration
from windows_computer_use_mcp.app import app


class TestAppInitialization:
    """Tests for app initialization."""

    def test_app_instance_exists(self):
        """Test that app instance is created."""
        assert app is not None
        assert hasattr(app, "name")
        assert app.name == "windows-computer-use-mcp"

    def test_app_version(self):
        """Test that app has correct version from pyproject.toml."""
        # Note: In our current industrialized version, app.version is 0.4.2
        assert app.version == "0.4.2"

    def test_ocr_availability_flag(self):
        """Test OCR availability flag."""
        from windows_computer_use_mcp.app import OCR_AVAILABLE

        assert isinstance(OCR_AVAILABLE, bool)


class TestToolRegistration:
    """Tests for tool registration."""

    @pytest.mark.asyncio
    async def test_tools_are_registered(self, app_instance):
        """Test that all 9 industrialized portmanteau tools are registered."""
        # FastMCP 3.2+ list_tools is async
        tools = await app_instance.list_tools()
        assert tools is not None

        tool_names = [t.name for t in tools]
        expected_tools = [
            "automation_windows",
            "automation_elements",
            "automation_mouse",
            "automation_keyboard",
            "automation_visual",
            "automation_system",
            "automation_mission",
            "get_desktop_state",
            # automation_face is optional, so we don't strictly assert it here
            # without checking the environment first
        ]

        for name in expected_tools:
            assert name in tool_names, f"Tool '{name}' not found in registered tools: {tool_names}"

    @pytest.mark.asyncio
    async def test_automation_system_tool_exists(self, app_instance):
        """Test that automation_system tool is registered."""
        tools = await app_instance.list_tools()
        tool_names = [t.name for t in tools]
        assert "automation_system" in tool_names


class TestModuleImports:
    """Tests for module imports."""

    def test_all_tool_modules_importable(self):
        """Test that all tool modules can be imported."""
        modules = [
            "windows_computer_use_mcp.tools.portmanteau_windows",
            "windows_computer_use_mcp.tools.portmanteau_elements",
            "windows_computer_use_mcp.tools.portmanteau_mouse",
            "windows_computer_use_mcp.tools.portmanteau_keyboard",
            "windows_computer_use_mcp.tools.portmanteau_visual",
            "windows_computer_use_mcp.tools.portmanteau_system",
            "windows_computer_use_mcp.tools.portmanteau_mission",
            "windows_computer_use_mcp.tools.desktop_state",
        ]

        for module_name in modules:
            try:
                __import__(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import {module_name}: {e}")
