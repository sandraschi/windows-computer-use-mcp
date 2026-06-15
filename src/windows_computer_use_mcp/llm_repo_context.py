"""Curated repository knowledge for local LLM system prompts (web UI chat).

Keep this factual and concise so it fits in context windows. Update when tools or safety model change.
"""

REPO_CONTEXT_MARKDOWN = """
## pywinauto-mcp — what this project is

- **Purpose:** Windows desktop **UI automation** exposed over **MCP** (Model Context Protocol) using **PyWinAuto**, **PyAutoGUI**, and related libraries.
- **Scope:** Automates **real windows, controls, mouse, keyboard** on the host Windows session — not a browser sandbox.

## Can I click and drag?

- **Yes**, in principle: mouse movement, clicks, drags, and keyboard input are within scope of the automation stack (e.g. **`automation_mouse`**, **`automation_elements`**, **`automation_windows`**), subject to **HITL** (human-in-the-loop) and **`approve_automation`** where configured.
- **Caveats:** Dragging is **app-dependent** (some UIs need a click-hold-move sequence). Use **`automation_visual`** for screenshots/OCR/template matching when coordinates are unknown. Prefer **element-backed** actions (**`automation_elements`**) over blind coordinates when possible.
- **Safety:** Mutating mouse/keyboard may require **`approve_automation`**. See **`docs/SAFETY.md`** and env vars like **`windows_computer_use_mcp_KILL_SWITCH`**, **`windows_computer_use_mcp_DRY_RUN`**.

## Main MCP tools (portmanteau pattern)

- **`automation_windows`** — find, focus, resize, close windows.
- **`automation_elements`** — click, type, read UI elements / control identifiers.
- **`automation_mouse`** — pointer moves, clicks (HITL may apply).
- **`automation_keyboard`** — keys and shortcuts (HITL may apply).
- **`automation_visual`** — screenshots, OCR, template matching.
- **`automation_system`** — status, help, wait, clipboard, processes, start apps, etc.
- **`get_desktop_state`** — structured UI tree / discovery.
- **`approve_automation`** — extends approval window for sensitive actions.
- **`automation_safety`** — counters, kill switch / dry-run visibility.
- **`automation_face`** — optional face features; **off** unless **`windows_computer_use_mcp_ENABLE_FACE=1`** + face extra (**`docs/SAFETY.md` §5**).

## Isolation

- **pywinauto-mcp** does **not** replace **Windows Sandbox** or a **VM**. For disposable desktops, pair with **`virtualization-mcp`** (separate project) per **`docs/SAFETY.md`**.

## Answering user questions

- Prefer **accurate, cautious** answers: cite **HITL**, **approval**, and **dry-run** when discussing input automation.
- If asked about **web** apps inside a browser, note that **browser MCP** is often more appropriate than desktop automation — but pywinauto can still drive browser windows as native windows when appropriate.
""".strip()
