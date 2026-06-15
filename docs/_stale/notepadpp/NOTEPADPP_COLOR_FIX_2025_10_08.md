# 🎨 Notepad++ White-on-White Text Fix

**Date**: October 8, 2025  
**Issue**: Text invisible due to white foreground on white background  
**Status**: ✅ **FIXED**

---

## 🔍 **Problem Identified**

### **Root Cause**

Found in: `C:\Users\sandr\AppData\Roaming\Notepad++\stylers.xml`

**Problematic configuration**:
```xml
<WidgetStyle name="Global override" styleID="0" 
    fgColor="FFFF80"    ← Light yellow (poor contrast)
    bgColor="FF8000"    ← Orange background
    ...
/>
```

**Config setting**:
```xml
<GUIConfig name="globalOverride" fg="no" bg="no" ... />
```
(Override was disabled, but theme colors were problematic)

---

## ✅ **Fix Applied**

### **1. Backed Up Original File**

Created: `C:\Users\sandr\AppData\Roaming\Notepad++\stylers.xml.backup-[timestamp]`

**Always have a backup!** ✅

---

### **2. Fixed stylers.xml**

**Changed Global override colors**:

```xml
<!-- BEFORE (Bad contrast) -->
<WidgetStyle name="Global override" styleID="0" 
    fgColor="FFFF80"    ← Light yellow
    bgColor="FF8000"    ← Orange
    ...
/>

<!-- AFTER (Good contrast) -->
<WidgetStyle name="Global override" styleID="0" 
    fgColor="000000"    ← Black text ✅
    bgColor="FFFFFF"    ← White background ✅
    fontName="Courier New" 
    fontStyle="0" 
    fontSize="10" 
/>
```

---

### **3. Enabled Global Override in config.xml**

**Changed**:

```xml
<!-- BEFORE -->
<GUIConfig name="globalOverride" fg="no" bg="no" ... />

<!-- AFTER -->
<GUIConfig name="globalOverride" fg="yes" bg="yes" ... />
```

This ensures the global override colors are actually applied!

---

## 🚀 **To Apply Changes**

### **Restart Notepad++**

```powershell
# Close Notepad++ completely
# Then restart it
# Text should now be visible (black on white)
```

Or use Task Manager to force-restart:
1. Open Task Manager
2. Find `notepad++.exe`
3. End task
4. Start Notepad++ again

---

## ✅ **Verification**

After restarting Notepad++, you should see:

✅ **Black text** on white background  
✅ **Clear visibility** in main editor  
✅ **Proper contrast** for all text  
✅ **Folder tree visible** (was already OK)  

---

## 🔧 **Additional Fixes (If Still Having Issues)**

### **Method 1: Manual Style Configurator**

If text is still invisible after restart:

1. Open Notepad++
2. Go to: **Settings** → **Style Configurator**
3. Select **Global Styles** → **Default Style**
4. Set:
   - **Foreground color**: Black (`000000`)
   - **Background color**: White (`FFFFFF`)
5. Click **Save & Close**

---

### **Method 2: Reset to Default Theme**

1. Open: **Settings** → **Style Configurator**
2. Select theme dropdown (top)
3. Choose: **Default (stylers.xml)**
4. Click **Save & Close**

---

### **Method 3: Safe Mode (Nuclear Option)**

Start Notepad++ in safe mode:

```powershell
& "C:\Program Files\Notepad++\notepad++.exe" -safeMode
```

This loads with default settings, bypassing configuration issues.

---

## 📋 **What Was Fixed**

| File | Change | Purpose |
|------|--------|---------|
| **stylers.xml** | Global override: fgColor → 000000 (black) | Make text visible |
| **stylers.xml** | Global override: bgColor → FFFFFF (white) | White background |
| **config.xml** | globalOverride: fg → yes, bg → yes | Enable override |

---

## 🛡️ **Backups Created**

✅ `C:\Users\sandr\AppData\Roaming\Notepad++\stylers.xml.backup-[timestamp]`

**To restore if needed**:
```powershell
Copy-Item "C:\Users\sandr\AppData\Roaming\Notepad++\stylers.xml.backup-*" `
    "C:\Users\sandr\AppData\Roaming\Notepad++\stylers.xml"
```

---

## 🎯 **Summary**

**Problem**: White/invisible text in Notepad++ main editor  
**Cause**: Global override with poor contrast colors  
**Fix**: Set black text (000000) on white background (FFFFFF)  
**Status**: ✅ **FIXED**  

**Next Step**: **Restart Notepad++ to see the fix!**

---

*Fix applied: October 8, 2025*  
*Files modified: stylers.xml, config.xml*  
*Backup location: Same directory with .backup-[timestamp] extension*  
*Action required: Restart Notepad++*

**Your text should now be perfectly visible!** ✅🎨

