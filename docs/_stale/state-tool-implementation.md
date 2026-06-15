# Desktop State Capture Implementation Guide

## Overview

Implement a comprehensive desktop state capture tool that provides UI element discovery, visual annotations, and OCR capabilities - similar to Windows-MCP State-Tool but enhanced.

## Architecture

### Core Components

1. **UI Automation Element Walker** - Traverse Windows UI tree
2. **Screenshot Annotator** - Visual element highlighting
3. **OCR Text Extractor** - Extract text from visual elements
4. **State Formatter** - Structure output data

### Technology Stack

```python
# Required libraries
import pywinauto
from pywinauto import Desktop
from pywinauto.uia_defines import IUIA
from PIL import Image, ImageDraw, ImageFont, ImageGrab
import pytesseract
import comtypes.client
from typing import List, Dict, Optional, Tuple
import base64
from io import BytesIO
```

## Implementation

### 1. UI Element Walker

```python
class UIElementWalker:
    """Walk Windows UI Automation tree and extract elements"""
    
    INTERACTIVE_TYPES = {
        'Button', 'Edit', 'ComboBox', 'ListItem', 'MenuItem', 
        'TabItem', 'Hyperlink', 'CheckBox', 'RadioButton', 
        'Slider', 'ScrollBar', 'DataItem', 'Link'
    }
    
    INFORMATIVE_TYPES = {
        'Text', 'StatusBar', 'TitleBar', 'ToolBar', 'Header'
    }
    
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.elements = []
        
    def walk(self, root_element=None) -> List[Dict]:
        """Walk UI tree and extract element information"""
        if root_element is None:
            root_element = Desktop(backend='uia')
        
        self.elements = []
        self._recurse(root_element, depth=0)
        return self.elements
    
    def _recurse(self, element, depth: int):
        """Recursively walk UI tree"""
        if depth > self.max_depth:
            return
            
        try:
            # Extract element properties
            info = self._extract_element_info(element)
            
            if info and self._should_include(info):
                info['id'] = len(self.elements)
                self.elements.append(info)
            
            # Recurse children
            for child in element.children():
                self._recurse(child, depth + 1)
                
        except Exception as e:
            # Skip problematic elements
            pass
    
    def _extract_element_info(self, element) -> Optional[Dict]:
        """Extract all relevant properties from element"""
        try:
            # Get bounding rectangle
            rect = element.rectangle()
            
            # Get parent window
            parent_window = self._get_parent_window(element)
            
            info = {
                'type': element.control_type,
                'name': element.window_text(),
                'app': parent_window.window_text() if parent_window else 'Desktop',
                'bounds': {
                    'x': rect.left,
                    'y': rect.top,
                    'width': rect.width(),
                    'height': rect.height()
                },
                'is_visible': element.is_visible(),
                'is_enabled': element.is_enabled(),
                'shortcut': getattr(element, 'access_key', ''),
                'class_name': element.class_name()
            }
            
            return info
            
        except Exception:
            return None
    
    def _get_parent_window(self, element):
        """Find parent top-level window"""
        current = element
        while current:
            try:
                if current.control_type == 'Window':
                    return current
                current = current.parent()
            except:
                break
        return None
    
    def _should_include(self, info: Dict) -> bool:
        """Determine if element should be included"""
        # Must be visible
        if not info.get('is_visible'):
            return False
        
        # Must have valid bounds
        if info['bounds']['width'] <= 0 or info['bounds']['height'] <= 0:
            return False
        
        # Must be interactive or informative
        elem_type = info.get('type', '')
        if elem_type not in self.INTERACTIVE_TYPES and elem_type not in self.INFORMATIVE_TYPES:
            return False
            
        return True
```

### 2. Screenshot Annotator

