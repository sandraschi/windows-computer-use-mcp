# 🚨 MCP Tool Corruption Issue - Lesson Learned

**Date**: October 8, 2025  
**Severity**: HIGH  
**Status**: IDENTIFIED - Our tools likely caused Notepad++ corruption

---

## 🎯 **The Discovery**

**User Report**:
- Notepad++ worked fine for months/years
- Started having white-on-white text issue ~1 week ago
- **Timeline matches**: Testing of notepadpp-mcp tools
- **Conclusion**: Our MCP tools likely corrupted Notepad++ config

---

## 🔍 **Suspected Culprits**

### **Tool 1: `fix_invisible_text()`**

**What it does**:
```python
# Lines 1741-1917 in server.py
- Opens Style Configurator via keyboard automation
- Navigates menus blindly with Tab/Arrow keys
- Tries to change theme and colors
- Presses buttons without visual confirmation
```

**Risk**:
- ❌ Keyboard navigation can go wrong
- ❌ Dialog layouts differ by version
- ❌ Tab counts can be off
- ❌ Can activate wrong settings
- ❌ **Can corrupt stylers.xml**

---

### **Tool 2: `fix_display_issue()`**

**What it does**:
```python
# Lines 1922-2022 in server.py
- Opens Settings menu
- Navigates to Style Configurator
- Tries to reset theme
- More blind keyboard automation
```

**Same risks as above**

---

## ⚠️ **The Problem with These Tools**

**Blind UI Automation**:
```python
# Example from fix_invisible_text()
keybd_event(win32con.VK_TAB, 0, 0, 0)  # Press Tab
keybd_event(win32con.VK_TAB, 0, win32con.KEYEVENTF_KEYUP, 0)
await asyncio.sleep(0.1)

# Press Tab 2 times to "navigate to theme dropdown"
for _ in range(2):
    keybd_event(win32con.VK_TAB, 0, 0, 0)
    ...
```

**Why This is Dangerous**:
- 🚨 Assumes dialog layout (can change between versions)
- 🚨 No visual verification
- 🚨 Can focus wrong controls
- 🚨 Can change unintended settings
- 🚨 **Can corrupt configuration files!**

---

## 📋 **What Likely Happened**

**Scenario**:
1. User runs `fix_invisible_text()` or `fix_display_issue()`
2. Tool opens Style Configurator
3. Blind Tab navigation focuses wrong control
4. Tool changes wrong setting or corrupts theme
5. Notepad++ saves corrupted stylers.xml
6. Text becomes invisible (white-on-white)
7. Split view gets activated accidentally
8. User is stuck with broken Notepad++

---

## ✅ **Immediate Fix Applied**

**For the current corruption**:
1. Stopped Notepad++
2. Deleted corrupted config files (config.xml, stylers.xml, session.xml)
3. Started fresh with `-nosession` flag
4. Notepad++ creates new default configs

**Expected**: Should work now!

---

## 🔧 **Long-Term Solutions**

### **Option 1: Deprecate These Tools** (Recommended)

**Mark as DANGEROUS**:
```python
@app.tool()
@deprecated("This tool uses blind UI automation and can corrupt Notepad++ config. Use manual Style Configurator instead.")
async def fix_invisible_text():
    return {
        "success": False,
        "error": "This tool is deprecated due to config corruption risk",
        "recommendation": "Manually use: Settings → Style Configurator → Select theme"
    }
```

---

### **Option 2: Rewrite with Direct API**

**Instead of keyboard automation**, use Scintilla messages directly:

```python
# Safer approach - direct Scintilla color setting
SCI_STYLESETFORE = 2051
SCI_STYLESETBACK = 2052
STYLE_DEFAULT = 32

# Set default style colors directly
await controller.send_message(
    controller.scintilla_hwnd, 
    SCI_STYLESETFORE, 
    STYLE_DEFAULT, 
    0x000000  # Black
)
await controller.send_message(
    controller.scintilla_hwnd,
    SCI_STYLESETBACK,
    STYLE_DEFAULT,
    0xFFFFFF  # White
)
```

**Benefits**:
- ✅ Direct API calls (no UI automation)
- ✅ No risk of wrong button presses
- ✅ Immediate effect
- ✅ No config file corruption
- ✅ Reversible

---

### **Option 3: Add Safety Warnings**

**If keeping the tools**:

```python
@app.tool()
async def fix_invisible_text():
    """
    ⚠️ WARNING: This tool uses UI automation and may corrupt Notepad++ config!
    
    BACKUP YOUR CONFIG FIRST:
    - Copy C:\\Users\\...\\AppData\\Roaming\\Notepad++\\ to safe location
    
    SAFER ALTERNATIVE:
    - Manually use Settings → Style Configurator
    - Select "Obsidian" or "Default" theme
    
    USE AT YOUR OWN RISK!
    """
    # ... existing code ...
```

---

## 📊 **Impact Assessment**

**Tools with UI Automation Risk**:
1. `fix_invisible_text()` - HIGH RISK ⚠️
2. `fix_display_issue()` - HIGH RISK ⚠️
3. `install_plugin()` - MEDIUM RISK ⚠️
4. `execute_plugin_command()` - MEDIUM RISK ⚠️
5. `find_text()` - LOW RISK (simpler automation)

**Safe tools**:
- `open_file()` - Uses command line ✅
- `new_file()`, `save_file()` - Simple Ctrl+N/S ✅
- `insert_text()` - Uses clipboard ✅
- All linting tools - File operations only ✅

---

## 🎯 **Recommendations**

### **Immediate**

1. **Deprecate** `fix_invisible_text()` and `fix_display_issue()`
2. **Add warnings** to plugin automation tools
3. **Document** this corruption risk
4. **Test** all tools for side effects

### **v1.3.0 Release**

1. **Rewrite** display fix tools with direct Scintilla API
2. **Add backup** functionality before any UI automation
3. **Implement** verification after tool execution
4. **Create** restore functionality

---

## 📝 **Documentation Updates Needed**

### **README.md**

Add warning:
```markdown
### ⚠️ Known Issues

**Display Fix Tools** (`fix_invisible_text`, `fix_display_issue`):
- Use UI automation which can corrupt Notepad++ config
- **Recommend**: Manual theme changes via Style Configurator
- **If using**: Backup config first
- **v1.3.0**: Will be rewritten with safe direct API calls
```

### **Tool Descriptions**

Update warnings in server.py docstrings.

---

## 🏆 **Lesson Learned**

**Blind UI automation is dangerous**:
- ❌ Can't verify what control is focused
- ❌ Dialog layouts change between versions
- ❌ Can press wrong buttons
- ❌ Can corrupt configuration
- ❌ Hard to debug when it goes wrong

**Better approaches**:
- ✅ Direct API calls (Scintilla messages)
- ✅ File-based operations
- ✅ Command-line parameters
- ✅ With visual verification
- ✅ With automatic backups

---

## 📞 **User Impact**

**This user's experience**:
- Spent hours troubleshooting
- Multiple fix attempts
- Fresh install required
- Still potentially broken via RustDesk

**Our responsibility**:
- Remove dangerous tools
- Add proper warnings
- Implement safer alternatives
- Prevent future corruption

---

*Issue documented: October 8, 2025*  
*Affected tools: fix_invisible_text, fix_display_issue*  
*Root cause: Blind UI automation*  
*Action: Deprecate or rewrite with safe API*  
*Priority: HIGH*

**Our tools should NEVER corrupt user configurations!** ⚠️

