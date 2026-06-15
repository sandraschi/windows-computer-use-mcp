# Windows Computer Use Test Suite

Comprehensive test harness for Windows Computer Use server.

## E2E (LibreOffice Calc — Cua parity)

Requires LibreOffice `soffice` (same install as **libreoffice-mcp**). Default pytest **excludes** e2e (`-m "not e2e"`).

```powershell
uv run pytest -m e2e -v --no-cov
```

Optional: `$env:PYWINAUTO_E2E_SOFFICE = "C:\Program Files\LibreOffice\program\soffice.exe"`

Tests live under `tests/e2e/` and set `WINDOWS_COMPUTER_USE_MCP_LOOSE_UIA=1` for LibreOffice UIA nodes.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_basic_tools.py      # Tests for basic tools (health_check, get_help)
├── test_window_tools.py     # Tests for window management tools
├── test_mouse_tools.py      # Tests for mouse control tools
├── test_system_tools.py     # Tests for system-level tools
├── test_app_integration.py  # Integration tests for app initialization
├── test_face_recognition.py # Tests for face recognition (existing)
└── test_images/             # Test images for face recognition
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=src/windows_computer_use_mcp --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_basic_tools.py
```

### Run specific test
```bash
pytest tests/test_basic_tools.py::TestHealthCheck::test_health_check_returns_healthy_status
```

### Run with markers
```bash
# Run only unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"

# Run only Windows-specific tests
pytest -m windows_only
```

## Test Categories

### Unit Tests
- Test individual tool functions in isolation
- Use mocks for Windows API calls
- Fast execution
- No external dependencies

### Integration Tests
- Test tool interactions
- Test app initialization
- Test module imports
- May require some system access

### Windows-Specific Tests
- Tests that require Windows OS
- May need actual window access
- Marked with `@pytest.mark.windows_only`

## Fixtures

Common fixtures available in `conftest.py`:

- `app_instance`: FastMCP app instance
- `mock_window`: Mock window object
- `mock_element`: Mock UI element
- `mock_pyautogui`: Mocked pyautogui
- `mock_pywinauto`: Mocked pywinauto
- `mock_pygetwindow`: Mocked pygetwindow
- `temp_test_dir`: Temporary directory for test files
- `sample_image_path`: Sample image file for testing

## Writing New Tests

1. **Use fixtures** from `conftest.py` when possible
2. **Mock Windows APIs** - don't rely on actual windows being open
3. **Test error cases** - ensure proper error handling
4. **Use descriptive names** - `test_function_name_scenario`
5. **Group related tests** in classes
6. **Add markers** for test categorization

### Example Test

```python
class TestMyTool:
    """Tests for my_tool."""
    
    @patch('windows_computer_use_mcp.tools.my_module.some_dependency')
    def test_my_tool_success(self, mock_dep, app_instance):
        """Test my_tool with successful execution."""
        from windows_computer_use_mcp.tools.my_module import my_tool
        
        mock_dep.return_value = "expected_result"
        
        result = my_tool(param="value")
        
        assert isinstance(result, dict)
        assert "success" in result
```

## Coverage Goals

- **Minimum**: 30% (enforced by pytest.ini)
- **Target**: 70%+
- **Current**: Check with `pytest --cov-report=term-missing`

## Continuous Integration

Tests run automatically on:
- Push to main/master/develop branches
- Pull requests
- Multiple Python versions (3.10, 3.11, 3.12)
- Windows environment

## Troubleshooting

### Import Errors
- Ensure `src/` is in Python path
- Check that all dependencies are installed
- Verify `conftest.py` is in tests directory

### Mock Issues
- Ensure mocks are patched before imports
- Check patch paths match actual import paths
- Verify mock return values match expected types

### Windows-Specific Failures
- Some tests require Windows OS
- Use `@pytest.mark.windows_only` marker
- Skip on non-Windows: `pytest -m "not windows_only"`

