"""Visual tools for PyWinAuto MCP.

This module provides functions for taking screenshots, image processing,
and optical character recognition (OCR).
"""

import base64
import io
import logging
import os
import tempfile
import time
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageGrab

# Import the FastMCP app instance
try:
    from windows_computer_use_mcp.main import app

    logger = logging.getLogger(__name__)
    logger.info("Successfully imported FastMCP app instance in visual tools")
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import FastMCP app in visual tools: {e}")
    app = None

# Try to import OCR dependencies
try:
    import pytesseract

    OCR_AVAILABLE = True
except ImportError:
    logger.warning("pytesseract not available. OCR functionality will be limited.")
    OCR_AVAILABLE = False

# Only proceed with tool registration if app is available
if app is not None:
    logger.info("Registering visual tools with FastMCP")

    @app.tool(
        name="take_screenshot",
        description="Take a screenshot of the entire screen or a specific window.",
    )
    def take_screenshot(
        window_handle: int | None = None,
        region: tuple[int, int, int, int] | None = None,
        format: str = "png",
        return_base64: bool = False,
    ) -> dict[str, Any]:
        """Take a screenshot of the entire screen or a specific window.

        Args:
            window_handle: Optional handle of the window to capture (None for entire screen)
            region: Optional tuple (left, top, right, bottom) defining the region to capture
            format: Image format ("png" or "jpg")
            return_base64: If True, return the image as a base64-encoded string

        Returns:
            Dict containing the screenshot data or an error message

        """
        try:
            # Validate format
            format = format.lower()
            if format not in ["png", "jpg", "jpeg"]:
                return {"status": "error", "error": "Invalid format. Must be 'png' or 'jpg'"}

            # Capture the screen or window
            if window_handle is not None:
                import win32gui
                from pywinauto.win32functions import SetForegroundWindow
                from pywinauto.win32structures import RECT

                # Bring window to foreground
                try:
                    SetForegroundWindow(window_handle)
                    time.sleep(0.5)  # Give window time to come to foreground
                except Exception as e:
                    logger.warning(f"Could not bring window to foreground: {e}")

                # Get window rectangle
                try:
                    rect = RECT()
                    win32gui.GetWindowRect(window_handle, rect)
                    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

                    # Adjust for DPI scaling
                    try:
                        from ctypes import windll

                        user32 = windll.user32
                        user32.SetProcessDPIAware()

                        # Get DPI scale factor
                        screen = user32.GetDC(0)
                        scale_x = 96.0 / user32.GetDeviceCaps(screen, 88)  # LOGPIXELSX
                        scale_y = 96.0 / user32.GetDeviceCaps(screen, 90)  # LOGPIXELSY
                        user32.ReleaseDC(0, screen)

                        # Scale coordinates
                        left = int(left * scale_x)
                        top = int(top * scale_y)
                        right = int(right * scale_x)
                        bottom = int(bottom * scale_y)
                    except Exception as e:
                        logger.warning(f"Could not adjust for DPI scaling: {e}")

                    # Apply region if specified
                    if region:
                        reg_left, reg_top, reg_right, reg_bottom = region
                        left += reg_left
                        top += reg_top
                        right = min(left + (reg_right - reg_left), right)
                        bottom = min(top + (reg_bottom - reg_top), bottom)

                    # Ensure valid dimensions
                    if right <= left or bottom <= top:
                        return {"status": "error", "error": "Invalid window dimensions"}

                    # Capture the window
                    screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
                except Exception as e:
                    logger.error(f"Error capturing window: {e}")
                    return {"status": "error", "error": f"Failed to capture window: {e}"}
            else:
                # Capture entire screen or specified region
                if region:
                    screenshot = ImageGrab.grab(bbox=region)
                else:
                    screenshot = ImageGrab.grab()

            # Save to bytes
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format=format)
            img_byte_arr = img_byte_arr.getvalue()

            # Prepare response
            result = {
                "status": "success",
                "format": format,
                "size": len(img_byte_arr),
                "timestamp": time.time(),
            }

            # Add base64 if requested
            if return_base64:
                result["image_base64"] = base64.b64encode(img_byte_arr).decode("utf-8")
            else:
                # Save to temp file and return path
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}") as temp_file:
                    temp_file.write(img_byte_arr)
                    temp_file_path = temp_file.name
                result["file_path"] = temp_file_path

            return result

        except Exception as e:
            logger.error(f"Error in take_screenshot: {e}")
            return {"status": "error", "error": str(e)}

    @app.tool()
    def extract_text(
        image_path: str | None = None,
        window_handle: int | None = None,
        region: tuple[int, int, int, int] | None = None,
        language: str = "eng",
        config: str = "--psm 6",
    ) -> dict[str, Any]:
        """Extract text from an image or screen region using OCR.

        Args:
            image_path: Path to the image file (if not using window/region)
            window_handle: Handle of the window to capture (if not using image_path)
            region: Region to capture (left, top, right, bottom)
            language: Language code for OCR (e.g., 'eng', 'fra', 'spa')
            config: Tesseract configuration parameters

        Returns:
            Dict containing the extracted text and confidence scores

        """
        if not OCR_AVAILABLE:
            return {
                "status": "error",
                "error": "OCR functionality not available. Install pytesseract.",
            }

        try:
            # Get image from source
            if image_path:
                if not os.path.exists(image_path):
                    return {"status": "error", "error": f"Image file not found: {image_path}"}
                image = Image.open(image_path)
            else:
                # Take screenshot of window or region
                screenshot = take_screenshot(window_handle=window_handle, region=region, return_base64=False)
                if screenshot["status"] != "success":
                    return screenshot

                try:
                    image = Image.open(screenshot["file_path"])
                    # Clean up temp file
                    try:
                        os.unlink(screenshot["file_path"])
                    except:
                        pass
                except Exception as e:
                    return {"status": "error", "error": f"Failed to process screenshot: {e}"}

            # Convert to grayscale for better OCR
            image = image.convert("L")

            # Extract text using pytesseract
            text = pytesseract.image_to_string(image, lang=language, config=config)

            # Get confidence scores if available
            try:
                data = pytesseract.image_to_data(
                    image, lang=language, config=config, output_type=pytesseract.Output.DICT
                )
                confidences = [float(c) for c in data["conf"] if float(c) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            except:
                avg_confidence = -1

            return {
                "status": "success",
                "text": text.strip(),
                "confidence": avg_confidence,
                "language": language,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(f"Error in extract_text: {e}")
            return {"status": "error", "error": str(e)}

    @app.tool()
    def find_image(
        template_path: str,
        window_handle: int | None = None,
        region: tuple[int, int, int, int] | None = None,
        threshold: float = 0.8,
    ) -> dict[str, Any]:
        """Find a template image within a screenshot or window.

        Args:
            template_path: Path to the template image to find
            window_handle: Optional handle of the window to search in (None for entire screen)
            region: Optional region (left, top, right, bottom) to search within
            threshold: Confidence threshold (0-1) for template matching

        Returns:
            Dict containing the match results

        """
        try:
            # Validate template path
            if not os.path.exists(template_path):
                return {"status": "error", "error": f"Template file not found: {template_path}"}

            # Load template
            try:
                template = cv2.imread(template_path, cv2.IMREAD_COLOR)
                if template is None:
                    return {
                        "status": "error",
                        "error": f"Failed to load template image: {template_path}",
                    }
                template_height, template_width = template.shape[:2]
            except Exception as e:
                return {"status": "error", "error": f"Error loading template image: {e}"}

            # Take screenshot of target area
            screenshot = take_screenshot(window_handle=window_handle, region=region, format="png")
            if screenshot["status"] != "success":
                return screenshot

            try:
                # Convert screenshot to OpenCV format
                screenshot_np = np.frombuffer(screenshot["image"], np.uint8)
                screenshot_cv = cv2.imdecode(screenshot_np, cv2.IMREAD_COLOR)

                # Perform template matching
                result = cv2.matchTemplate(screenshot_cv, template, cv2.TM_CCOEFF_NORMED)
                _min_val, max_val, _min_loc, max_loc = cv2.minMaxLoc(result)

                # Check if match is above threshold
                if max_val >= threshold:
                    # Calculate center and bounding box
                    x, y = max_loc
                    center_x = x + (template_width // 2)
                    center_y = y + (template_height // 2)

                    return {
                        "status": "success",
                        "found": True,
                        "confidence": float(max_val),
                        "location": {
                            "x": int(center_x),
                            "y": int(center_y),
                            "left": int(x),
                            "top": int(y),
                            "right": int(x + template_width),
                            "bottom": int(y + template_height),
                            "width": int(template_width),
                            "height": int(template_height),
                        },
                        "timestamp": time.time(),
                    }
                else:
                    return {
                        "status": "success",
                        "found": False,
                        "confidence": float(max_val),
                        "message": "No match found above threshold",
                        "threshold": float(threshold),
                        "timestamp": time.time(),
                    }

            except Exception as e:
                return {"status": "error", "error": f"Error during template matching: {e}"}

            finally:
                # Clean up temp file if it exists
                if "file_path" in screenshot:
                    try:
                        os.unlink(screenshot["file_path"])
                    except:
                        pass

        except Exception as e:
            logger.error(f"Error in find_image: {e}")
            return {"status": "error", "error": str(e)}

    @app.tool()
    def highlight_element(
        window_handle: int,
        control_id: str,
        color: str = "red",
        thickness: int = 2,
        duration: float = 3.0,
        output_path: str | None = None,
    ) -> dict[str, Any]:
        """Highlight a UI element with a colored rectangle.

        Args:
            window_handle: Handle of the window containing the element
            control_id: Control ID of the element to highlight
            color: Highlight color (name or hex code, e.g., "red" or "#FF0000")
            thickness: Thickness of the highlight border in pixels
            duration: Duration to show the highlight in seconds (0 for just save/return)
            output_path: Optional path to save the highlighted image

        Returns:
            Dict containing the result of the operation

        """
        try:
            from pywinauto import Desktop
            from pywinauto.win32functions import SetForegroundWindow

            # Bring window to foreground
            try:
                SetForegroundWindow(window_handle)
                time.sleep(0.5)  # Give window time to come to foreground
            except Exception as e:
                logger.warning(f"Could not bring window to foreground: {e}")

            # Get the element rectangle
            desktop = Desktop(backend="uia")
            window = desktop.window(handle=window_handle)
            element = window.child_window(control_id=control_id)

            if not element.exists():
                return {
                    "status": "error",
                    "error": f"Element with control_id '{control_id}' not found",
                }

            rect = element.rectangle()

            # Take screenshot of the window
            screenshot = take_screenshot(window_handle=window_handle, format="png")
            if screenshot["status"] != "success":
                return screenshot

            try:
                # Convert screenshot to OpenCV format
                screenshot_np = np.frombuffer(screenshot["image"], np.uint8)
                img = cv2.imdecode(screenshot_np, cv2.IMREAD_COLOR)

                # Convert color to BGR for OpenCV
                if color.startswith("#"):
                    # Hex color
                    color = color.lstrip("#")
                    bgr = tuple(int(color[i : i + 2], 16) for i in (4, 2, 0))
                else:
                    # Named color
                    color_lower = color.lower()
                    if color_lower == "red":
                        bgr = (0, 0, 255)
                    elif color_lower == "green":
                        bgr = (0, 255, 0)
                    elif color_lower == "blue":
                        bgr = (255, 0, 0)
                    elif color_lower == "yellow":
                        bgr = (0, 255, 255)
                    else:
                        bgr = (0, 0, 255)  # Default to red

                # Draw rectangle
                top_left = (rect.left, rect.top)
                bottom_right = (rect.right, rect.bottom)
                cv2.rectangle(img, top_left, bottom_right, bgr, thickness)

                # Save or show the result
                if output_path:
                    cv2.imwrite(output_path, img)

                # Convert back to PIL for display if needed
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(img_rgb)

                # Save to temp file if no output path specified
                if not output_path:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                        temp_path = temp_file.name
                        pil_img.save(temp_path, format="PNG")
                        output_path = temp_path

                # Show the image if duration > 0
                if duration > 0:
                    pil_img.show()
                    time.sleep(duration)

                return {
                    "status": "success",
                    "output_path": output_path,
                    "element": {
                        "control_id": control_id,
                        "left": rect.left,
                        "top": rect.top,
                        "right": rect.right,
                        "bottom": rect.bottom,
                        "width": rect.width(),
                        "height": rect.height(),
                    },
                    "timestamp": time.time(),
                }

            except Exception as e:
                return {"status": "error", "error": f"Error processing image: {e}"}

            finally:
                # Clean up temp file if it exists
                if "file_path" in screenshot:
                    try:
                        os.unlink(screenshot["file_path"])
                    except:
                        pass

        except Exception as e:
            logger.error(f"Error in highlight_element: {e}")
            return {"status": "error", "error": str(e)}

    # Add all tools to __all__
    __all__ = ["extract_text", "find_image", "highlight_element", "take_screenshot"]
