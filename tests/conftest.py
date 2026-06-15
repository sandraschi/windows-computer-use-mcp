"""Pytest configuration and shared fixtures for PyWinAuto MCP tests."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Environment-aware CI vs local (mcp-central-docs: standards/testing-environment-aware.md)


@pytest.fixture(scope="session")
def app_instance():
    """Get the FastMCP app instance."""
    from windows_computer_use_mcp.app import app

    return app


@pytest.fixture
def mock_window():
    """Create a mock window object."""
    window = MagicMock()
    window.title = "Test Window"
    window.handle = 12345
    window.isVisible = True
    window.isEnabled = True
    window.rectangle = MagicMock()
    window.rectangle.left = 100
    window.rectangle.top = 100
    window.rectangle.right = 800
    window.rectangle.bottom = 600
    window.rectangle.width = 700
    window.rectangle.height = 500
    window.class_name = "TestWindowClass"
    window.process_id = 1234
    window.process_name = "test.exe"
    return window


@pytest.fixture
def mock_element():
    """Create a mock UI element."""
    element = MagicMock()
    element.automation_id = "btnOK"
    element.name = "OK Button"
    element.control_type = "Button"
    element.is_visible = True
    element.is_enabled = True
    element.rectangle = MagicMock()
    element.rectangle.left = 200
    element.rectangle.top = 300
    element.rectangle.right = 300
    element.rectangle.bottom = 350
    element.rectangle.width = 100
    element.rectangle.height = 50
    element.text = "OK"
    return element


@pytest.fixture
def mock_desktop():
    """Create a mock Desktop object."""
    desktop = MagicMock()
    return desktop


@pytest.fixture
def mock_application():
    """Create a mock Application object."""
    app = MagicMock()
    app.window.return_value = MagicMock()
    return app


@pytest.fixture
def mock_pyautogui():
    """Mock pyautogui for testing across portmanteau modules."""
    # We patch it in multiple modules because portmanteau tools import it directly
    mock_instance = MagicMock()
    patches = [
        patch("windows_computer_use_mcp.tools.portmanteau_mouse.pyautogui", mock_instance),
        patch("windows_computer_use_mcp.tools.portmanteau_elements.pyautogui", mock_instance),
        patch("windows_computer_use_mcp.tools.portmanteau_keyboard.pyautogui", mock_instance),
    ]

    for p in patches:
        p.start()

    # Configure common mock behavior
    mock_instance.position.return_value = (500, 500)
    mock_instance.size.return_value = (1920, 1080)
    mock_instance.click.return_value = None
    mock_instance.moveTo.return_value = None
    mock_instance.scroll.return_value = None
    mock_instance.write.return_value = None
    mock_instance.typewrite.return_value = None
    mock_instance.press.return_value = None
    mock_instance.hotkey.return_value = None
    mock_instance.doubleClick.return_value = None
    mock_instance.rightClick.return_value = None
    mock_instance.dragTo.return_value = None

    yield mock_instance

    for p in patches:
        p.stop()


@pytest.fixture
def mock_desktop_uia():
    """Mock pywinauto.Desktop for UIA-based element discovery."""
    # Patch all locations where Desktop is instantiated
    with (
        patch("windows_computer_use_mcp.tools.portmanteau_elements.Desktop") as mock_elem_desktop,
        patch("windows_computer_use_mcp.tools.portmanteau_windows.Desktop") as mock_win_desktop,
        patch("windows_computer_use_mcp.tools.portmanteau_visual.Desktop") as mock_vis_desktop,
        patch("windows_computer_use_mcp.tools.utils.Desktop") as mock_utils_desktop,
        patch("windows_computer_use_mcp.desktop_state.walker.Desktop") as mock_walker_desktop,
    ):
        mock_instance = MagicMock()
        mock_elem_desktop.return_value = mock_instance
        mock_win_desktop.return_value = mock_instance
        mock_vis_desktop.return_value = mock_instance
        mock_utils_desktop.return_value = mock_instance
        mock_walker_desktop.return_value = mock_instance

        yield mock_instance


@pytest.fixture
def mock_pywinauto():
    """Mock pywinauto for testing."""
    # Patch in the new portmanteau locations
    patches = [
        patch("windows_computer_use_mcp.tools.portmanteau_windows.Application"),
        patch("windows_computer_use_mcp.tools.portmanteau_windows.findwindows"),
    ]

    mock_objs = [p.start() for p in patches]
    mock_app, mock_find = mock_objs

    mock_window = MagicMock()
    mock_window.wrapper_object.return_value = MagicMock()
    mock_app.return_value = mock_window

    yield {"Application": mock_app, "findwindows": mock_find}

    for p in patches:
        p.stop()


@pytest.fixture
def mock_pygetwindow():
    """Mock pygetwindow for testing."""
    with patch("windows_computer_use_mcp.tools.portmanteau_system.gw") as mock:
        mock_window = MagicMock()
        mock_window.title = "Test Window"
        mock_window.isActive = True
        mock.getWindowsWithTitle.return_value = [mock_window]
        mock.getAllWindows.return_value = [mock_window]
        yield mock


@pytest.fixture
def mock_psutil():
    """Mock psutil for testing."""
    with patch("windows_computer_use_mcp.tools.portmanteau_system.psutil") as mock:
        mock_process = MagicMock()
        mock_process.name.return_value = "test.exe"
        mock_process.pid = 1234
        mock.process_iter.return_value = [mock_process]
        yield mock


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture(autouse=True)
def mock_approval():
    """Mock approval_state.is_approved to always return True for tests."""
    with patch("windows_computer_use_mcp.app.approval_state.is_approved") as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def sample_image_path(tmp_path):
    """Create a sample image file for testing."""
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test_image.png"
    img.save(img_path)
    return str(img_path)


@pytest.fixture
def mock_ocr():
    """Mock OCR functionality."""
    with patch("windows_computer_use_mcp.tools.portmanteau_visual.pytesseract") as mock:
        mock.image_to_string.return_value = "Sample OCR Text"
        mock.image_to_data.return_value = []
        yield mock


@pytest.fixture
def mock_face_recognition():
    """Mock face recognition functionality."""
    with patch("windows_computer_use_mcp.tools.portmanteau_face.face_recognition") as mock:
        mock.face_locations.return_value = [(100, 200, 300, 400)]
        mock.face_encodings.return_value = [[0.1] * 128]
        mock.compare_faces.return_value = [True]
        mock.face_distance.return_value = [0.3]
        yield mock


@pytest.fixture
def mock_cv2():
    """Mock OpenCV for testing."""
    with patch("windows_computer_use_mcp.tools.portmanteau_visual.cv2") as mock:
        mock.imread.return_value = None
        mock.imwrite.return_value = True
        mock.VideoCapture.return_value = MagicMock()
        yield mock


@pytest.fixture
def mock_pil():
    """Mock PIL/Pillow for testing."""
    with (
        patch("windows_computer_use_mcp.tools.portmanteau_visual.Image") as mock_image,
        patch("windows_computer_use_mcp.tools.portmanteau_visual.ImageGrab") as mock_grab,
    ):
        mock_img = MagicMock()
        mock_img.size = (1920, 1080)
        mock_img.save.return_value = None
        mock_image.open.return_value = mock_img
        mock_image.new.return_value = mock_img
        mock_grab.grab.return_value = mock_img


@pytest.fixture
def verify_result():
    """Helper fixture to verify ToolResult objects."""

    def _verify(result, expected_status="success", expected_keys=None, message_contains=None):
        """
        Verify ToolResult contents.

        Args:
            result: The ToolResult (or dict) to verify.
            expected_status: "success" or "error".
            expected_keys: List of keys that must be present in result.data.
            message_contains: Substring that must be in the message.
        """
        # Convert Pydantic model to dict if necessary
        res = result if isinstance(result, dict) else result.model_dump()

        assert res["status"] == expected_status, f"Expected {expected_status}, got {res['status']}"

        if message_contains:
            assert message_contains.lower() in res["message"].lower()

        if expected_status == "success":
            assert "data" in res
            if expected_keys and res["data"]:
                for key in expected_keys:
                    assert key in res["data"], f"Missing expected key '{key}' in result.data"
        elif expected_status == "error":
            assert res.get("recovery_tip") is not None, "Error result must include a recovery_tip"

        return res

    return _verify
