"""Tests for the automation_mouse portmanteau tool."""

# Imports moved for mocking integrity


class TestAutomationMouse:
    """Tests for automation_mouse tool operations."""

    def test_mouse_position(self, mock_pyautogui, verify_result):
        """Test getting mouse position."""
        mock_pyautogui.position.return_value = (100, 200)

        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="position")
        result = automation_mouse(req)

        verify_result(result, expected_keys=["x", "y"])
        assert result.data["x"] == 100
        assert result.data["y"] == 200
        mock_pyautogui.position.assert_called_once()

    def test_mouse_move_absolute(self, mock_pyautogui, verify_result):
        """Test absolute mouse movement."""
        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="move", x=500, y=600, absolute=True)
        result = automation_mouse(req)

        verify_result(result, expected_keys=["x", "y"])
        assert result.data["x"] == 500
        assert result.data["y"] == 600
        mock_pyautogui.moveTo.assert_called_once_with(500, 600, duration=0.0)

    def test_mouse_move_relative(self, mock_pyautogui, verify_result):
        """Test relative mouse movement."""
        mock_pyautogui.position.return_value = (150, 150)

        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="move_relative", x=50, y=50)
        result = automation_mouse(req)

        verify_result(result, expected_keys=["x", "y"])
        assert result.data["x"] == 150
        assert result.data["y"] == 150
        mock_pyautogui.moveRel.assert_called_once_with(50, 50, duration=0.0)

    def test_mouse_click(self, mock_pyautogui, verify_result):
        """Test mouse click at position."""
        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="click", x=100, y=100, button="left")
        result = automation_mouse(req)

        verify_result(result)
        mock_pyautogui.click.assert_called_once()
        _args, kwargs = mock_pyautogui.click.call_args
        assert kwargs["button"] == "left"

    def test_mouse_double_click(self, mock_pyautogui, verify_result):
        """Test mouse double click."""
        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="double_click", x=100, y=100)
        result = automation_mouse(req)

        verify_result(result)
        mock_pyautogui.doubleClick.assert_called_once()

    def test_mouse_right_click(self, mock_pyautogui, verify_result):
        """Test mouse right click."""
        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="right_click", x=100, y=100)
        result = automation_mouse(req)

        verify_result(result)
        mock_pyautogui.rightClick.assert_called_once()

    def test_mouse_scroll(self, mock_pyautogui, verify_result):
        """Test mouse scroll."""
        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="scroll", clicks=10)
        result = automation_mouse(req)

        verify_result(result)
        mock_pyautogui.scroll.assert_called_once_with(10)

    def test_mouse_drag(self, mock_pyautogui, verify_result):
        """Test mouse drag."""
        from windows_computer_use_mcp.tools.models import MouseOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mouse import automation_mouse

        req = MouseOperationRequest(operation="drag", x=100, y=100, x2=200, y2=200)
        result = automation_mouse(req)

        verify_result(result)
        mock_pyautogui.moveTo.assert_called_with(100, 100)
        mock_pyautogui.dragTo.assert_called_once_with(200, 200, duration=0.0, button="left")

    def test_invalid_operation(self, verify_result):
        """Test invalid operation error handling."""
        import pytest
        from pydantic import ValidationError

        from windows_computer_use_mcp.tools.models import MouseOperationRequest

        with pytest.raises(ValidationError):
            MouseOperationRequest(operation="invalid_op")
