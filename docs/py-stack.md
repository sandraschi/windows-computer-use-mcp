# Python Stack

Every `py-` module in this project and what it does.

## Core UI Automation

| Package | What it does here |
|---------|-------------------|
| **[pywinauto](https://github.com/pywinauto/pywinauto)** | Walks UIA and Win32 control trees, finds elements by automation ID / title / class, clicks, reads text, checks state. Backs `automation_windows`, `automation_elements`. |
| **pywin32** | Win32 COM and low-level API bindings. Used for session management, process enumeration, DPI helpers, and raw `SetCursorPos`/`mouse_event` alongside pywinauto. |
| **pygetwindow** | Lightweight window enumeration by title — fallback discovery before pywinauto attaches to the HWND. |
| **pyautogui** | Screen-level pointer and screenshot fallback. Used mainly for keyboard injection paths where pywinauto's `type_keys` has focus issues. |

## Input Simulation

| Package | What it does here |
|---------|-------------------|
| **pynput** | Cross-platform keyboard/mouse listener and controller. Powers `automation_keyboard` — normal typing, modifier combos, and the opt-in `global_keylogger` for debugging shortcut focus issues. |
| **pyperclip** | Clipboard read/write for `automation_system`. Used to paste long paths in file dialogs (`automation_dialog`) and for copy/paste automation flows. |

## Vision and OCR

| Package | What it does here |
|---------|-------------------|
| **opencv-python-headless** | Screenshot capture, template matching, camera index probe. Backs `automation_visual` (`find_image`, `screenshot`) and the `automation_face` biometric preview pipeline. |
| **pytesseract** | Tesseract OCR wrapper for `automation_visual` `extract_text`. Requires Tesseract 5.x installed on the host. Auto-install via `just install-tesseract` or NSIS installer checkbox. **Known limitation:** reads prose, punctuation, and all symbol characters correctly in normal text flow. ASCII art with widely separated character groups may produce segmentation errors (isolated groups confuse page layout analysis). For best results, ensure text is at least 10pt (default Notepad size may need enlargement via Ctrl+Shift+>). OCR results and screenshots are saved to `ocr_scans/` for review. |

## Optional: Face Recognition

| Package | What it does here |
|---------|-------------------|
| **face_recognition** | Webcam capture and face matching for `automation_face` (opt-in, `WINDOWS_COMPUTER_USE_MCP_ENABLE_FACE=1`). Not installed by default. |
| **dlib** | ML backend for face_recognition. Heavy dependency — requires CMake to build. |

## Infrastructure Dependencies

These aren't `py-*` packages but are critical to the stack:

| Package | Role |
|---------|------|
| **FastMCP** | MCP 3.2 framework — tool registration, transport (stdio + HTTP), Prefab cards, sampling |
| **FastAPI + uvicorn** | HTTP REST layer — `/api/v1/*`, `/mcp` streamable HTTP, health checks |
| **Pillow** | Image format handling — screenshot encoding (PNG/JPEG), thumbnail generation |
| **numpy** | Array operations under opencv, face_recognition, and image diff/hash functions in `automation_assert` |
| **httpx** | Async HTTP client — bridge calls to fleet MCP servers and LLM proxies |
| **psutil** | Process listing, system resource monitoring in `automation_system` |
| **Pydantic** | Request/response models for all portmanteau tools |