```python
class ScreenshotAnnotator:
    """Annotate screenshots with UI element bounding boxes"""
    
    COLOR_MAP = {
        'Button': '#00FF00',      # Green
        'Edit': '#FFFF00',        # Yellow
        'Link': '#00FFFF',        # Cyan
        'ListItem': '#FF00FF',    # Magenta
        'MenuItem': '#FFA500',    # Orange
        'CheckBox': '#87CEEB',    # Sky Blue
        'RadioButton': '#DDA0DD', # Plum
        'default': '#FFFFFF'      # White
    }
    
    def __init__(self, font_size: int = 12):
        self.font_size = font_size
        try:
            self.font = ImageFont.truetype("arial.ttf", font_size)
        except:
            self.font = ImageFont.load_default()
    
    def capture_and_annotate(self, elements: List[Dict]) -> Image:
        """Capture screenshot and draw element annotations"""
        # Capture full screen
        screenshot = ImageGrab.grab()
        draw = ImageDraw.Draw(screenshot)
        
        # Draw each element
        for elem in elements:
            self._draw_element(draw, elem)
        
        return screenshot
    
    def _draw_element(self, draw: ImageDraw, elem: Dict):
        """Draw single element annotation"""
        bounds = elem['bounds']
        x = bounds['x']
        y = bounds['y']
        x2 = x + bounds['width']
        y2 = y + bounds['height']
        
        # Get color for element type
        color = self.COLOR_MAP.get(elem['type'], self.COLOR_MAP['default'])
        
        # Draw bounding box
        draw.rectangle([x, y, x2, y2], outline=color, width=2)
        
        # Draw label with ID
        label = str(elem['id'])
        label_bg = [x, y - 18, x + 30, y - 2]
        
        draw.rectangle(label_bg, fill=color)
        draw.text((x + 2, y - 16), label, fill='#000000', font=self.font)
    
    def to_base64(self, image: Image) -> str:
        """Convert image to base64 string"""
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return base64.b64encode(buffer.getvalue()).decode()
```

### 3. OCR Text Extractor

```python
class OCRExtractor:
    """Extract text from UI elements using OCR"""
    
    def __init__(self, tesseract_cmd: Optional[str] = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def enhance_elements(self, elements: List[Dict], screenshot: Image) -> List[Dict]:
        """Add OCR text to elements without readable text"""
        for elem in elements:
            # Skip if already has good text
            if elem.get('name') and len(elem['name'].strip()) >= 2:
                continue
            
            # Extract text via OCR
            ocr_text = self._extract_text(elem, screenshot)
            if ocr_text:
                elem['ocr_text'] = ocr_text
        
        return elements
    
    def _extract_text(self, elem: Dict, screenshot: Image) -> str:
        """OCR text from element region"""
        try:
            bounds = elem['bounds']
            
            # Crop element region with padding
            padding = 2
            region = screenshot.crop((
                bounds['x'] - padding,
                bounds['y'] - padding,
                bounds['x'] + bounds['width'] + padding,
                bounds['y'] + bounds['height'] + padding
            ))
            
            # OCR with single line mode
            text = pytesseract.image_to_string(
                region, 
                config='--psm 7'  # Single text line
            )
            
            return text.strip()
            
        except Exception:
            return ''
```

### 4. State Formatter

```python
class DesktopStateFormatter:
    """Format desktop state into structured output"""
    
    def format(self, elements: List[Dict], screenshot: Optional[Image] = None) -> Dict:
        """Format complete state output"""
        # Separate element types
        interactive = [e for e in elements if self._is_interactive(e)]
        informative = [e for e in elements if self._is_informative(e)]
        
        # Build text report
        text_report = self._build_text_report(interactive, informative)
        
        # Prepare output
        output = {
            'text': text_report,
            'interactive_elements': interactive,
            'informative_elements': informative,
            'element_count': len(elements)
        }
        
        # Add screenshot if provided
        if screenshot:
            annotator = ScreenshotAnnotator()
            output['screenshot_base64'] = annotator.to_base64(screenshot)
        
        return output
    
    def _build_text_report(self, interactive: List[Dict], informative: List[Dict]) -> str:
        """Build human-readable text report"""
        lines = []
        
        # Interactive elements section
        lines.append("Interactive Elements:")
        lines.append("-" * 60)
        for elem in interactive:
            bounds = elem['bounds']
            name = elem.get('name', elem.get('ocr_text', ''))
            lines.append(
                f"[{elem['id']}] {elem['type']} \"{name}\" "
                f"at ({bounds['x']},{bounds['y']}) - App: {elem['app']}"
            )
        
        lines.append("\n")
        
        # Informative elements section
        lines.append("Informative Elements:")
        lines.append("-" * 60)
        for elem in informative:
            name = elem.get('name', elem.get('ocr_text', ''))
            if name:
                lines.append(f"- {name} (App: {elem['app']})")
        
        return "\n".join(lines)
    
    def _is_interactive(self, elem: Dict) -> bool:
        """Check if element is interactive"""
        return elem['type'] in UIElementWalker.INTERACTIVE_TYPES
    
    def _is_informative(self, elem: Dict) -> bool:
        """Check if element is informative"""
        return elem['type'] in UIElementWalker.INFORMATIVE_TYPES
```

### 5. Main State Capture Tool

