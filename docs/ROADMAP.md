# Roadmap

## Short-term (highest impact)

### 1. Windows Media OCR as default
Windows Media OCR (via PyWinRT) is zero-install on every Windows 10/11 system and produces comparable results to Tesseract. Currently Tesseract is the default. Switch the default to Windows Media OCR when available, with Tesseract as fallback.

- [ ] Modify `automation_visual` to probe Windows Media OCR first
- [ ] Remove Tesseract PATH requirement for basic OCR
- [ ] Add `WINDOWS_COMPUTER_USE_MCP_OCR_PROVIDER` env var override

### 2. Screen recording / GIF capture
Add ffmpeg-based screen recording to `automation_visual`. A sequence of screenshots can be composited into a GIF or MP4 for demo videos, verification, or debugging failed missions.

- [ ] `automation_visual(record, duration=30, output="demo.mp4")`
- [ ] `automation_visual(record_to_gif, duration=10, output="demo.gif")`
- [ ] Auto-attach recording to mission results

### 3. Session replay to video
When replaying a macro with `automation_macro(replay)`, optionally record the screen simultaneously. Produces a demo video of any automated workflow.

- [ ] `automation_macro(replay_with_video, name="my_macro")`
- [ ] Records screen during replay, saves as MP4
- [ ] Useful for documentation, demos, debugging

### 4. HITL tray app polish
The system tray controller exists (`scripts/tray-control.py`) but is bare. Add:

- [ ] Real-time HITL approval notifications (balloon popup)
- [ ] Quick-record button (macro record/stop with hotkey shown)
- [ ] Server status indicator (connection health, tool count)
- [ ] Macro list with one-click replay

## Medium-term

### 5. Multi-monitor coordinate support
Window management across multiple monitors. Currently coordinates assume primary display. Add display-aware coordinate translation.

- [ ] Virtual screen bounds detection
- [ ] Per-monitor DPI scaling
- [ ] `automation_mouse(move_to_monitor, index=2)`

### 6. App-specific automation profiles
Structured profiles for common applications defining element selectors, window states, recovery sequences, and semantic shortcuts. Extends `automation_shortcut`.

- [ ] Profile format: YAML with selectors, states, expected behaviors
- [ ] Built-in profiles: Notepad, Paint, VS Code, installer dialogs
- [ ] Auto-detect app and load profile

### 7. Mission presets
Pre-built workflows for common tasks as JSON files. Loadable via `automation_mission(run_preset="install_app")`.

- [ ] Preset format with parameter substitution
- [ ] Registry: `~/.windows-computer-use-mcp/presets/`
- [ ] Initial presets: "install NSIS app", "export PDF from Notepad", "screenshot + OCR"

### 8. YAML/JSON portable workflow runner
Define multi-step automations as portable config files. No Python needed to define a workflow.

- [ ] `just run-workflow path/to/workflow.yaml`
- [ ] Step format: {tool, params, verify, retry}
- [ ] Cross-repo compatible (same format usable by fleet)

## Long-term

### 9. Computer vision for element finding
When UIA fails (e.g., custom controls, games, embedded web views), use lightweight object detection (YOLO, template matching) to find buttons and controls by appearance.

- [ ] Template matching improvement (multi-scale, rotation-invariant)
- [ ] Optional YOLO model for common UI elements (buttons, text fields, checkboxes)
- [ ] Fallback: when UIA selectors return nothing, try vision

### 10. Voice control integration
Integrate with `speech-mcp` to allow voice commands: "click Save", "type hello world", "screenshot". The tray app becomes a voice-controlled automation assistant.

- [ ] Speech-to-text via speech-mcp
- [ ] Natural language → tool call mapping
- [ ] Voice initiator in tray app

### 11. Remote desktop automation
Drive automation on a remote machine via RDP/VNC integration. Two approaches:

**Via rustdesk-mcp:** rustdesk-mcp already provides remote desktop access. Extend it with RDP/VNC protocol support, or create a dedicated `remote-control-mcp` that bundles RDP + VNC + RustDesk under one interface.

- [ ] RDP client automation (send keystrokes/clicks to RDP session)
- [ ] VNC client automation (same)
- [ ] `remote-control-mcp` umbrella repo, or extend `rustdesk-mcp`
- [ ] Transparent: `automation_windows(find, remote="hostname:port")`

### 12. Self-improving telemetry
The telemetry SQLite store already logs every action. Extend it to:

- [ ] Auto-detect failure patterns (specific app + operation + error)
- [ ] Generate GitHub issue drafts from failure clusters
- [ ] Suggest config changes (e.g., "Notepad's NotepadTextBox click fails 80% — try coordinate fallback")
- [ ] Weekly improvement report

### 13. Docker/sandbox execution mode
Run automation inside a Windows Sandbox or Docker container instead of on the host. Pairs with `virtualization-mcp`.

- [ ] `automation_system(sandbox=True)` — provision sandbox, run automation there
- [ ] Guest-side agent: lightweight pywinauto runner in the sandbox
- [ ] Result extraction: screenshots, logs, evidence back to host

## AI Model Notes

### Kimi K2.7 Code (Moonshot AI, June 2026)

Open-weight coding agent model, very relevant to this repo's mission engine:

| Metric | K2.6 | K2.7 Code |
|--------|------|-----------|
| MCP Atlas | 69.4 | **76.0** |
| MCP Mark Verified | 72.8 | **81.1** |
| Kimi Claw 24/7 | 42.9 | **46.9** |
| Thinking tokens | baseline | **-30%** |

- **Architecture:** 1T total / 32B activated MoE, 256K context, MLA attention
- **Multi-step tool call:** Native interleaved thinking + tool call support — matches `automation_mission(run=...)` pattern exactly
- **License:** Modified MIT (open weight)
- **Deployment:** INT4 quantization available, fits RTX 4090 at 4-bit
- **Vision:** MoonViT encoder (400M params) — can process screenshots for visual grounding

Could serve as the LLM backend for `ctx.sample()` in the mission engine, either via API or local inference.

### Other notable Chinese open-weight models

| Model | Company | Notes |
|-------|---------|-------|
| DeepSeek V4 / R2 | DeepSeek | Strong general reasoning, used by opencode |
| Qwen 3.5 | Alibaba | Good code + agentic, 235B MoE |
| GLM-5 | Zhipu | Strong on Chinese language tasks |
| Yi-Lightning | 01.AI | Fast inference, good for real-time |

## Cross-cutting

- **RDP/VNC consolidation:** Consider creating `remote-control-mcp` that unifies RustDesk, RDP, and VNC under a single tool surface. This avoids splitting focus across three repos. rustdesk-mcp can be the reference implementation.
- **Benchmark suite:** Automate comparison of Tesseract vs Windows Media OCR accuracy across font sizes, UI types, and languages.
- **User documentation:** Video tutorials for each major feature, linked from README.
