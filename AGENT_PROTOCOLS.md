# AGENT_PROTOCOLS - Windows Computer Use [v14.2.0]

This document establishes the authoritative operational protocols for AI agents consuming the `windows-computer-use-mcp` service on Windows 11 environments.

## I. Operational Guardrails

### 1. HITL (Human-in-the-Loop) Requirements
- **Mandatory Approval**: All "Destructive" or "Interaction" tools (mouse clicks, keyboard typing) REQUIRE an active approval window.
- **Approval Tool**: Call `approve_automation(duration_minutes=5)` to open an idempotent safety window.
- **Fail-Safe**: Tools will return an error if called outside the safety window for non-read-only operations.

### 2. Physical Safety & System Stability
- **Kill Switch**: The system obeys the `WINDOWS_COMPUTER_USE_MCP_KILL_SWITCH` environment variable. If set to `true`, all automation tools will immediately abort.
- **Rate Limiting**: AI agents must not exceed 20 UI actions per minute to prevent OS instability.
- **Dry Run Mode**: Agents should use `DRY_RUN=true` for initial validation of complex UI selectors.

## II. Tooling Patterns (Portmanteau)

Agents must prefer the consolidated portmanteau tools over granular legacy methods:

- **automation_windows**: Primary for window lifecycle (list, activate, close).
- **automation_elements**: High-fidelity UI element control (click, set_text, info).
- **automation_visual**: OCR and template matching for non-standard UI.
- **get_desktop_state**: Root discovery of the current UI tree with OCR enrichment.
- **automation_mission**: Orchestrates complex goals via agentic sampling (requires FastMCP 3.2+).

## III. Agentic Sampling & Missions

Agents should utilize the `automation_mission` tool for high-level tasks that require planning:

1. **Mission Planning**: The tool calls `ctx.sample()` to generate a multi-step execution plan from a natural language goal.
2. **Dialogue Pattern**: If the plan is ambiguous, the tool will return `clarification_needed`.
3. **Execution**: The agent should review the sampled plan metadata before committing to intensive UI interactions.

## IV. Error Handling Protocol

### UI Search Failures
- If an element is not found, the agent MUST call `get_desktop_state` to refresh their mental map of the UI.
- Do NOT guess coordinates; use `info` to verify element rects before interaction.

### Permission Errors
- Accessing system-level windows (e.g., Task Manager) may require the server to be running with Administrative privileges.
- If an operation fails with `0x5` (Access Denied), inform the user about the privilege bottleneck.

## IV. SOTA v14.1.0 Compliance
This server implements the "Vienna Industrial" standard:
- **Registry**: Ports 10788 (Web) / 10789 (API)
- **FastMCP**: v3.2.0 stable with native Sampling Support (SEP-1577).
- **Orchestration**: Managed via root `start.ps1` with port synchronization (10788/10789).
- **Resources**: Dynamic desktop state available at `resource://automation/current_state`.
- **Prompts**: Standardized runbooks available (e.g., `desktop_automation_runbook`).
