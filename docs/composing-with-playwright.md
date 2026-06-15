# Composing with Playwright (browser-mcp)

`windows-computer-use-mcp` drives **native Windows UI** (Win32, UIA). `browser-mcp` drives **HTML/DOM in a browser** via Playwright. They are complementary — run both side by side.

## When to use which

| Target | Tool | Reason |
|--------|------|--------|
| Notepad, Calc, Paint, installer dialogs | `automation_elements`, `automation_mouse` | No DOM — only UIA/Win32 access |
| File dialogs, taskbar, system tray | `automation_windows`, `automation_elements` | OS-level chrome, not browser |
| A webapp (Vite, internal tool) | `browser-mcp` (`browser_navigate`, `browser_click`) | Full DOM access, CSS selectors |
| A website inside a native Electron app | `automation_elements` | No Playwright access to embedded WebView |
| Mixed: click a native desktop shortcut | `automation_mouse` → waits for browser | Chain both: native click opens URL, then Playwright drives the page |

## Running both MCPs

Add both to your MCP client config:

```json
{
  "mcpServers": {
    "windows-computer-use": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/windows-computer-use-mcp", "run", "windows-computer-use-mcp"]
    },
    "browser-mcp": {
      "command": "uv",
      "args": ["--directory", "D:/Dev/repos/browser-mcp", "run", "browser-mcp"]
    }
  }
}
```

The LLM sees both tool sets and selects the appropriate one based on the task.

## Cross-MCP workflow pattern

```
1. automation_elements(click, title="Launch Browser")   ← native click
2. browser_mcp.navigate(url="http://localhost:5173")    ← Playwright on the opened browser
3. browser_mcp.click(selector="#submit")                ← DOM interaction
4. automation_visual(screenshot)                         ← capture result
```

This lets you automate workflows that span the OS/browser boundary — e.g., install a dev tool, open its web UI, configure it, verify the result.

## Fleet MCP port reservation

| Server | Port |
|--------|------|
| windows-computer-use-mcp (backend) | 10789 |
| browser-mcp (backend) | 10780 |
| browser-mcp (frontend) | 10781 |

See `mcp-central-docs/operations/WEBAPP_PORTS.md` for the full fleet registry.
