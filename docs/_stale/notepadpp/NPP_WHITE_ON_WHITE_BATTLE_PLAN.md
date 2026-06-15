# 🎯 Notepad++ White-on-White Battle Plan

**Mission**: Fix the damn invisible text, once and for all!  
**Stubbornness Level**: 9/10  
**Stupidity Level**: 8/10  
**Date**: October 8, 2025  
**Status**: TO BE CONQUERED TOMORROW

---

## 📋 **What We Know So Far**

### **The Problem**
- White text on white background in Notepad++ editor pane
- Text IS there (line counter increases, scrollbar shows content)
- Started ~1 week ago after testing notepadpp-mcp tools
- Persists through:
  - ✅ Config file edits
  - ✅ Complete reinstall
  - ✅ Fresh config directory
  - ✅ Multiple theme changes
  - ✅ Global override attempts

### **Environmental Factors**
- **RustDesk remote desktop** - Makes it worse/visible
- **High Contrast Mode** - Was NOT on initially
- **Windows High Contrast themes** - Actually show text better via RustDesk!

### **Timeline**
1. Notepad++ worked fine for years
2. ~1 week ago: Started testing notepadpp-mcp tools
3. `fix_invisible_text()` tool used (blind UI automation)
4. Text became invisible (white-on-white)
5. Multiple fix attempts failed
6. Complete reinstall → Still broken
7. Issue persists even with fresh install

---

## 🔍 **Suspected Root Causes**

### **Theory 1: MCP Tool Corrupted Something Deep** ⭐ **MOST LIKELY**

**Evidence**:
- Worked before testing MCP tools
- `fix_invisible_text()` uses blind keyboard automation
- Could have changed hidden/registry settings
- Survived config deletion AND reinstall

**What to check tomorrow**:
```powershell
# Check registry settings for Notepad++
reg query "HKEY_CURRENT_USER\Software\Notepad++" /s > npp-registry.txt

# Check for hidden config files
Get-ChildItem "$env:APPDATA\Notepad++" -Force -Recurse

# Check for local settings (not in AppData)
Get-ChildItem "$env:LOCALAPPDATA\Notepad++" -Force -Recurse
```

---

### **Theory 2: RustDesk DirectWrite Conflict**

**Evidence**:
- High Contrast themes work over RustDesk
- Normal themes don't render text
- DirectWrite font rendering issues

**What to try tomorrow**:
1. **Disable DirectWrite in Notepad++**:
   - Settings → Preferences → MISC
   - Uncheck "Enable DirectWrite"
   
2. **Test locally** (not via RustDesk):
   - Go to physical PC
   - Open Notepad++
   - See if text is visible

---

### **Theory 3: Windows Registry Corruption**

**Evidence**:
- Survived config deletion
- Survived complete reinstall
- Something persistent is broken

**What to check tomorrow**:
```powershell
# Backup current registry for Notepad++
reg export "HKEY_CURRENT_USER\Software\Notepad++" npp-backup.reg

# Delete Notepad++ registry settings
reg delete "HKEY_CURRENT_USER\Software\Notepad++" /f

# Restart Notepad++ (will recreate registry)
```

---

### **Theory 4: Scintilla Component Corruption**

**Evidence**:
- Editor pane broken (Scintilla)
- Workspace panel works (Win32 TreeView)
- Split view causes issues
- Text exists but not rendered

**What to try tomorrow**:
1. Force Scintilla to reset:
   ```xml
   <!-- In config.xml, try adding: -->
   <GUIConfig name="ScintillaViewsSplitter" />
   ```

2. Check Scintilla lexer settings:
   ```powershell
   # Look for corrupted lexer files
   Get-ChildItem "$env:APPDATA\Notepad++\plugins\Config" -Recurse
   ```

---

## 🎯 **Tomorrow's Attack Plan**

### **Phase 1: Local Testing** (15 minutes)

**Goal**: Determine if it's RustDesk or actual Notepad++ issue

1. **Go to physical PC** (not via RustDesk)
2. Open Notepad++
3. Type text
4. **Is text visible?**
   - ✅ **YES** → It's RustDesk! Use DirectWrite fix
   - ❌ **NO** → Continue to Phase 2

---

### **Phase 2: Registry Nuclear Option** (10 minutes)

**Goal**: Completely reset Notepad++ at registry level

```powershell
# 1. Backup
reg export "HKEY_CURRENT_USER\Software\Notepad++" npp-backup-2025-10-09.reg

# 2. Kill Notepad++
Get-Process notepad++ | Stop-Process -Force

# 3. Delete registry
reg delete "HKEY_CURRENT_USER\Software\Notepad++" /f

# 4. Delete AppData
Remove-Item "$env:APPDATA\Notepad++" -Recurse -Force

# 5. Restart
Start-Process "C:\Program Files\Notepad++\notepad++.exe"
```

