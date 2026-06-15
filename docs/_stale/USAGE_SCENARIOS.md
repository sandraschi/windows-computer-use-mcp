# Windows Computer Use - Usage Scenarios & Patterns

**Target:** AI Agents, Claude Desktop, MCP Clients  
**Platform:** Windows 10/11 only

> **Opt-in tools:** `automation_face` and `global_keylogger` are **not registered** in default installs. Scenarios below that mention them require env flags — see [SAFETY.md](SAFETY.md) and [README.md](../README.md).

---

## Why This Server Is Powerful (And Non-Obvious)

Windows Computer Use provides **programmatic control of the Windows desktop** through an MCP interface. This means Claude (or any MCP client) can:

1. **See everything on your screen** - List windows, read UI elements, extract text via OCR
2. **Interact with any application** - Click buttons, type text, navigate menus
3. **Automate complex workflows** - Chain operations across multiple apps
4. **Provide accessibility insights** - Deep UI element tree inspection
5. **Optional local face unlock** - Only if you enable `automation_face` (not default)

The key insight: **Claude becomes a Windows power user** who can see and interact with your desktop like a remote assistant.

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Scenario: Desktop Discovery](#scenario-desktop-discovery)
3. [Scenario: Application Automation](#scenario-application-automation)
4. [Scenario: Form Filling](#scenario-form-filling)
5. [Scenario: Window Management](#scenario-window-management)
6. [Scenario: Visual Intelligence](#scenario-visual-intelligence)
7. [Scenario: Face Recognition Security](#scenario-face-recognition-security)
8. [Scenario: Cross-Application Workflow](#scenario-cross-application-workflow)
9. [Scenario: Accessibility Testing](#scenario-accessibility-testing)
10. [Advanced Patterns](#advanced-patterns)
11. [Error Handling Strategies](#error-handling-strategies)
12. [Performance Optimization](#performance-optimization)

---

## Quick Reference

### Tool Overview

| Tool | Purpose | Key Operations |
|------|---------|----------------|
| `automation_windows` | Window management | list, find, maximize, minimize, activate, position |
| `automation_elements` | UI interaction | click, hover, text, set_text, wait, verify |
| `automation_mouse` | Mouse control | move, click, scroll, drag |
| `automation_keyboard` | Keyboard input | type, press, hotkey |
| `automation_visual` | Vision/OCR | screenshot, extract_text, find_image |
| `automation_face` | Face recognition (**opt-in**) | add, recognize, capture, list |
| `automation_system` | System utilities | health, wait, clipboard, process_list |
| `get_desktop_state` | UI tree discovery | Full element hierarchy with OCR |

### Common Invocation Pattern

```python
# All portmanteau tools follow this pattern:
result = tool_name("operation", param1=value1, param2=value2)

# Example:
result = automation_windows("find", title="Notepad", partial=True)
```

---

## Scenario: Desktop Discovery

### Problem
"What's currently running on my Windows desktop? What can I interact with?"

### Solution: Full Desktop Enumeration

```python
# Step 1: List all visible windows
windows = automation_windows("list")
# Returns: window handles, titles, class names, visibility states

# Step 2: Get comprehensive UI state
state = get_desktop_state()
# Returns: Complete element tree, accessibility info

# Step 3: Deep analysis with OCR
detailed_state = get_desktop_state(use_vision=True, use_ocr=True, max_depth=15)
# Returns: Element tree + visual annotations + all visible text
```

### Practical Example: "What Applications Am I Working With?"

**User Prompt:**
> "Tell me what's open on my desktop and what I'm working on"

**Claude's Approach:**
1. Call `automation_windows("list")` to get all windows
2. Call `get_desktop_state(use_ocr=True)` for deep inspection
3. Synthesize results: "You have VS Code open with `project.py`, Chrome showing GitHub, and Outlook with 3 unread emails"

### Output Interpretation

The `get_desktop_state` tool returns structured data:

```json
{
  "windows": [
    {
      "handle": 12345,
      "title": "Document.docx - Microsoft Word",
      "class_name": "OpusApp",
      "elements": [
        {"type": "Button", "name": "Save", "automationId": "SaveButton"},
        {"type": "Edit", "name": "Document Content", "value": "...text..."}
      ]
    }
  ],
  "ocr_text": ["Save", "File", "Edit", "Your document text here..."],
  "active_window": 12345
}
```

---

## Scenario: Application Automation

### Problem
"I need to automate interactions with a specific Windows application"

### Solution: Targeted Application Control

```python
# Step 1: Find the target application
notepad = automation_windows("find", title="Notepad", partial=True)
handle = notepad["windows"][0]["handle"]

# Step 2: Activate it (bring to foreground)
automation_windows("activate", handle=handle)

# Step 3: Get its UI elements
elements = get_desktop_state(use_vision=False)  # Focused on active window

# Step 4: Interact with elements
automation_elements("click", window_handle=handle, control_id="Edit1")
automation_keyboard("type", text="Hello from Claude!")
```

### Practical Example: Notepad Automation

**User Prompt:**
> "Open Notepad, write a reminder about tomorrow's meeting, and save it as meeting-notes.txt"

**Claude's Approach:**

```python
# 1. Launch Notepad (via system command or Start menu)
automation_keyboard("hotkey", keys=["win", "r"])
automation_keyboard("type", text="notepad")
automation_keyboard("press", key="enter")

# 2. Wait for Notepad to open
automation_system("wait", seconds=1.0)

# 3. Find and activate Notepad
notepad = automation_windows("find", title="Untitled - Notepad")
handle = notepad["windows"][0]["handle"]
automation_windows("activate", handle=handle)

# 4. Type the content
automation_keyboard("type", text="REMINDER: Meeting tomorrow at 2pm\n\nAgenda:\n- Project status\n- Q4 planning")

# 5. Save the file (Ctrl+S)
automation_keyboard("hotkey", keys=["ctrl", "s"])

# 6. Wait for Save dialog
automation_system("wait", seconds=0.5)

# 7. Type filename and save
automation_keyboard("type", text="meeting-notes.txt")
automation_keyboard("press", key="enter")
```

---

## Scenario: Form Filling

### Problem
"I need to fill out forms in Windows applications automatically"

### Solution: Element-Based Form Interaction

```python
# Get window handle first
app = automation_windows("find", title="Application Form")
handle = app["windows"][0]["handle"]

# Fill each field by control ID or name
automation_elements("set_text", window_handle=handle, control_id="NameField", text="John Doe")
automation_elements("set_text", window_handle=handle, control_id="EmailField", text="john@example.com")

# Select dropdown values
automation_elements("click", window_handle=handle, control_id="CountryDropdown")
automation_keyboard("type", text="United States")
automation_keyboard("press", key="enter")

# Check checkboxes
automation_elements("click", window_handle=handle, control_id="AgreeCheckbox")

# Submit
automation_elements("click", window_handle=handle, control_id="SubmitButton")
```

### Finding Element IDs

When you don't know the control IDs:

```python
# Use desktop state to discover elements
state = get_desktop_state(use_vision=True)

# Look for elements with names/automationIds matching your target
# The returned element tree shows all interactive elements

# Alternatively, click by position if you know coordinates
automation_elements("click", x=300, y=450)  # Click at specific coordinates
```

---

## Scenario: Window Management

### Problem
"I need to organize my desktop - arrange windows, manage multiple monitors"

### Solution: Window Layout Control

```python
# Get all windows
windows = automation_windows("list")

# Arrange windows side by side
# Left half of screen (assuming 1920x1080)
automation_windows("position", handle=window1_handle, x=0, y=0, width=960, height=1080)
# Right half
automation_windows("position", handle=window2_handle, x=960, y=0, width=960, height=1080)

# Minimize all except active
for w in windows["windows"]:
    if w["handle"] != active_handle:
        automation_windows("minimize", handle=w["handle"])

# Cascade windows
y_offset = 0
for i, w in enumerate(windows["windows"]):
    automation_windows("position", handle=w["handle"], x=i*30, y=y_offset, width=800, height=600)
    y_offset += 30
```

### Practical Example: Focus Mode

**User Prompt:**
> "Set up focus mode - maximize VS Code, minimize everything else"

**Claude's Approach:**

```python
# Find VS Code
vscode = automation_windows("find", title="Visual Studio Code", partial=True)
vscode_handle = vscode["windows"][0]["handle"]

# Get all windows
all_windows = automation_windows("list")

# Minimize everything except VS Code
for w in all_windows["windows"]:
    if w["handle"] != vscode_handle and w["is_visible"]:
        automation_windows("minimize", handle=w["handle"])

# Maximize VS Code
automation_windows("maximize", handle=vscode_handle)
automation_windows("activate", handle=vscode_handle)
```

---

## Scenario: Visual Intelligence

### Problem
"I need to extract text from screen, find visual elements, or take screenshots"

### Solution: Vision & OCR Operations

```python
# Take a screenshot of the entire screen
screenshot = automation_visual("screenshot")
# Returns: path to saved image

# Screenshot specific window
screenshot = automation_visual("screenshot", window_handle=handle, return_base64=True)
# Returns: Base64-encoded image

# Extract all text from screen via OCR
text = automation_visual("extract_text")
# Returns: List of extracted text strings with positions

# Extract text from specific image
text = automation_visual("extract_text", image_path="screenshot.png")

# Find image on screen (template matching)
location = automation_visual("find_image", template_path="button.png", threshold=0.8)
# Returns: x, y coordinates if found
```

### Practical Example: Reading Non-Accessible Content

**User Prompt:**
> "What does that error dialog say? I can't copy the text"

**Claude's Approach:**

```python
# Take screenshot of active window
screenshot = automation_visual("screenshot", return_base64=True)

# Extract text via OCR
text = automation_visual("extract_text")

# Report findings
# "The dialog says: 'Error 0x80070005: Access Denied. Please run as administrator.'"
```

### Finding UI Elements Visually

When accessibility APIs fail:

```python
# Save a template image of the button you want to click
# Then find it on screen
location = automation_visual("find_image", template_path="save_button.png")

if location["found"]:
    automation_mouse("click", x=location["x"], y=location["y"])
```

---

## Scenario: Face Recognition Security

### Problem
"Add biometric security to sensitive automation workflows"

### Solution: Face-Gated Operations

```python
# First, register authorized users
automation_face("add", name="admin_user", image_path="admin_photo.jpg")

# Before sensitive operations, verify identity
captured = automation_face("capture", camera_index=0)  # Take photo from webcam
result = automation_face("recognize", image_path=captured["image_path"])

if result["recognized"] and result["name"] == "admin_user":
    # Proceed with sensitive operation
    automation_system("clipboard_set", text="CONFIDENTIAL: API_KEY=xyz123")
else:
    # Deny access
    print("Access denied - unrecognized face")
```

### Face Recognition Operations

```python
# Add a face to the database
automation_face("add", name="John Doe", image_path="john_photo.jpg")

# List all registered faces
faces = automation_face("list")

# Recognize a face
result = automation_face("recognize", image_path="unknown_person.jpg")
# Returns: {"recognized": True, "name": "John Doe", "confidence": 0.95}

# Delete a registered face
automation_face("delete", name="John Doe")
```

---

## Scenario: Cross-Application Workflow

### Problem
"I need to orchestrate a workflow spanning multiple applications"

### Solution: Multi-App Automation Chain

### Practical Example: Copy Data Between Apps

**User Prompt:**
> "Copy the table from Excel and paste it into Word"

**Claude's Approach:**

```python
# Step 1: Find and activate Excel
excel = automation_windows("find", title="Excel", partial=True)
excel_handle = excel["windows"][0]["handle"]
automation_windows("activate", handle=excel_handle)

# Step 2: Select all data (Ctrl+A)
automation_keyboard("hotkey", keys=["ctrl", "a"])
automation_system("wait", seconds=0.3)

# Step 3: Copy (Ctrl+C)
automation_keyboard("hotkey", keys=["ctrl", "c"])
automation_system("wait", seconds=0.3)

# Step 4: Find and activate Word
word = automation_windows("find", title="Word", partial=True)
word_handle = word["windows"][0]["handle"]
automation_windows("activate", handle=word_handle)

# Step 5: Paste (Ctrl+V)
automation_keyboard("hotkey", keys=["ctrl", "v"])
```

### Practical Example: Report Generation Pipeline

```python
# 1. Export data from database app
db_app = automation_windows("find", title="DatabaseClient")
automation_windows("activate", handle=db_app["windows"][0]["handle"])
automation_keyboard("hotkey", keys=["ctrl", "e"])  # Export shortcut
automation_system("wait", seconds=2.0)  # Wait for export dialog
automation_keyboard("type", text="report_data.csv")
automation_keyboard("press", key="enter")

# 2. Open in Excel for formatting
automation_keyboard("hotkey", keys=["win", "r"])
automation_keyboard("type", text="excel report_data.csv")
automation_keyboard("press", key="enter")
automation_system("wait", seconds=3.0)

# 3. Apply formatting macro
excel = automation_windows("find", title="Excel")
automation_windows("activate", handle=excel["windows"][0]["handle"])
automation_keyboard("hotkey", keys=["alt", "f8"])  # Macro dialog
automation_keyboard("type", text="FormatReport")
automation_keyboard("press", key="enter")

# 4. Save as PDF
automation_keyboard("hotkey", keys=["ctrl", "shift", "s"])
automation_system("wait", seconds=0.5)
automation_keyboard("type", text="Final_Report.pdf")
automation_keyboard("press", key="enter")
```

---

## Scenario: Accessibility Testing

### Problem
"I need to audit an application's accessibility compliance"

### Solution: Deep UI Inspection

```python
# Get full element tree
state = get_desktop_state(max_depth=20, use_vision=True, use_ocr=True)

# Analyze for accessibility issues:

# 1. Find elements without names (accessibility labels)
for window in state["windows"]:
    for element in window["elements"]:
        if not element.get("name") or element["name"] == "":
            print(f"ISSUE: Unnamed element of type {element['type']}")

# 2. Check for keyboard accessibility
for element in all_elements:
    if element["type"] == "Button" and not element.get("is_keyboard_focusable"):
        print(f"ISSUE: Button not keyboard accessible: {element}")

# 3. Verify text contrast (requires OCR + vision)
# OCR confidence scores can indicate contrast issues
for text_region in state["ocr_results"]:
    if text_region["confidence"] < 0.7:
        print(f"ISSUE: Possible contrast issue at {text_region['location']}")
```

---

## Advanced Patterns

### Pattern 1: Robust Element Interaction

```python
def click_element_robust(handle, control_id, timeout=10.0):
    """Click an element with retry and fallback logic."""
    
    # Try by control ID first
    result = automation_elements("click", window_handle=handle, control_id=control_id)
    if result["status"] == "success":
        return result
    
    # Fallback: Wait for element
    wait_result = automation_elements("wait", window_handle=handle, control_id=control_id, timeout=timeout)
    if wait_result["found"]:
        return automation_elements("click", window_handle=handle, control_id=control_id)
    
    # Last resort: Find by OCR and click position
    text = automation_visual("extract_text")
    # Find matching text and click its position
    ...
```

### Pattern 2: State Verification

```python
def verify_operation_completed(expected_state, timeout=10.0):
    """Verify an operation completed by checking UI state."""
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        state = get_desktop_state(use_ocr=True)
        
        # Check for expected text/element
        if expected_state in str(state):
            return True
        
        automation_system("wait", seconds=0.5)
    
    return False
```

### Pattern 3: Error Recovery

```python
def automation_with_recovery(operation_func, max_retries=3):
    """Execute automation with automatic error recovery."""
    
    for attempt in range(max_retries):
        try:
            result = operation_func()
            if result.get("status") == "success":
                return result
        except Exception as e:
            # Check for common recoverable errors
            if "dialog" in str(e).lower():
                # Dismiss unexpected dialog
                automation_keyboard("press", key="escape")
            elif "not found" in str(e).lower():
                # Wait and retry
                automation_system("wait", seconds=1.0)
    
    raise Exception(f"Operation failed after {max_retries} attempts")
```

### Pattern 4: Visual Verification

```python
def verify_click_worked(before_screenshot, after_screenshot):
    """Verify a click had an effect by comparing screenshots."""
    
    # Take before screenshot
    before = automation_visual("screenshot", return_base64=True)
    
    # Perform click
    automation_mouse("click", x=x, y=y)
    
    # Take after screenshot
    automation_system("wait", seconds=0.3)
    after = automation_visual("screenshot", return_base64=True)
    
    # Compare (simplified - real implementation would use image diff)
    return before != after
```

---

## Error Handling Strategies

### Handle Window Not Found

```python
result = automation_windows("find", title="MyApp")
if result["windows_found"] == 0:
    # App might not be running - try to start it
    automation_keyboard("hotkey", keys=["win"])
    automation_keyboard("type", text="MyApp")
    automation_keyboard("press", key="enter")
    automation_system("wait", seconds=3.0)
    result = automation_windows("find", title="MyApp")
```

### Handle Element Not Found

```python
result = automation_elements("click", window_handle=handle, control_id="SaveButton")
if result["status"] == "error":
    # Try alternative approaches
    # 1. Wait for element to appear
    automation_elements("wait", window_handle=handle, control_id="SaveButton", timeout=5.0)
    
    # 2. Use OCR to find and click
    text = automation_visual("extract_text")
    # Find "Save" in extracted text and click its position
    
    # 3. Use keyboard shortcut instead
    automation_keyboard("hotkey", keys=["ctrl", "s"])
```

### Handle Permission Errors

```python
result = automation_visual("screenshot")
if "permission" in result.get("error", "").lower():
    print("Screenshot permission denied. Possible causes:")
    print("- UAC elevation required")
    print("- Application running in different security context")
    print("- DRM-protected content")
```

---

## Performance Optimization

### Minimize Desktop State Calls

```python
# BAD: Calling get_desktop_state repeatedly
for i in range(10):
    state = get_desktop_state()  # Expensive!
    # Process state...

# GOOD: Call once, reuse results
state = get_desktop_state(use_ocr=True)
for element in state["elements"]:
    # Process element...
```

### Use Targeted Operations

```python
# BAD: Full desktop state for single window
state = get_desktop_state(max_depth=20, use_ocr=True)  # Expensive!

# GOOD: Target specific window
automation_windows("activate", handle=target_handle)
state = get_desktop_state(max_depth=5)  # Focused on active window
```

### Batch Operations

```python
# BAD: Individual operations with waits
automation_keyboard("type", text="a")
automation_system("wait", seconds=0.1)
automation_keyboard("type", text="b")
automation_system("wait", seconds=0.1)

# GOOD: Batch typing
automation_keyboard("type", text="ab")
```

---

## Limitations & Caveats

### What Windows Computer Use Cannot Do

1. **Bypass DRM/Protected Content** - Some applications block UI automation APIs
2. **Run Without Windows** - This is Windows-only (no macOS/Linux)
3. **Cross-Session Automation** - Cannot automate other user sessions
4. **Game Automation** - Most games block UI automation and input simulation
5. **Elevated Applications** - UAC-elevated apps require elevated MCP server

### Security Considerations

- Face recognition data is stored locally
- Screenshots may capture sensitive information
- Clipboard operations handle potentially sensitive data
- Consider running in isolated VM for untrusted automation

### Reliability Notes

- UI automation depends on application implementing accessibility APIs
- Some modern apps (Electron, web apps) have limited automation support
- Network latency can affect timing-sensitive operations
- Window handles can change after app restart

---

## See Also

- [Desktop State Tool Documentation](./desktop-state-tool.md)
- [Development](./DEVELOPMENT.md)
- [MCP Technical Docs](./mcp-technical/README.md)
- [Glama Platform Integration](./glama-platform/README.md)