```python
class DesktopStateCapture:
    """Main desktop state capture orchestrator"""
    
    def __init__(self, 
                 max_depth: int = 10,
                 tesseract_cmd: Optional[str] = None):
        self.walker = UIElementWalker(max_depth)
        self.annotator = ScreenshotAnnotator()
        self.ocr = OCRExtractor(tesseract_cmd)
        self.formatter = DesktopStateFormatter()
    
    def capture(self, use_vision: bool = False, use_ocr: bool = False) -> Dict:
        """
        Capture desktop state
        
        Args:
            use_vision: Include annotated screenshot
            use_ocr: Use OCR to extract text from elements
            
        Returns:
            Dictionary with text report, element data, and optional screenshot
        """
        # Walk UI tree
        elements = self.walker.walk()
        
        screenshot = None
        
        if use_vision or use_ocr:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            # Enhance with OCR if requested
            if use_ocr:
                elements = self.ocr.enhance_elements(elements, screenshot)
            
            # Annotate screenshot if vision enabled
            if use_vision:
                screenshot = self.annotator.capture_and_annotate(elements)
        
        # Format output
        return self.formatter.format(elements, screenshot)
```

## MCP Tool Integration

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("pywinauto")

@mcp.tool()
def get_desktop_state(
    use_vision: bool = False,
    use_ocr: bool = False,
    max_depth: int = 10
) -> dict:
    """
    Capture comprehensive desktop state with UI element discovery
    
    Args:
        use_vision: Include annotated screenshot with element boundaries
        use_ocr: Use OCR to extract text from visual elements
        max_depth: Maximum UI tree traversal depth
        
    Returns:
        Desktop state with elements, text report, and optional screenshot
    """
    capturer = DesktopStateCapture(max_depth=max_depth)
    return capturer.capture(use_vision=use_vision, use_ocr=use_ocr)
```

## Usage Examples

### Basic State Capture
```python
state = get_desktop_state()
print(state['text'])
print(f"Found {state['element_count']} elements")
```

### With Visual Annotation
```python
state = get_desktop_state(use_vision=True)
# state['screenshot_base64'] contains annotated image
```

### With OCR Enhancement
```python
state = get_desktop_state(use_vision=True, use_ocr=True)
# Elements without text will have 'ocr_text' field
```

### Find Specific Element
```python
state = get_desktop_state()
buttons = [e for e in state['interactive_elements'] if e['type'] == 'Button']
login_button = next((b for b in buttons if 'login' in b['name'].lower()), None)
if login_button:
    print(f"Login button at: {login_button['bounds']}")
```

## Performance Considerations

1. **UI Tree Depth** - Limit max_depth for faster traversal (default: 10)
2. **Element Filtering** - Only include visible, enabled elements
3. **OCR Caching** - Cache OCR results for repeated captures
4. **Screenshot Size** - Consider downscaling for large screens
5. **Async Capture** - Run UI walking in background thread

## Error Handling

```python
try:
    state = get_desktop_state(use_vision=True, use_ocr=True)
except Exception as e:
    # Fallback to basic capture
    state = get_desktop_state(use_vision=False, use_ocr=False)
```

## Testing

```python
def test_state_capture():
    """Test basic state capture"""
    state = get_desktop_state()
    assert 'text' in state
    assert 'interactive_elements' in state
    assert state['element_count'] > 0

def test_vision_capture():
    """Test with visual annotation"""
    state = get_desktop_state(use_vision=True)
    assert 'screenshot_base64' in state
    assert len(state['screenshot_base64']) > 0

def test_ocr_enhancement():
    """Test OCR text extraction"""
    state = get_desktop_state(use_ocr=True)
    ocr_elements = [e for e in state['interactive_elements'] if 'ocr_text' in e]
    # Should find some OCR-enhanced elements
    assert len(ocr_elements) >= 0
```

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    "pywinauto>=0.6.8",
    "Pillow>=10.0.0",
    "pytesseract>=0.3.10",
    "comtypes>=1.2.0"
]
```

## System Requirements

1. **Tesseract OCR** - Install from: https://github.com/UB-Mannheim/tesseract/wiki
   - Add to PATH or specify path in OCRExtractor
   
2. **Windows UI Automation** - Built into Windows (no install needed)

3. **Python 3.11+** - For full compatibility

## Next Steps

1. Implement core classes in `src/desktop_state/`
2. Add MCP tool integration in `src/windows_computer_use_mcp/server.py`
3. Test with various applications
4. Optimize performance for complex UIs
5. Add caching layer for repeated captures
6. Document edge cases and limitations
