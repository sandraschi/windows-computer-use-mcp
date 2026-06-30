"""Pydantic models for PyWinAuto MCP tool parameters and results.

Ensures strict schema visibility and validation for portmanteau tools.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class WindowOperationRequest(BaseModel):
    """Request model for window management operations."""

    operation: Literal[
        "list",
        "find",
        "manage",
        "focus",
        "get_active",
        "maximize",
        "minimize",
        "restore",
        "close",
        "activate",
        "position",
        "rect",
        "title",
        "state",
    ] = Field(..., description="The window operation to perform.")

    handle: int | None = Field(
        None, description="Window handle (HWND). Required for all operations except 'list', 'find', and 'get_active'."
    )

    title: str | None = Field(
        None, description="Window title or partial title. Used primarily with the 'find' operation."
    )

    process_id: int | None = Field(None, description="Process ID to match against during 'find'.")

    class_name: str | None = Field(None, description="Window class name to match against during 'find'.")

    partial: bool = Field(True, description="Whether to perform a partial title match during 'find'.")

    action: Literal["maximize", "minimize", "restore", "close", "activate", "focus"] | None = Field(
        None, description="Specific window action to perform when operation set to 'manage'."
    )

    x: int | None = Field(None, description="Target X coordinate for 'position' operation.")
    y: int | None = Field(None, description="Target Y coordinate for 'position' operation.")
    width: int | None = Field(None, description="Target width for 'position' operation.")
    height: int | None = Field(None, description="Target height for 'position' operation.")

    monitor_index: int | None = Field(
        None,
        description="0-based monitor index for coordinate translation. "
        "When set, x/y are treated as relative to this monitor's origin. "
        "Use with 'position' to place a window on a specific monitor.",
    )


class ElementOperationRequest(BaseModel):
    """Request model for element-level automation operations."""

    window_handle: int = Field(..., description="Handle of the parent window containing the element.")

    operation: Literal[
        "list",
        "info",
        "click",
        "double_click",
        "right_click",
        "hover",
        "set_text",
        "get_text",
        "wait",
        "exists",
        "rect",
        "visible",
        "enabled",
        "verify_text",
    ] = Field(..., description="The element operation to perform.")

    # Selection criteria (Legacy individual fields supported for backward compat and explicit schema)
    control_id: str | None = Field(None, description="Element Control ID.")
    auto_id: str | None = Field(None, description="Element Automation ID.")
    title: str | None = Field(None, description="Element Title/Name.")
    control_type: str | None = Field(None, description="Element Control Type (e.g., 'Button').")
    class_name: str | None = Field(None, description="Element Class Name.")

    # Coordinate fallback
    x: int | None = Field(None, description="Relative or absolute X coordinate.")
    y: int | None = Field(None, description="Relative or absolute Y coordinate.")
    absolute: bool = Field(False, description="Whether coordinates are screen-absolute.")
    monitor_index: int | None = Field(
        None, description="0-based monitor index for 'absolute=True' coordinate translation."
    )

    # Action parameters
    text: str | None = Field(None, description="Text to enter for 'set_text'.")
    expected_text: str | None = Field(None, description="Text to verify for 'verify_text'.")
    exact_match: bool = Field(False, description="Use exact match for 'verify_text'.")
    button: Literal["left", "right", "middle"] = Field("left", description="Mouse button for clicks.")
    duration: float = Field(0.0, description="Duration for 'hover' or movement delay.")

    # Cua-style snapshot targeting
    snapshot_id: str | None = Field(None, description="Snapshot from get_window_state; use with element_index.")
    element_index: int | None = Field(None, description="Index from snapshot elements[].element_index.")
    dispatch: Literal["foreground", "background"] | None = Field(
        None,
        description="Input dispatch mode; default from windows_computer_use_mcp_DISPATCH (foreground).",
    )

    # Outcome verification
    verify: bool = Field(
        False,
        description="If True, verify the action succeeded (e.g. text appeared, state changed)."
        " On failure, retries with the configured retry policy.",
    )
    verify_text: str | None = Field(
        None,
        description="For click/set_text with verify=True: expected text to appear after the action.",
    )

    # Discovery parameters
    max_depth: int = Field(2, description="Max depth for 'list' recursion.")
    timeout: float = Field(10.0, description="Max wait time in seconds.")


class MouseOperationRequest(BaseModel):
    """Request model for mouse input operations."""

    operation: Literal[
        "move",
        "move_relative",
        "click",
        "double_click",
        "right_click",
        "scroll",
        "drag",
        "hover",
        "position",
        "telemetry",
    ] = Field(..., description="The mouse operation to perform.")

    x: int | None = Field(None, description="X coordinate or relative X offset.")
    y: int | None = Field(None, description="Y coordinate or relative Y offset.")
    monitor_index: int | None = Field(
        None,
        description="0-based monitor index. When set, x/y are treated as relative "
        "to this monitor's origin. Pass None (default) for absolute virtual screen coordinates.",
    )

    target_x: int | None = Field(None, description="Target X for 'drag'.")
    target_y: int | None = Field(None, description="Target Y for 'drag'.")

    # Legacy aliases support
    x2: int | None = Field(None, description="Alias for target_x.")
    y2: int | None = Field(None, description="Alias for target_y.")

    button: Literal["left", "right", "middle"] = Field("left", description="Mouse button to use.")
    amount: int = Field(1, description="Amount to scroll or number of clicks.")
    clicks: int = Field(1, description="Alias for amount.")

    horizontal: bool = Field(False, description="Whether to scroll horizontally.")
    duration: float = Field(0.0, description="Movement duration in seconds.")
    hover_duration: float = Field(0.5, description="Duration to pause for 'hover'.")

    telemetry_duration: int = Field(10, description="Duration in seconds to show the HUD.")
    capture_keys: bool = Field(False, description="Whether to capture key presses in HUD.")


class KeyloggerOperationRequest(BaseModel):
    """Request model for global keyboard capture (pynput low-level hook)."""

    operation: Literal["start", "stop", "status", "read", "clear"] = Field(
        ..., description="Keylogger operation: start/stop the listener, status, read buffered events, or clear buffer."
    )
    max_buffer: int = Field(
        5000,
        description="Ring buffer capacity for 'start' (oldest dropped when full).",
        ge=1,
        le=100_000,
    )
    include_release: bool = Field(
        False,
        description="For 'start': also record key release events (roughly doubles volume).",
    )
    limit: int = Field(100, description="Max events to return for 'read' (most recent batch).", ge=1, le=10_000)
    flush: bool = Field(
        False,
        description="For 'read': remove returned events from the buffer (keeps older events if any).",
    )


class KeyboardOperationRequest(BaseModel):
    """Request model for keyboard input operations."""

    operation: Literal["type", "hotkey", "press", "release", "hold"] = Field(
        ..., description="The keyboard operation to perform."
    )

    text: str | None = Field(None, description="Text to type for 'type'.")
    key: str | None = Field(None, description="Single key for 'press'.")
    keys: list[str] | None = Field(None, description="Key list for 'hotkey' or 'hold'.")

    presses: int = Field(1, description="Number of times to press the key.")
    interval: float = Field(0.0, description="Pause between characters for 'type'.")
    pause: float = Field(0.0, description="Pause between repeated presses.")
    window_handle: int | None = Field(None, description="HWND to focus before send (win32 keyboard backend).")


class VisualOperationRequest(BaseModel):
    """Request model for visual/OCR operations."""

    operation: Literal[
        "screenshot",
        "extract_text",
        "find_image",
        "highlight",
        "record",
        "record_to_gif",
        "find_image_multi_scale",
        "find_image_feature_match",
        "describe_region",
    ] = Field(..., description="The visual operation to perform.")

    window_handle: int | None = Field(None, description="HWND of target window.")

    monitor_index: int | None = Field(
        None,
        description="0-based monitor index. When set without region, captures the full "
        "monitor. When set with region, region coordinates are relative to this monitor's origin.",
    )

    region_left: int | None = Field(None, description="X1 coordinate of region.")
    region_top: int | None = Field(None, description="Y1 coordinate of region.")
    region_right: int | None = Field(None, description="X2 coordinate of region.")
    region_bottom: int | None = Field(None, description="Y2 coordinate of region.")

    image_path: str | None = Field(None, description="Source image path for OCR.")
    template_path: str | None = Field(None, description="Template image path for matching.")
    output_path: str | None = Field(None, description="Path to save output image.")

    format: str = Field("png", description="Image format (png, jpg, etc.).")
    return_base64: bool = Field(False, description="Return base64 string instead of path.")

    language: str = Field("eng", description="Tesseract language code.")
    ocr_config: str = Field("--psm 6", description="Tesseract config flags.")
    ocr_provider: str | None = Field(
        None, description="OCR provider: 'tesseract' (default), 'windowsmedia' (WinRT built-in)."
    )
    threshold: float = Field(0.8, description="Matching confidence threshold (0-1).", ge=0, le=1)

    control_id: str | None = Field(None, description="Element ID for highlighting.")
    color: str = Field("red", description="Highlight color name.")
    thickness: int = Field(2, description="Highlight border thickness.", ge=1)
    highlight_duration: float = Field(3.0, description="Duration to show highlight in seconds.", ge=0)

    # Recording options
    duration: float = Field(10.0, description="Recording duration in seconds (for record/record_to_gif).", ge=1, le=300)
    fps: int = Field(10, description="Frames per second for recording.", ge=1, le=60)


class FaceOperationRequest(BaseModel):
    """Request model for face recognition operations."""

    operation: Literal["add", "recognize", "list", "delete", "capture"] = Field(
        ..., description="The face recognition operation."
    )

    name: str | None = Field(None, description="Person's name for registration/deletion.")
    image_path: str | None = Field(None, description="Image path for recognition/registration.")
    camera_index: int = Field(0, description="Webcam index (0 is primary).", ge=0)
    save_capture_path: str | None = Field(None, description="Path to save captured frame.")
    tolerance: float = Field(0.6, description="Matching tolerance (lower is stricter).", ge=0, le=1)


class SystemOperationRequest(BaseModel):
    """Request model for system-level operations."""

    operation: Literal[
        "status",
        "help",
        "wait",
        "info",
        "wait_for_window",
        "clipboard_get",
        "clipboard_set",
        "processes",
        "start_app",
        "telemetry",
        "analyze_failures",
        "issue_draft",
        "weekly_report",
        "voice_listen",
        "voice_status",
    ] = Field(..., description="The system operation to perform.")

    seconds: float | None = Field(None, description="Seconds to wait.", ge=0)
    title: str | None = Field(None, description="Window title for wait_for_window.")
    timeout: float = Field(10.0, description="Operation timeout in seconds.", ge=0)
    exact_match: bool = Field(False, description="Exact title match if True.")
    text: str | None = Field(None, description="Clipboard text content.")
    app_path: str | None = Field(None, description="App executable path.")
    work_dir: str | None = Field(None, description="App working directory.")
    filter: str | None = Field(None, description="Process name filter.")


class DesktopStateRequest(BaseModel):
    """Request model for get_desktop_state discovery."""

    use_vision: bool = Field(False, description="Include annotated screenshots.")
    use_ocr: bool = Field(False, description="Use OCR for text extraction.")
    capture_mode: Literal["ax", "som", "vision"] | None = Field(
        None,
        description="Cua-style capture: ax (tree only), som (tree + annotated screenshot), vision (image only).",
    )
    max_depth: int = Field(10, description="Max UI tree depth.", ge=1)
    element_timeout: float = Field(0.5, description="Timeout per element capture.", ge=0)


class WindowStateRequest(BaseModel):
    """Request model for get_window_state (per-window, Cua-shaped)."""

    window_handle: int = Field(..., description="Target window HWND.")
    capture_mode: Literal["ax", "som", "vision"] = Field(
        "som",
        description="ax = UIA tree only; som = tree + set-of-mark screenshot; vision = window image only.",
    )
    use_ocr: bool = Field(False, description="OCR enrich elements when capture_mode is som.")
    max_depth: int = Field(10, description="Max UI tree depth.", ge=1)
    element_timeout: float = Field(0.5, description="Timeout per element capture.", ge=0)


class TaskOperationRequest(BaseModel):
    """Request model for closed-loop automation_task runner."""

    operation: Literal["run", "status", "cancel", "list_profiles", "list_templates"] = Field(
        ..., description="Task operation."
    )

    app: str | None = Field(None, description="App profile id (vroidstudio, libreoffice).")
    task_id: str | None = Field(None, description="Task session id for status/cancel/run.")
    window_handle: int | None = Field(None, description="Default HWND for steps.")
    steps: list[dict[str, Any]] | None = Field(None, description="Step list for run.")
    output_dir: str | None = Field(None, description="Directory for evidence screenshots.")


class ShortcutOperationRequest(BaseModel):
    """Request model for semantic app shortcuts."""

    operation: Literal["send", "list", "describe", "profile_list", "profile_detect", "profile_shortcut"] = Field(
        ..., description="Shortcut operation."
    )

    app: str | None = Field(None, description="Application id (vroidstudio, notepad, paint, or profile name).")
    action: str | None = Field(None, description="Semantic action (export_vrm, save, bold, ...).")
    window_handle: int | None = Field(None, description="HWND to focus before send (win32 backend).")
    verify_stable: bool | None = Field(None, description="Wait for UI stable after send; default from registry.")
    pause: float = Field(0.05, description="Pause after key send.", ge=0)

    # Profile operations
    profile_name: str | None = Field(None, description="Profile name for profile_shortcut operation.")
    window_title: str | None = Field(None, description="Window title for profile_detect operation.")
    window_class: str | None = Field(None, description="Window class for profile_detect operation.")
    process_name: str | None = Field(None, description="Process name for profile_detect operation.")


class DialogOperationRequest(BaseModel):
    """Request model for file dialog path entry."""

    operation: Literal["set_path", "confirm", "submit_path"] = Field(..., description="Dialog operation.")

    path: str | None = Field(None, description="File path for set_path / submit_path.")
    use_clipboard: bool = Field(True, description="Paste via clipboard (recommended for long paths).")
    select_all_first: bool = Field(True, description="Ctrl+A before paste/type.")
    confirm_key: str = Field("enter", description="Key to confirm dialog (enter, escape).")
    pause_before_confirm_s: float = Field(0.3, description="Pause before confirm key.", ge=0)
    post_confirm_pause_s: float = Field(0.0, description="Pause after confirm (submit_path).", ge=0)
    type_interval: float = Field(0.02, description="Per-char interval when typing path.", ge=0)


class AssertOperationRequest(BaseModel):
    """Request model for UI verification and stability assertions."""

    operation: Literal[
        "hash",
        "hash_region",
        "diff",
        "wait_stable",
        "assert_changed",
        "assert_unchanged",
        "assert_template",
        "assert_text",
    ] = Field(..., description="Verification operation to perform.")

    window_handle: int | None = Field(None, description="HWND for live capture.")
    image_path: str | None = Field(None, description="Primary image path (before / source).")
    image_path_b: str | None = Field(None, description="Second image path (after) for diff/assert ops.")

    region_left: int | None = Field(None, description="Region left (X1).")
    region_top: int | None = Field(None, description="Region top (Y1).")
    region_right: int | None = Field(None, description="Region right (X2).")
    region_bottom: int | None = Field(None, description="Region bottom (Y2).")

    hash_algorithm: Literal["sha256", "dhash"] = Field("dhash", description="Hash algorithm for stability checks.")
    stable_frames_required: int = Field(2, description="Consecutive stable frames for wait_stable.", ge=1)
    poll_interval_s: float = Field(0.5, description="Poll interval for wait_stable.", ge=0.05)
    timeout_s: float = Field(10.0, description="Timeout for wait_stable.", ge=0.5)

    change_threshold_pct: float = Field(1.0, description="Min % pixel change for assert_changed.", ge=0)
    unchanged_threshold_pct: float = Field(0.5, description="Max % pixel change for assert_unchanged.", ge=0)
    pixel_diff_threshold: int = Field(25, description="Per-pixel diff sensitivity (0-255).", ge=1, le=255)

    template_path: str | None = Field(None, description="Template image for assert_template.")
    match_threshold: float = Field(0.8, description="Template match confidence (0-1).", ge=0, le=1)

    expected_text: str | None = Field(None, description="Text to find for assert_text.")
    exact_match: bool = Field(False, description="Exact OCR match if true.")
    language: str = Field("eng", description="Tesseract language code.")

    output_path: str | None = Field(None, description="Path to save diff/heatmap PNG.")
    output_dir: str | None = Field(None, description="Directory for wait_stable snapshot files.")
    evidence_bundle: bool = Field(False, description="Include before/after/diff paths in error data.")


class MissionOperationRequest(BaseModel):
    """Request model for high-level agentic missions."""

    operation: Literal["run", "plan", "status", "cancel", "record", "replay", "workflow", "run_preset"] = Field(
        "run", description="The mission operation to perform. 'run' executes the full autonomous loop."
    )
    preset_name: str | None = Field(
        None, description="For 'run_preset': name of a preset workflow file (without .json)."
    )
    app: str | None = Field(None, description="For 'workflow' operation: target application (e.g. 'notepad.exe').")
    actions: list[dict] | None = Field(
        None, description="For 'workflow' operation: list of action dicts like [{'tool': 'elements', 'params': {...}}]."
    )
    timeout: float | None = Field(None, description="Max seconds for the workflow to complete.", ge=1)
    goal: str = Field("", description="The high-level objective to achieve (required for plan).")
    strategy: Literal["element", "visual"] = Field(
        "element", description="Whether to prefer UIA elements or visual cues."
    )
    mission_id: str | None = Field(None, description="Unique ID for session persistence.")
    steps: list[dict] | None = Field(None, description="Pre-defined steps for 'replay'.")


class ToolResult(BaseModel):
    """Standardized response model for all MCP tools."""

    status: Literal["success", "error", "clarification_needed", "blocked"] = Field(
        ..., description="The outcome of the operation."
    )

    message: str = Field(..., description="A human-readable summary of the result.")

    data: Any | None = Field(None, description="Operation-specific payload (e.g., window metadata).")

    recovery_tip: str | None = Field(
        None, description="Actionable guidance for agents if the operation failed or was ambiguous."
    )
