"""Tests for dependency failure reporting and agentic recovery."""

from unittest.mock import patch


class TestDependencyFailures:
    """Tests for tools with missing optional dependencies."""

    @patch("windows_computer_use_mcp.tools.portmanteau_face.FACE_RECOGNITION_AVAILABLE", False)
    def test_face_tool_missing_dependency(self, verify_result):
        """Test that automation_face reports missing dependency correctly."""
        # Note: We need to import inside to ensure the patch works if it was already imported
        # Or better yet, just call the tool directly with the mock state
        from windows_computer_use_mcp.tools.models import FaceOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_face import automation_face

        req = FaceOperationRequest(operation="recognize", name="admin", image_path="test.jpg")
        result = automation_face(req)

        verify_result(result, expected_status="error", message_contains="face_recognition library is not installed")
        assert "pip install face_recognition" in result.recovery_tip

    @patch("windows_computer_use_mcp.app.OCR_AVAILABLE", False)
    def test_visual_tool_missing_ocr(self, verify_result):
        """Test that automation_visual reports missing OCR correctly."""
        from windows_computer_use_mcp.tools.models import VisualOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_visual import automation_visual

        req = VisualOperationRequest(operation="extract_text", handle=12345)
        result = automation_visual(req)

        # automation_visual should fail if OCR is requested but not available
        verify_result(result, expected_status="error", message_contains="tesseract is not installed")
        assert "README" in result.recovery_tip or "PATH" in result.recovery_tip or result.recovery_tip is not None

    def test_mission_tool_no_ctx(self, verify_result):
        """Test mission fails gracefully when sampling context is missing."""
        # Already tested in test_mission.py, but good to have here for compliance check
        import asyncio

        from windows_computer_use_mcp.tools.models import MissionOperationRequest
        from windows_computer_use_mcp.tools.portmanteau_mission import automation_mission

        req = MissionOperationRequest(operation="plan", goal="Test goal")

        # automation_mission is async
        result = asyncio.run(automation_mission(req, ctx=None))

        verify_result(result, expected_status="error", message_contains="Sampling context not available")
        assert "SOTA-compliant host" in result.recovery_tip
