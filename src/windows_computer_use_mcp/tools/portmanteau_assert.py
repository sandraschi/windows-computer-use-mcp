"""UI verification portmanteau tool — hash, diff, wait_stable, template/text asserts."""

from __future__ import annotations

import logging
import time

from windows_computer_use_mcp import assert_engine

try:
    from windows_computer_use_mcp.app import app

    logger = logging.getLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)
    app = None

from windows_computer_use_mcp.tools.models import AssertOperationRequest, ToolResult


def _region(request: AssertOperationRequest) -> tuple[int, int, int, int] | None:
    return assert_engine._region_tuple(
        request.region_left,
        request.region_top,
        request.region_right,
        request.region_bottom,
    )


if app is not None:

    @app.tool(
        name="automation_assert",
        description="""UI verification for computer-use automation — stability polling, image diff, template/OCR asserts.

WHAT IT DOES:
Polls screenshots until the UI stabilizes, compares before/after images, and asserts expected visual
or text state. Use after keyboard shortcuts or clicks to confirm the action succeeded before continuing.

WHEN TO USE:
- wait_stable: after navigation shortcuts (F-keys, Ctrl+N) — wait for rendering to finish
- assert_changed: confirm a step produced a visible UI change
- assert_unchanged: confirm a no-op or focus-only action did not alter the canvas
- diff: get changed_pct and a heatmap PNG for failure logs
- assert_template: check a dialog or button icon is visible (OpenCV template match)
- assert_text: OCR a region and check for expected dialog title or label
- hash / hash_region: fingerprint a screen region (dhash tolerates GPU rendering noise)

RECOVERY:
If wait_stable times out, increase timeout_s or narrow region_* to the editor panel only.
If assert_changed fails with low changed_pct, the shortcut may not have reached the focused window.
""",
    )
    def automation_assert(request: AssertOperationRequest) -> ToolResult:
        """Verification portmanteau — stability, diff, and assert operations."""
        try:
            op = request.operation
            region = _region(request)
            ts = time.time()

            if op in ("hash", "hash_region"):
                if op == "hash_region" and region is None:
                    return ToolResult(
                        status="error",
                        message="hash_region requires region_left/top/right/bottom.",
                        recovery_tip="Set region_* to the editor canvas, ignoring window chrome.",
                    )
                img = assert_engine.capture_image(
                    image_path=request.image_path,
                    window_handle=request.window_handle,
                    region=region,
                )
                h = assert_engine.image_hash(img, request.hash_algorithm)
                return ToolResult(
                    status="success",
                    message=f"Image hash computed ({request.hash_algorithm}).",
                    data={
                        "hash": h,
                        "algorithm": request.hash_algorithm,
                        "width": img.width,
                        "height": img.height,
                        "timestamp": ts,
                    },
                )

            if op == "diff":
                if not request.image_path or not request.image_path_b:
                    return ToolResult(
                        status="error",
                        message="diff requires image_path and image_path_b.",
                        recovery_tip="Capture before/after screenshots with automation_visual first.",
                    )
                before = assert_engine.capture_image(image_path=request.image_path)
                after = assert_engine.capture_image(image_path=request.image_path_b)
                if region:
                    before = assert_engine.crop_region(before, region)
                    after = assert_engine.crop_region(after, region)
                result = assert_engine.image_diff(
                    before,
                    after,
                    change_threshold=request.pixel_diff_threshold,
                    output_path=request.output_path,
                )
                return ToolResult(
                    status="success",
                    message=f"Diff complete: {result['changed_pct']}% pixels changed.",
                    data={**result, "timestamp": ts},
                )

            if op == "wait_stable":
                result = assert_engine.wait_stable(
                    window_handle=request.window_handle,
                    image_path=request.image_path,
                    region=region,
                    stable_frames_required=request.stable_frames_required,
                    poll_interval_s=request.poll_interval_s,
                    timeout_s=request.timeout_s,
                    hash_algorithm=request.hash_algorithm,
                    output_dir=request.output_dir,
                )
                if result.get("stable"):
                    return ToolResult(
                        status="success",
                        message="UI stabilized.",
                        data={**result, "timestamp": ts},
                    )
                return ToolResult(
                    status="error",
                    message=f"UI did not stabilize within {request.timeout_s}s.",
                    data={**result, "timestamp": ts},
                    recovery_tip="Increase timeout_s, narrow region_* to the editor panel, or check if an animation is still running.",
                )

            if op == "assert_changed":
                if not request.image_path or not request.image_path_b:
                    return ToolResult(
                        status="error",
                        message="assert_changed requires image_path and image_path_b.",
                    )
                before = assert_engine.capture_image(image_path=request.image_path)
                after = assert_engine.capture_image(image_path=request.image_path_b)
                if region:
                    before = assert_engine.crop_region(before, region)
                    after = assert_engine.crop_region(after, region)
                diff = assert_engine.image_diff(
                    before,
                    after,
                    change_threshold=request.pixel_diff_threshold,
                    output_path=request.output_path,
                )
                if diff["changed_pct"] >= request.change_threshold_pct:
                    return ToolResult(
                        status="success",
                        message=f"UI changed ({diff['changed_pct']}% >= {request.change_threshold_pct}%).",
                        data={**diff, "timestamp": ts},
                    )
                err_data = {**diff, "timestamp": ts}
                if request.evidence_bundle:
                    err_data["evidence"] = {
                        "before_path": request.image_path,
                        "after_path": request.image_path_b,
                        "diff_path": diff.get("diff_path"),
                        "changed_pct": diff["changed_pct"],
                    }
                return ToolResult(
                    status="error",
                    message=f"UI unchanged ({diff['changed_pct']}% < {request.change_threshold_pct}%).",
                    data=err_data,
                    recovery_tip="The action may not have reached the focused window. Call automation_windows(focus) first.",
                )

            if op == "assert_unchanged":
                if not request.image_path or not request.image_path_b:
                    return ToolResult(
                        status="error",
                        message="assert_unchanged requires image_path and image_path_b.",
                    )
                before = assert_engine.capture_image(image_path=request.image_path)
                after = assert_engine.capture_image(image_path=request.image_path_b)
                if region:
                    before = assert_engine.crop_region(before, region)
                    after = assert_engine.crop_region(after, region)
                diff = assert_engine.image_diff(
                    before,
                    after,
                    change_threshold=request.pixel_diff_threshold,
                    output_path=request.output_path,
                )
                if diff["changed_pct"] <= request.unchanged_threshold_pct:
                    return ToolResult(
                        status="success",
                        message=f"UI stable ({diff['changed_pct']}% <= {request.unchanged_threshold_pct}%).",
                        data={**diff, "timestamp": ts},
                    )
                return ToolResult(
                    status="error",
                    message=f"Unexpected UI change ({diff['changed_pct']}% > {request.unchanged_threshold_pct}%).",
                    data={**diff, "timestamp": ts},
                    recovery_tip="An animation or background update may be invalidating the check. Use region_* to mask volatile areas.",
                )

            if op == "assert_template":
                if not request.template_path:
                    return ToolResult(
                        status="error",
                        message="assert_template requires template_path.",
                    )
                haystack = assert_engine.capture_image(
                    image_path=request.image_path,
                    window_handle=request.window_handle,
                    region=None,
                )
                match = assert_engine.assert_template_match(
                    haystack,
                    request.template_path,
                    match_threshold=request.match_threshold,
                    region=region,
                )
                if match["found"]:
                    return ToolResult(
                        status="success",
                        message=f"Template found (confidence {match['confidence']}).",
                        data={**match, "timestamp": ts},
                    )
                return ToolResult(
                    status="error",
                    message=f"Template not found (confidence {match['confidence']} < {request.match_threshold}).",
                    data={**match, "timestamp": ts},
                    recovery_tip="Recapture template at current resolution/DPI or lower match_threshold slightly.",
                )

            if op == "assert_text":
                if not request.expected_text:
                    return ToolResult(
                        status="error",
                        message="assert_text requires expected_text.",
                    )
                img = assert_engine.capture_image(
                    image_path=request.image_path,
                    window_handle=request.window_handle,
                    region=region,
                )
                text_result = assert_engine.assert_text_in_image(
                    img,
                    request.expected_text,
                    exact_match=request.exact_match,
                    region=region,
                    language=request.language,
                )
                if text_result["found"]:
                    return ToolResult(
                        status="success",
                        message=f"Text found: {request.expected_text!r}.",
                        data={**text_result, "timestamp": ts},
                    )
                return ToolResult(
                    status="error",
                    message=f"Text not found: {request.expected_text!r}.",
                    data={**text_result, "timestamp": ts},
                    recovery_tip="Widen region_* or verify Tesseract is installed. OCR text is in data.ocr_text.",
                )

            return ToolResult(status="error", message=f"Unknown operation: {op}")

        except FileNotFoundError as exc:
            return ToolResult(
                status="error",
                message=str(exc),
                recovery_tip="Verify image_path or template_path exists.",
            )
        except RuntimeError as exc:
            return ToolResult(
                status="error",
                message=str(exc),
                recovery_tip="Install missing dependency (opencv-python-headless or pytesseract).",
            )
        except Exception as exc:
            if type(exc).__name__ == "TesseractNotFoundError":
                return ToolResult(
                    status="error",
                    message="Tesseract OCR binary not installed or not in PATH.",
                    recovery_tip="Install Tesseract OCR on the host and ensure it is in PATH.",
                )
            logger.exception("automation_assert failed")
            return ToolResult(
                status="error",
                message=f"Assert operation failed: {exc}",
                recovery_tip="Capture a screenshot with automation_visual and retry with image_path.",
            )
