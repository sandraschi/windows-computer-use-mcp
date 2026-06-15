# Desktop State Capture Tool Documentation

## Overview

The `get_desktop_state` tool provides comprehensive Windows UI element discovery, visual annotations, and OCR text extraction capabilities. This tool serves as an advanced Windows automation assistant, similar to Windows-MCP State-Tool but enhanced with additional features.

## Features

### 🏗️ **Core Capabilities**
- **Complete UI Tree Traversal**: Discovers all interactive and informative elements
- **Intelligent Element Classification**: Automatically categorizes buttons, inputs, text, etc.
- **Visual Annotations**: Color-coded element boundaries on screenshots
- **OCR Text Extraction**: Extracts text from visual elements without accessible text
- **Structured Output**: JSON-formatted results perfect for AI processing

### 🚀 **Revolutionary Deep IDE Inspection**
- **IDE State Analysis**: Inspects open Cursor/VSCode instances for development status
- **Error Detection**: Discovers linter errors, syntax issues, and code quality problems
- **File Content Access**: Reads open file contents through UI element discovery
- **Development Monitoring**: Tracks coding activity and project health indicators
- **Repository Awareness**: Identifies current projects and open repositories

#### **How Deep IDE Inspection Works**

The Desktop State tool uses Windows UI Automation (UIA) to perform deep introspection of development environments:

1. **UI Tree Traversal**: Starting from the Desktop, recursively walks all visible windows and their child elements
2. **IDE Detection**: Identifies Cursor/VSCode windows by class name and window text patterns
3. **Element Discovery**: Extracts all UI elements within IDE windows (tabs, editors, panels, status bars)
4. **Content Analysis**: Reads text content from editor areas, error panels, and status indicators
5. **Context Mapping**: Correlates elements to understand file states, error locations, and project structure

**Technical Implementation**:
- **Backend**: PyWinAuto UIA (UI Automation) for comprehensive element access
- **Traversal**: Recursive depth-first search with configurable depth limits
- **Classification**: Intelligent categorization of interactive vs informative elements
- **Text Extraction**: Direct text property access and OCR fallback for visual elements

**What Gets Discovered**:
- Open file names and paths in tabs
- Syntax errors and linter warnings in error panels
- Current cursor position and selection
- Git status indicators and branch information
- Terminal/command output in integrated terminals
- Extension status and notifications

### 🎨 **Visual Intelligence**
- **Element Highlighting**: Different colors for different element types
- **Boundary Detection**: Precise element positioning and sizing
- **Screenshot Integration**: Full desktop or window capture
- **Base64 Encoding**: Web-ready image transmission

### 📝 **OCR Enhancement**
- **Smart Text Detection**: Only processes elements lacking readable text
- **Region-Based Processing**: Crops element areas for accurate OCR
- **Fallback Support**: Graceful degradation when OCR is unavailable
- **Multi-language Support**: Configurable OCR language settings

## Tool Signature

```python
get_desktop_state(
    use_vision: bool = False,
    use_ocr: bool = False,
    max_depth: int = 10,
    element_timeout: float = 0.5
) -> Dict[str, Any]
```

## Parameters

### `use_vision` (boolean, default: False)
- **Purpose**: Include annotated screenshot with element boundaries
- **When to Use**: When you need visual context or element positioning
- **Impact**: Adds ~372KB base64-encoded PNG to response
- **Example**: `use_vision=True`

### `use_ocr` (boolean, default: False)
- **Purpose**: Extract text from visual elements using Tesseract OCR
- **When to Use**: When elements don't have accessible text properties
- **Requirements**: Tesseract OCR installed on system
- **Example**: `use_ocr=True`

### `max_depth` (integer, default: 10)
- **Purpose**: Maximum depth for UI tree traversal
- **Range**: 1-50 (higher = more elements, slower performance)
- **Recommendation**: Start with 10, increase only if needed
- **Example**: `max_depth=15`

### `element_timeout` (float, default: 0.5)
- **Purpose**: Timeout in seconds for processing each UI element
- **When to Use**: When dealing with slow-responding applications like complex IDEs (Cursor, VSCode)
- **Impact**: Lower values (0.1-0.3) are faster but may skip slow elements; higher values (0.5-1.0) are more thorough
- **Recommendation**: Use 0.2 for fast scans, 0.5-0.8 for comprehensive IDE analysis
- **Example**: `element_timeout=0.2` (fast), `element_timeout=0.8` (thorough)

## Return Format

