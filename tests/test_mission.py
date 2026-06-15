"""Tests for the automation_mission portmanteau tool and sampling integration."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from windows_computer_use_mcp.tools.models import MissionOperationRequest
from windows_computer_use_mcp.tools.portmanteau_mission import automation_mission


class TestAutomationMission:
    """Tests for automation_mission tool."""

    @pytest.mark.asyncio
    async def test_automation_mission_success(self, app_instance, verify_result):
        """Test successful mission planning via sampling."""
        # Mock FastMCP Context
        mock_ctx = AsyncMock()

        # Mock Sample response
        mock_sample_result = MagicMock()
        mock_sample_result.content = "1. Open Notepad\n2. Type 'Hello'\n3. Save"
        mock_ctx.sample.return_value = mock_sample_result

        req = MissionOperationRequest(operation="plan", goal="Test goal")
        result = await automation_mission(req, ctx=mock_ctx)

        verify_result(result, expected_keys=["mission_id", "plan", "status"])
        assert "Notepad" in result.data["plan"]

        # Verify context calls
        assert mock_ctx.sample.called
        assert mock_ctx.report_progress.called

        # Verify the prompt sent to sample
        _args, kwargs = mock_ctx.sample.call_args
        assert "Test goal" in kwargs["messages"]

    @pytest.mark.asyncio
    async def test_automation_mission_no_ctx(self, app_instance, verify_result):
        """Test mission fails gracefully when sampling context is missing."""
        req = MissionOperationRequest(operation="plan", goal="No context goal")
        result = await automation_mission(req, ctx=None)

        verify_result(result, expected_status="error", message_contains="Sampling context not available")
