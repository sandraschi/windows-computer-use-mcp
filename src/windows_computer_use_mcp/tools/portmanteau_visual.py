"""Visual/Screenshot/OCR portmanteau tool for PyWinAuto MCP.

PORTMANTEAU PATTERN RATIONALE:
Instead of creating 5+ separate tools (one per visual operation), this tool consolidates related
visual operations into a single interface. This design:
- Prevents tool explosion (5+ tools → 1 tool) while maintaining full functionality
- Improves discoverability by grouping related operations together
- Follows FastMCP 2.13+ best practices for feature-rich MCP servers

SUPPORTED OPERATIONS:
- screenshot: Capture screen, window, or region
- extract_text: OCR text extraction from image or screen region
- find_image: Template matching to find image on screen
- highlight: Highlight a UI element with colored rectangle
"""

import base64
import logging
import os
import tempfile
import time

import cv2
import numpy as np
from PIL import Image, ImageGrab
from pywinauto import Desktop

# Import the FastMCP app instance
try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in portmanteau_visual")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in portmanteau_visual: {e}")
    app = None
from windows_computer_use_mcp.display_utils import enum_monitors, get_monitor_by_index
from windows_computer_use_mcp.tools.models import ToolResult, VisualOperationRequest

# Try to import OCR
try:
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract not available. OCR functionality will be limited.")