```json
{
  "text": "Interactive Elements:\n-------------------\n[0] Button \"OK\" at (500,300) - App: Notepad\n[1] Edit \"Type here\" at (100,100) - App: Word\n\nInformative Elements:\n-------------------\n- Welcome to Windows (App: Desktop)\n- File Edit View (App: Word)",
  "interactive_elements": [
    {
      "id": 0,
      "type": "Button",
      "name": "OK",
      "app": "Notepad",
      "bounds": {"x": 500, "y": 300, "width": 80, "height": 25},
      "is_visible": true,
      "is_enabled": true,
      "class_name": "Button"
    }
  ],
  "informative_elements": [
    {
      "id": 1,
      "type": "Text",
      "name": "Welcome to Windows",
      "app": "Desktop",
      "bounds": {"x": 10, "y": 10, "width": 200, "height": 20},
      "is_visible": true,
      "is_enabled": true
    }
  ],
  "element_count": 15,
  "screenshot_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

## Usage Examples

### Basic UI Discovery
```python
# Simple element discovery
state = get_desktop_state()
print(f"Found {state['element_count']} elements")
print(state['text'])  # Human-readable summary
```

### Visual Analysis
```python
# With visual annotations
state = get_desktop_state(use_vision=True)

# Save annotated screenshot
import base64
with open('desktop_analysis.png', 'wb') as f:
    f.write(base64.b64decode(state['screenshot_base64']))
```

### Complete Analysis
```python
# Full analysis with OCR and deep traversal
state = get_desktop_state(
    use_vision=True,
    use_ocr=True,
    max_depth=20
)

# Access specific element types
buttons = [e for e in state['interactive_elements'] if e['type'] == 'Button']
text_fields = [e for e in state['interactive_elements'] if e['type'] == 'Edit']
```

### Smart Element Selection
```python
state = get_desktop_state()

# Find login button
login_buttons = [
    e for e in state['interactive_elements']
    if e['type'] == 'Button' and 'login' in e.get('name', '').lower()
]

if login_buttons:
    login_btn = login_buttons[0]
    print(f"Login button at: {login_btn['bounds']}")
    # Use with click_element tool
```

## Element Types

### Interactive Elements
- **Button**: Clickable buttons and controls
- **Edit**: Text input fields
- **ComboBox**: Dropdown selection controls
- **ListItem**: Items in lists and trees
- **MenuItem**: Menu options and context items
- **TabItem**: Tab controls
- **Hyperlink**: Clickable links
- **CheckBox/RadioButton**: Selection controls
- **Slider/ScrollBar**: Range and scrolling controls

### Informative Elements
- **Text**: Static text labels and content
- **StatusBar**: Status information displays
- **TitleBar**: Window title information
- **ToolBar**: Toolbar elements
- **Header**: Column headers and labels

## Color Coding (Visual Mode)

| Element Type | Color | Hex Code |
|-------------|--------|----------|
| Button | Green | #00FF00 |
| Edit | Yellow | #FFFF00 |
| Link | Cyan | #00FFFF |
| ListItem | Magenta | #FF00FF |
| MenuItem | Orange | #FFA500 |
| CheckBox | Sky Blue | #87CEEB |
| RadioButton | Plum | #DDA0DD |
| Default | White | #FFFFFF |

## Performance Considerations

### Optimization Strategies
1. **Depth Limiting**: Use appropriate `max_depth` (default: 10)
2. **Feature Selection**: Only enable `use_vision`/`use_ocr` when needed
3. **Element Filtering**: Focus on specific applications when possible
4. **Caching**: Cache results for repeated analysis of stable UIs

### Performance Metrics
- **Basic Mode**: < 2 seconds (UI traversal only)
- **Vision Mode**: < 5 seconds (includes screenshot + annotation)
- **OCR Mode**: < 10 seconds (includes OCR processing)
- **Full Mode**: < 15 seconds (all features enabled)

## Error Handling

### Common Issues
```python
try:
    state = get_desktop_state(use_vision=True, use_ocr=True)
except Exception as e:
    print(f"Analysis failed: {e}")
    # Fallback to basic mode
    state = get_desktop_state()
```

### Graceful Degradation
- **OCR Unavailable**: Falls back to elements with accessible text
- **Screenshot Failure**: Continues without visual annotations
- **UI Access Denied**: Skips inaccessible windows/elements
- **Memory Issues**: Processes elements in batches for large UIs

## Integration Examples

### With Click Element Tool
```python
# Get desktop state
state = get_desktop_state()

# Find and click OK button
ok_buttons = [
    e for e in state['interactive_elements']
    if e['type'] == 'Button' and e.get('name') == 'OK'
]

if ok_buttons:
    btn = ok_buttons[0]
    click_element(
        window_handle=btn['app'],  # This needs proper window handle mapping
        control_id=btn.get('class_name')
    )
```

### With Screenshot Analysis
```python
# Capture desktop state with vision
state = get_desktop_state(use_vision=True)

