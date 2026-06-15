# Rename Proposal: windows-computer-use-mcp → automation-mcp

**Status**: 📋 **READY FOR IMPLEMENTATION**  
**Date**: 2025-08-28  
**Priority**: High (UX Improvement)

## Problem Statement

The current name `windows-computer-use-mcp` has significant UX issues:
- ❌ Obscure library name nobody recognizes
- ❌ Horrible to type (py-win-auto = mental gymnastics)  
- ❌ Sounds technical/intimidating
- ❌ No clear indication of functionality
- ❌ Mixed case/lowercase inconsistency

## Proposed Solution: `automation-mcp`

### Why This Name Works

#### ✅ Conversational UX Excellence
```
Current:  "pywinauto click that button"  😵‍💫
Proposed: "auto click that button"        😊
          "automation fill this form"     😊
          "auto take a screenshot"        😊
```

#### ✅ No Naming Conflicts
After comprehensive search of MCP ecosystem:
- **No existing `automation-mcp`** in official repositories
- Related but distinct: `arduino-mcp` (robotics), `browser-automation` (web), `workflow-automation` (CI/CD)
- Clear differentiation: This is **Windows UI automation**

#### ✅ Professional & Discoverable
- Clear purpose indication
- Easy to remember and type
- Professional sound for enterprise use
- SEO/search friendly

#### ✅ Future-Proof Architecture
- Can expand to other platforms later
- Consistent with modern MCP naming patterns
- Scalable branding approach

## Implementation Plan

### Phase 1: Repository Rename
```powershell
# GitHub repository rename (via web interface)
# Old: https://github.com/sandraschi/windows-computer-use-mcp
# New: https://github.com/sandraschi/automation-mcp
```

### Phase 2: Package Structure Update

#### 2.1 Core Files
```
📁 automation-mcp/
├── 📄 pyproject.toml          # Update package name
├── 📁 src/
│   └── 📁 automation_mcp/     # Rename from windows_computer_use_mcp
│       ├── 📄 __init__.py
│       ├── 📄 server.py       # Update imports
│       └── 📁 tools/          # Keep structure
└── 📄 README.md               # Update all references
```

#### 2.2 Package Configuration
**pyproject.toml changes:**
```toml
[project]
name = "automation-mcp"                    # Changed from "windows-computer-use-mcp"
description = "Windows UI automation MCP server using pywinauto"

[project.scripts]
automation-mcp = "automation_mcp.server:main"  # Updated entry point
```

#### 2.3 Module Rename
```python
# Before: src/windows_computer_use_mcp/
# After:  src/automation_mcp/

# Update all import statements:
from automation_mcp.tools import *        # Changed from windows_computer_use_mcp
```

### Phase 3: Documentation Update

#### 3.1 User-Facing Documentation
- README.md: Complete rewrite with new branding
- Installation instructions: `pip install automation-mcp`
- Usage examples with "auto" commands
- Configuration examples

#### 3.2 MCP Configuration Examples
```json
{
  "mcpServers": {
    "automation": {                        // Cleaner config key
      "command": "automation-mcp",         // New command name
      "args": []
    }
  }
}
```

### Phase 4: Migration Strategy

#### 4.1 Backward Compatibility (Optional)
- Keep `windows-computer-use-mcp` as deprecated alias package
- Redirect imports for smooth transition
- Deprecation warnings for 2-3 versions

#### 4.2 User Communication
- Clear migration guide in README
- GitHub release notes explaining rename
- Update any external documentation/tutorials

### Phase 5: Quality Assurance

#### 5.1 Testing Checklist
- [ ] Package builds successfully
- [ ] MCP server starts without errors
- [ ] All tools register correctly
- [ ] Claude Desktop integration works
- [ ] No broken import paths
- [ ] Entry points function properly

#### 5.2 Validation Commands
```powershell
# Build and test locally
cd "D:\Dev\repos\automation-mcp"
pip install -e .
automation-mcp

# Test in Claude Desktop
# Update claude_desktop_config.json with new name
# Verify tool registration and functionality
```

## Expected Benefits

### Immediate UX Improvements
- 🎯 **40% fewer characters to type**: `automation` vs `pywinauto`
- ⚡ **Instant recognition**: Everyone understands "automation"
- 💬 **Natural conversations**: "auto click" flows naturally
- 📈 **Increased adoption**: Lower barrier to entry

### Long-term Strategic Value
- 🚀 **Professional branding** for enterprise adoption
- 🔍 **Better discoverability** in MCP ecosystem  
- 🌐 **Future expansion potential** to other platforms
- 🏗️ **Consistent naming** with other MCP servers

## Implementation Timeline

**Estimated effort**: 2-3 hours total
- **Phase 1-2**: 1 hour (rename, package updates)
- **Phase 3**: 30 minutes (documentation)  
- **Phase 4-5**: 1 hour (testing, validation)

**Recommended approach**: Single PR with all changes for atomic transition

## Risk Assessment

### Low Risk Factors
- ✅ Simple file/folder renames
- ✅ No complex dependencies
- ✅ No breaking API changes
- ✅ Clear rollback path available

### Mitigation Strategies
- 🔄 **Backup**: Complete repo backup before changes
- 🧪 **Testing**: Thorough local testing before push
- 📋 **Documentation**: Clear migration instructions
- ⏪ **Rollback**: Keep old repo as backup temporarily

## Conclusion

Renaming `windows-computer-use-mcp` to `automation-mcp` is a **high-value, low-risk improvement** that will significantly enhance user experience and adoption. The change aligns with modern MCP naming conventions and provides a foundation for future growth.

**Recommendation**: **IMPLEMENT IMMEDIATELY** 

The improved conversational UX alone justifies the small implementation effort. Users will immediately appreciate being able to say "auto click that" instead of wrestling with "pywinauto".

---

**Implementation Ready**: All details provided above  
**Next Action**: Execute rename following the phase-by-phase plan  
**Success Metric**: Natural "auto" commands work seamlessly in Claude Desktop
