"""Tests for utility functions and decorators."""

import time
from unittest.mock import MagicMock, patch

import pytest

from windows_computer_use_mcp.tools import utils


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_error_response_creation(self):
        """Test creating an ErrorResponse."""
        error = utils.ErrorResponse(error="Test error", error_type="ValueError")

        assert error.success is False
        assert error.error == "Test error"
        assert error.error_type == "ValueError"
        assert isinstance(error.timestamp, str)


class TestSuccessResponse:
    """Tests for SuccessResponse model."""

    def test_success_response_creation(self):
        """Test creating a SuccessResponse."""
        success = utils.SuccessResponse(data={"result": "test"})

        assert success.success is True
        assert success.data == {"result": "test"}
        assert isinstance(success.timestamp, str)


class TestHandleErrors:
    """Tests for handle_errors decorator."""

    def test_handle_errors_success(self):
        """Test error handler with successful function."""

        @utils.handle_errors
        def test_func():
            return {"result": "success"}

        result = test_func()

        assert result["success"] is True
        assert "data" in result
        assert "timestamp" in result

    def test_handle_errors_exception(self):
        """Test error handler with exception."""

        @utils.handle_errors
        def test_func():
            raise ValueError("Test error")

        result = test_func()

        assert result["success"] is False
        assert result["error"] == "Test error"
        assert result["error_type"] == "ValueError"
        assert "timestamp" in result

    def test_handle_errors_exception_no_args(self):
        """Test error handler with exception but no args in extra."""

        @utils.handle_errors
        def test_func_no_args():
            raise ValueError("Test error")

        result = test_func_no_args()

        assert result["success"] is False
        assert result["error"] == "Test error"

    def test_handle_errors_already_has_response(self):
        """Test error handler when function already returns response dict."""

        @utils.handle_errors
        def test_func():
            return {"success": True, "data": "test"}

        result = test_func()

        assert result["success"] is True
        assert result["data"] == "test"


class TestLogExecution:
    """Tests for log_execution decorator."""

    @patch("windows_computer_use_mcp.tools.utils.logger")
    def test_log_execution_success(self, mock_logger):
        """Test execution logging with successful function."""

        @utils.log_execution
        def test_func():
            return "result"

        result = test_func()

        assert result == "result"
        assert mock_logger.info.called

    @patch("windows_computer_use_mcp.tools.utils.logger")
    def test_log_execution_exception(self, mock_logger):
        """Test execution logging with exception."""

        @utils.log_execution
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            test_func()

        assert mock_logger.error.called


class TestTimer:
    """Tests for timer context manager."""

    @patch("windows_computer_use_mcp.tools.utils.logger")
    def test_timer_context_manager(self, mock_logger):
        """Test timer context manager."""
        with utils.timer("test operation"):
            time.sleep(0.01)

        assert mock_logger.debug.called


class TestValidateWindowHandle:
    """Tests for validate_window_handle function."""

    @patch("windows_computer_use_mcp.tools.utils.Desktop")
    def test_validate_window_handle_valid(self, mock_desktop):
        """Test validating a valid window handle."""
        mock_desktop_obj = MagicMock()
        mock_window = MagicMock()
        mock_window.exists.return_value = True
        mock_desktop_obj.window.return_value = mock_window
        mock_desktop.return_value = mock_desktop_obj

        result = utils.validate_window_handle(12345)

        assert result is True

    @patch("windows_computer_use_mcp.tools.utils.Desktop")
    def test_validate_window_handle_invalid(self, mock_desktop):
        """Test validating an invalid window handle."""
        mock_desktop_obj = MagicMock()
        mock_desktop_obj.window.side_effect = Exception("Window not found")
        mock_desktop.return_value = mock_desktop_obj

        result = utils.validate_window_handle(99999)

        assert result is False


class TestGetDesktop:
    """Tests for get_desktop function."""

    @patch("windows_computer_use_mcp.tools.utils.Desktop")
    def test_get_desktop_success(self, mock_desktop):
        """Test getting desktop instance successfully."""
        mock_desktop_obj = MagicMock()
        mock_desktop.return_value = mock_desktop_obj

        result = utils.get_desktop()

        assert result == mock_desktop_obj
        mock_desktop.assert_called_once_with(backend="uia")

    @patch("windows_computer_use_mcp.tools.utils.Desktop")
    @patch("windows_computer_use_mcp.tools.utils.logger")
    def test_get_desktop_failure(self, mock_logger, mock_desktop):
        """Test getting desktop instance with failure."""
        mock_desktop.side_effect = Exception("Desktop init failed")

        with pytest.raises(RuntimeError) as exc_info:
            utils.get_desktop()

        assert "Failed to initialize Windows Desktop automation" in str(exc_info.value)
        assert mock_logger.error.called