if app is not None:
    logger.info("Registering portmanteau_visual tool with FastMCP")

    @app.tool(
        name="automation_visual",
        description="""Comprehensive computer vision and OCR tool for Windows UI automation.

WHAT IT DOES:
This tool provides multimodal capabilities for interacting with the desktop when traditional UI element selectors (UIA/MSAA) are insufficient or unavailable (e.g., in remote desktops, games, or legacy apps). It supports pixel-perfect screenshots, Tesseract-based OCR text extraction, OpenCV template matching to find graphical assets, and temporary visual highlighting.

WHEN TO USE:
- Use 'screenshot' to capture current UI states for verification or documentation.
- Use 'extract_text' (OCR) to read text from custom-drawn controls, icons, or web-in-app views.
- Use 'find_image' when you have a template image (e.g., a specific button icon) and need to click its center coordinates.
- Use 'highlight' to visually confirm the identified target during complex automation sequences.

RECOVERY AND AMBIGUITY:
If 'find_image' fails to meet the confidence threshold (default 0.8), consider decreasing the 'threshold' parameter or verifying that the template image is not resolution-dependent. If OCR results are noisy, ensure the target region coordinates are precisely bounded or use 'ocr_config' to specify page segmentation modes.
""",
    )
    def automation_visual(request: VisualOperationRequest) -> ToolResult:
        """Comprehensive visual automation tool for screenshots, OCR, and image recognition."""
        try:
            timestamp = time.time()
            operation = request.operation
            window_handle = request.window_handle
            region_left = request.region_left
            region_top = request.region_top
            region_right = request.region_right
            region_bottom = request.region_bottom
            image_path = request.image_path
            template_path = request.template_path
            output_path = request.output_path
            format_ext = request.format
            return_base64 = request.return_base64
            language = request.language
            ocr_config = request.ocr_config
            threshold = request.threshold
            control_id = request.control_id
            color = request.color
            thickness = request.thickness
            # highlight_duration = request.highlight_duration # Currently unused in implementation

            monitors = []
            try:
                monitors = [
                    {"index": m.index, "width": m.width, "height": m.height,
                     "left": m.left, "top": m.top, "primary": m.is_primary}
                    for m in enum_monitors()
                ]
            except Exception:
                pass
            visual_metadata = {
                "timestamp": timestamp,
                "engine": "opencv_tesseract_pillow",
                "identity": "pywinauto-mcp-sota-2026",
                "monitor_count": len(monitors),
                "monitors": monitors,
            }

            # Build region tuple — support monitor_index for per-monitor capture
            region = None
            mi = None
            if request.monitor_index is not None:
                try:
                    mi = get_monitor_by_index(request.monitor_index)
                except Exception as e:
                    logger.warning(f"Invalid monitor_index {request.monitor_index}: {e}")

            if mi is not None:
                if all(v is not None for v in [region_left, region_top, region_right, region_bottom]):
                    # Region coords relative to monitor origin
                    region = (region_left + mi.left, region_top + mi.top,
                              region_right + mi.left, region_bottom + mi.top)
                else:
                    # Full monitor capture
                    region = (mi.left, mi.top, mi.right, mi.bottom)
            elif all(v is not None for v in [region_left, region_top, region_right, region_bottom]):
                region = (region_left, region_top, region_right, region_bottom)

            # === SCREENSHOT OPERATION ===
            if operation == "screenshot":
                from windows_computer_use_mcp.win32_window import get_window_bbox

                if window_handle is not None:
                    try:
                        left, top, right, bottom = get_window_bbox(window_handle)
                        if region:
                            left += region[0]
                            top += region[1]
                            right = min(left + (region[2] - region[0]), right)
                            bottom = min(top + (region[3] - region[1]), bottom)
                        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                    except Exception as e:
                        return ToolResult(
                            status="error",
                            message=f"Failed to capture window: {e}",
                            recovery_tip="Ensure the window handle is still valid and the window is not minimized or obscured.",
                        )
                elif region:
                    screenshot = ImageGrab.grab(bbox=region)
                else:
                    screenshot = ImageGrab.grab()

                import io
                import shutil
                import subprocess
                img_buffer = io.BytesIO()
                screenshot.save(img_buffer, format=format_ext.upper())
                img_bytes = img_buffer.getvalue()

                img_b64 = None
                file_path = None
                if return_base64:
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")

                # Save to file if output_path is provided or if not returning base64
                if not return_base64 or output_path:
                    if output_path:
                        with open(output_path, "wb") as f:
                            f.write(img_bytes)
                        file_path = output_path
                    else:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format_ext}") as f:
                            f.write(img_bytes)
                            file_path = f.name

                return ToolResult(
                    status="success",
                    message="Screenshot captured successfully.",
                    data={
                        "image_b64": img_b64,
                        "size": len(img_bytes),
                        "screenshot_path": file_path,
                        "timestamp": timestamp,
                        "visual_metadata": visual_metadata,
                    },
                )

            # === EXTRACT_TEXT OPERATION ===
            elif operation == "extract_text":
                if not OCR_AVAILABLE:
                    return ToolResult(
                        status="error",
                        message="OCR functionality is unavailable because pytesseract is not installed.",
                        recovery_tip="Install Tesseract OCR on the host and run 'pip install pytesseract'.",
                    )

                # Get image
                if image_path:
                    if not os.path.exists(image_path):
                        return ToolResult(
                            status="error",
                            message=f"Image file not found: {image_path}",
                            recovery_tip="Verify the image path or capture a new screenshot using 'screenshot' first.",
                        )
                    image = Image.open(image_path)
                else:
                    # Take screenshot
                    if region:
                        image = ImageGrab.grab(bbox=region)
                    elif window_handle:
                        import win32gui

                        rect = win32gui.GetWindowRect(window_handle)
                        image = ImageGrab.grab(bbox=rect)
                    else:
                        image = ImageGrab.grab()

                # Convert to grayscale for better OCR
                image = image.convert("L")

                # Choose OCR provider: default = Windows Media OCR, fallback = Tesseract
                provider = (request.ocr_provider or os.environ.get("WINDOWS_COMPUTER_USE_MCP_OCR_PROVIDER", "")).lower()
                if provider == "tesseract":
                    use_tesseract = True
                elif provider == "windowsmedia":
                    use_tesseract = False
                else:
                    from windows_computer_use_mcp.windows_media_ocr import is_available as wm_avail
                    use_tesseract = not wm_avail()

                if not use_tesseract:
                    from windows_computer_use_mcp.windows_media_ocr import extract_text as wm_ocr
                    temp_path = f"_ocr_temp_{int(time.time())}.png"
                    try:
                        image.save(temp_path)
                        text = wm_ocr(temp_path)
                    except Exception as e:
                        logger.warning("Windows Media OCR failed (%s), falling back to Tesseract", e)
                        text = pytesseract.image_to_string(image, lang=language, config=ocr_config)
                    finally:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    avg_confidence = -1
                else:
                    text = pytesseract.image_to_string(image, lang=language, config=ocr_config)
                    try:
                        data = pytesseract.image_to_data(
                            image, lang=language, config=ocr_config, output_type=pytesseract.Output.DICT
                        )
                        confidences = [float(c) for c in data["conf"] if float(c) > 0]
                        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    except:
                        avg_confidence = -1

                return ToolResult(
                    status="success",
                    message=f"Text extracted successfully using language '{language}'.",
                    data={
                        "text": text.strip(),
                        "confidence": avg_confidence,
                        "language": language,
                        "timestamp": timestamp,
                        "visual_metadata": visual_metadata,
                    },
                )

            # === FIND_IMAGE OPERATION ===
            elif operation == "find_image":
                if not template_path:
                    return ToolResult(
                        status="error",
                        message="template_path parameter is required for 'find_image' operation.",
                        recovery_tip="Provide a valid path to a template image file.",
                    )

                if not os.path.exists(template_path):
                    return ToolResult(
                        status="error",
                        message=f"Template file not found: {template_path}",
                        recovery_tip="Ensure the template image exists at the specified location.",
                    )

                # Load template
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is None:
                    return ToolResult(
                        status="error",
                        message=f"Failed to load template image: {template_path}",
                        recovery_tip="Check if the file is a valid image format supported by OpenCV.",
                    )

                template_h, template_w = template.shape[:2]

                # Take screenshot
                if region:
                    screenshot = ImageGrab.grab(bbox=region)
                elif window_handle:
                    import win32gui

                    rect = win32gui.GetWindowRect(window_handle)
                    screenshot = ImageGrab.grab(bbox=rect)
                else:
                    screenshot = ImageGrab.grab()

                # Convert to OpenCV format
                screen_cv = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # Template matching
                result_cv = cv2.matchTemplate(screen_cv, template, cv2.TM_CCOEFF_NORMED)
                _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result_cv)

                best_match = None
                if max_val >= threshold:
                    x, y = max_loc
                    center_x = x + (template_w // 2)
                    center_y = y + (template_h // 2)

                    best_match = {
                        "confidence": float(max_val),
                        "location": {
                            "x": int(center_x),
                            "y": int(center_y),
                            "left": int(x),
                            "top": int(y),
                            "right": int(x + template_w),
                            "bottom": int(y + template_h),
                            "width": int(template_w),
                            "height": int(template_h),
                        },
                    }

                return ToolResult(
                    status="success",
                    message="Match found" if best_match else f"No match found above threshold {threshold}",
                    data={
                        "found": bool(best_match),
                        "best_match": best_match,
                        "threshold": threshold,
                        "timestamp": timestamp,
                        "visual_metadata": visual_metadata,
                    },
                    recovery_tip="If no match was found, try decreasing the 'threshold' or ensure the UI is currently visible."
                    if not best_match
                    else None,
                )

            # === MULTI-SCALE FIND IMAGE ===
            elif operation == "find_image_multi_scale":
                if not template_path:
                    return ToolResult(status="error", message="template_path is required.")
                if not os.path.exists(template_path):
                    return ToolResult(status="error", message=f"Template not found: {template_path}")

                try:
                    from windows_computer_use_mcp.computer_vision import find_template_multi_scale

                    scale_min = 0.5
                    scale_max = 2.0
                    matches = find_template_multi_scale(
                        template_path, region=region, window_handle=window_handle,
                        threshold=threshold, scale_min=scale_min, scale_max=scale_max,
                    )
                    return ToolResult(
                        status="success",
                        message=f"Found {len(matches)} matches (multi-scale).",
                        data={"found": len(matches) > 0, "matches": matches[:10],
                              "match_count": len(matches), "timestamp": timestamp,
                              "visual_metadata": visual_metadata},
                    )
                except Exception as e:
                    return ToolResult(status="error", message=f"Multi-scale matching failed: {e}")

            # === FEATURE MATCH FIND IMAGE ===
            elif operation == "find_image_feature_match":
                if not template_path:
                    return ToolResult(status="error", message="template_path is required.")
                if not os.path.exists(template_path):
                    return ToolResult(status="error", message=f"Template not found: {template_path}")

                try:
                    from windows_computer_use_mcp.computer_vision import find_template_feature_match

                    matches = find_template_feature_match(
                        template_path, region=region, window_handle=window_handle,
                        min_matches=8,
                    )
                    return ToolResult(
                        status="success",
                        message=f"Found {len(matches)} feature matches.",
                        data={"found": len(matches) > 0, "matches": matches,
                              "timestamp": timestamp, "visual_metadata": visual_metadata},
                    )
                except Exception as e:
                    return ToolResult(status="error", message=f"Feature matching failed: {e}")

            # === DESCRIBE REGION ===
            elif operation == "describe_region":
                try:
                    from windows_computer_use_mcp.computer_vision import describe_region

                    desc = describe_region(region=region)
                    return ToolResult(
                        status="success",
                        message=f"Described region: {desc['width']}x{desc['height']}, {desc['object_count']} objects.",
                        data={**desc, "timestamp": timestamp, "visual_metadata": visual_metadata},
                    )
                except Exception as e:
                    return ToolResult(status="error", message=f"Region description failed: {e}")

            # === HIGHLIGHT OPERATION ===
            elif operation == "highlight":
                if window_handle is None or control_id is None:
                    return ToolResult(
                        status="error",
                        message="window_handle and control_id are required for 'highlight' operation.",
                        recovery_tip="Specify both the parent window handle and the target element's control_id.",
                    )

                desktop = Desktop(backend="uia")
                window = desktop.window(handle=window_handle)
                element = window.child_window(control_id=control_id)

                if not element.exists():
                    return ToolResult(
                        status="error",
                        message=f"Element with control_id '{control_id}' not found in window {window_handle}.",
                        recovery_tip="Verify the control_id using 'get_desktop_state' or 'automation_elements(operation=\"list\")'.",
                    )

                rect = element.rectangle()

                import win32gui

                win_rect = win32gui.GetWindowRect(window_handle)
                screenshot = ImageGrab.grab(bbox=win_rect)
                img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

                # Convert color
                color_map = {
                    "red": (0, 0, 255),
                    "green": (0, 255, 0),
                    "blue": (255, 0, 0),
                    "yellow": (0, 255, 255),
                }
                bgr = color_map.get(color.lower(), (0, 0, 255))

                # Draw rectangle (adjust for window position)
                top_left = (rect.left - win_rect[0], rect.top - win_rect[1])
                bottom_right = (rect.right - win_rect[0], rect.bottom - win_rect[1])
                cv2.rectangle(img, top_left, bottom_right, bgr, thickness)

                # Save or return
                if output_path:
                    cv2.imwrite(output_path, img)
                    file_path = output_path
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                        cv2.imwrite(f.name, img)
                        file_path = f.name

                return ToolResult(
                    status="success",
                    message=f"Element '{control_id}' highlighted successfully.",
                    data={
                        "file_path": file_path,
                        "element": {
                            "control_id": control_id,
                            "left": rect.left,
                            "top": rect.top,
                            "right": rect.right,
                            "bottom": rect.bottom,
                            "width": rect.width(),
                            "height": rect.height(),
                        },
                        "timestamp": timestamp,
                    },
                )

            # === RECORD / RECORD_TO_GIF (ffmpeg-based screen capture) ===
            elif operation in ("record", "record_to_gif"):
                import io
                import shutil
                import subprocess
                rec_duration = request.duration
                rec_fps = request.fps
                out_path = request.output_path or os.path.join(
                    os.getcwd(), f"screenshot_{operation}_{int(time.time())}.mp4" if operation == "record" else f"screenshot_{operation}_{int(time.time())}.gif"
                )
                total_frames = int(rec_duration * rec_fps)
                interval = rec_duration / max(total_frames, 1)

                ffmpeg_path = shutil.which("ffmpeg") or r"C:\Users\sandr\scoop\shims\ffmpeg.exe"
                if ffmpeg_path is None:
                    raise RuntimeError("ffmpeg not found. Install with: scoop install ffmpeg")

                if operation == "record":
                    cmd = [
                        ffmpeg_path, "-y", "-f", "image2pipe", "-framerate", str(rec_fps),
                        "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        str(out_path)
                    ]
                else:
                    cmd = [
                        ffmpeg_path, "-y", "-f", "image2pipe", "-framerate", str(rec_fps),
                        "-i", "-", "-vf", "fps=10,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                        str(out_path)
                    ]

                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                try:
                    for _ in range(total_frames):
                        if window_handle:
                            import win32gui
                            rect = win32gui.GetWindowRect(window_handle)
                            frame = ImageGrab.grab(bbox=rect)
                        else:
                            frame = ImageGrab.grab()
                        buf = io.BytesIO()
                        frame.save(buf, format="PNG")
                        proc.stdin.write(buf.getvalue())
                        time.sleep(interval)
                finally:
                    proc.stdin.close()
                    proc.wait()

                size_mb = round(os.path.getsize(out_path) / (1024 * 1024), 1) if os.path.exists(out_path) else 0
                return ToolResult(
                    status="success",
                    message=f"Recording saved: {out_path} ({size_mb} MB, {rec_duration}s, {rec_fps}fps)",
                    data={"path": str(out_path), "duration": rec_duration, "fps": rec_fps, "frames": total_frames, "size_mb": size_mb},
                )

            else:
                return ToolResult(
                    status="error",
                    message=f"Unknown operation: {operation}",
                    recovery_tip="Supported operations are: screenshot, extract_text, find_image, highlight, record, record_to_gif.",
                )

        except Exception as e:
            return ToolResult(
                status="error",
                message=f"Visual operation failed: {e}",
                recovery_tip="Check if all vision dependencies (opencv-python, pytesseract, pillow) are correctly installed.",
            )


__all__ = ["automation_visual"]