# The screenshot_base64 can be:
# 1. Saved to file for manual inspection
# 2. Sent to vision AI models for analysis
# 3. Used in automated testing frameworks
```

### Automated Workflow
```python
def automate_login(username: str, password: str):
    """Automated login using desktop state analysis"""

    # Analyze current desktop
    state = get_desktop_state()

    # Find username field
    username_fields = [
        e for e in state['interactive_elements']
        if e['type'] == 'Edit' and 'user' in e.get('name', '').lower()
    ]

    if username_fields:
        # Focus on username field and type
        # (Additional automation logic here)
        pass

    # Similar logic for password field and login button
```

## System Requirements

### Windows Requirements
- **Windows 10/11** with UI Automation support
- **Administrator privileges** recommended for full UI access
- **64-bit Python** for best compatibility

### Software Dependencies
- **Tesseract OCR** (for OCR features)
  - Download: https://github.com/UB-Mannheim/tesseract/wiki
  - Add to system PATH
- **Python packages** automatically included in DXT build

### Hardware Recommendations
- **RAM**: 4GB+ for large desktop analysis
- **CPU**: Multi-core recommended for OCR processing
- **Storage**: 500MB+ free space for temporary files

## Troubleshooting

### Common Issues

#### "No elements found"
- Check if target application is running
- Ensure application windows are not minimized
- Try running with administrator privileges
- Verify UI Automation is enabled in Windows

#### "OCR not working"
- Install Tesseract OCR and add to PATH
- Check if `tesseract` command is available in terminal
- Verify PIL/Pillow is properly installed
- Try without OCR first (`use_ocr=False`)

#### "Screenshot failed"
- Ensure no other applications are capturing screen
- Check Windows display settings
- Try running without vision (`use_vision=False`)
- Verify PIL/Pillow installation

#### "Access denied errors"
- Run as administrator
- Check Windows UAC settings
- Ensure target applications allow UI automation
- Try with different applications

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with minimal settings first
state = get_desktop_state(max_depth=5)
print(f"Basic analysis: {state['element_count']} elements")

# Gradually add features
state = get_desktop_state(use_vision=True, max_depth=5)
state = get_desktop_state(use_ocr=True, max_depth=5)
```

## Advanced Usage

### Custom Element Filtering
```python
def filter_elements(state, app_name=None, element_type=None):
    """Filter elements by application and type"""
    elements = state['interactive_elements']

    if app_name:
        elements = [e for e in elements if app_name.lower() in e.get('app', '').lower()]

    if element_type:
        elements = [e for e in elements if e['type'] == element_type]

    return elements

# Usage
state = get_desktop_state()
notepad_buttons = filter_elements(state, app_name='notepad', element_type='Button')
```

### Batch Processing
```python
def analyze_multiple_apps(app_names):
    """Analyze multiple applications"""
    results = {}

    for app_name in app_names:
        # Focus analysis on specific app (would need window filtering logic)
        state = get_desktop_state(use_vision=True)
        results[app_name] = state

    return results
```

## API Reference

### REST Endpoint
```
POST /api/v1/desktop_state/capture
Content-Type: application/json

{
  "use_vision": true,
  "use_ocr": false,
  "max_depth": 10
}
```

### Response Schema
```typescript
interface DesktopStateResponse {
  text: string;                    // Human-readable summary
  interactive_elements: Element[]; // Clickable/actionable elements
  informative_elements: Element[]; // Text/display elements
  element_count: number;           // Total element count
  screenshot_base64?: string;      // Base64 PNG (if use_vision=true)
}

interface Element {
  id: number;                      // Unique element identifier
  type: string;                    // Element type (Button, Edit, etc.)
  name?: string;                   // Element name/text
  app: string;                     // Parent application name
  bounds: {                        // Screen coordinates
    x: number;
    y: number;
    width: number;
    height: number;
  };
  is_visible: boolean;             // Visibility status
  is_enabled: boolean;             // Enabled status
  class_name?: string;             // Windows class name
  ocr_text?: string;               // OCR-extracted text (if applicable)
}
```

## Future Enhancements

### Planned Features
- **Element Change Detection**: Compare desktop states over time
- **Accessibility Analysis**: WCAG compliance checking
- **Automated Testing**: Generate test scripts from analysis
- **Multi-Monitor Support**: Extended multi-display analysis
- **Performance Profiling**: UI responsiveness metrics

### Integration Opportunities
- **Test Automation**: Selenium/Appium-style element selection
- **Accessibility Tools**: Screen reader integration
- **Workflow Automation**: Macro generation from user actions
- **Quality Assurance**: Automated UI testing frameworks

---

## Support

For issues or questions about the desktop state capture tool:

1. **Check Documentation**: Review this guide and examples
2. **Test Incrementally**: Start with basic mode, add features gradually
3. **Review Logs**: Enable debug logging for troubleshooting
4. **Community Support**: Create issues with detailed reproduction steps

The desktop state capture tool provides comprehensive Windows UI analysis capabilities, making it an essential component of the Windows Computer Use automation ecosystem.