**Expected**: Fresh registry + fresh config = Should work!

---

### **Phase 3: Scintilla Component Investigation** (20 minutes)

**If Phase 2 fails**, check Scintilla:

```powershell
# Check Scintilla DLL version
Get-ItemProperty "C:\Program Files\Notepad++\SciLexer.dll" | Select-Object VersionInfo

# Compare with known-good version
# Download portable Notepad++ to compare
```

---

### **Phase 4: MCP Tool Forensics** (30 minutes)

**What did our tool ACTUALLY do?**

1. Review `fix_invisible_text()` code in `server.py`
2. Trace every keyboard command it sent
3. Manually reverse each action
4. Look for hidden registry changes

```python
# Lines 1741-1917 in server.py
# What menus did it navigate?
# What buttons did it press?
# What could it have changed that we missed?
```

---

### **Phase 5: Nuclear Portable Install** (Last Resort)

**If EVERYTHING fails**:

1. Download Notepad++ **Portable** (doesn't use registry/AppData)
2. Extract to `C:\PortableApps\Notepad++`
3. Run from there
4. **Should work** (no shared state with broken install)

**Link**: https://notepad-plus-plus.org/downloads/

---

## 🛠️ **Tools & Scripts Ready**

**On Desktop**:
- ✅ `fix-notepadpp-colors.ps1` - Config file fix
- ✅ `fix-scintilla-colors-direct.ps1` - Direct Scintilla fix
- ✅ `notepadpp-safe-mode.bat` - Safe mode startup
- ✅ `MANUAL-FIX-STEPS.txt` - Manual UI steps
- ✅ `RUSTDESK-RENDERING-FIX.txt` - RustDesk compatibility

**To create tomorrow**:
- `nuke-npp-registry.ps1` - Registry deletion script
- `compare-scintilla.ps1` - DLL version checker

---

## 📝 **What to Document Tomorrow**

**When we fix it**:
1. Exact steps that worked
2. Root cause identified
3. Prevention for future
4. Update `MCP_TOOL_CORRUPTION_ISSUE.md`

**If we don't fix it**:
1. Workaround used (portable/alternative)
2. Bug report to Notepad++ team
3. Deprecate dangerous MCP tools

---

## 💡 **Alternative Solutions**

**If Notepad++ won't cooperate**:

1. **VS Code** (already installed)
   - ✅ Works perfectly
   - ✅ RustDesk compatible
   - ✅ Better features anyway

2. **Sublime Text**
   - ✅ Faster than Notepad++
   - ✅ No rendering issues

3. **Notepad3**
   - ✅ Notepad++ clone
   - ✅ Clean install
   - ✅ No baggage

**Remember**: **Don't let Notepad++ win!** We have options!

---

## 🎯 **Success Criteria**

**We WIN when**:
- ✅ Black text on white background visible
- ✅ Can type and see text
- ✅ Cursor shows
- ✅ Works locally AND via RustDesk
- ✅ Root cause identified and documented

**We LOSE if**:
- ❌ Spend more than 2 hours on it
- ❌ Still not working after all phases
- ❌ **In which case**: Use VS Code and move on!

---

## 🔥 **Battle Cry**

> **"Tomorrow we fix Notepad++... and if it's the last thing we ever do!"**  
> *— Sandra, October 8, 2025, 9/10 stubborn, 8/10 stupid problem*

**Stubbornness Level**: MAXIMUM  
**Determination Level**: LEGENDARY  
**Backup Plan**: Ready and waiting

---

## 📞 **When to Call It**

**Give up and use alternative if**:
- More than 2 hours spent
- Phase 5 (portable) also fails
- Can't identify root cause
- Getting too frustrated

**Remember**: The goal is to EDIT TEXT, not fix Notepad++!  
**VS Code works perfectly** - it's not defeat, it's pragmatism! 🎯

---

*Battle Plan Created: October 8, 2025*  
*Status: Ready for tomorrow's assault*  
*Backup Plan: VS Code standing by*  
*Mood: Determined but realistic*

**LET'S GET THIS THING FIXED!** 💪🔥

---

## 🎁 **Secret Weapon for Tomorrow**

**Process of Elimination**:

```powershell
# Quick diagnostic script for tomorrow morning
$tests = @(
    "Physical PC test (no RustDesk)",
    "Registry nuke test",
    "Portable install test",
    "VS Code fallback (win condition)"
)

foreach ($test in $tests) {
    Write-Host "`n🎯 Trying: $test" -ForegroundColor Cyan
    # Execute test
    Read-Host "Did it work? (Y/N)"
    # If Y, document and STOP!
}
```

**One of these WILL work!** ✅

*Good luck tomorrow, warrior!* ⚔️

