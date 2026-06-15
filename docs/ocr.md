# OCR (Optical Character Recognition)

Windows Computer Use MCP uses [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) via the `pytesseract` Python wrapper for extracting text from screenshots and window captures.

## How it's used

| Tool | Function | OCR Use |
|------|----------|---------|
| `automation_visual` | `extract_text` | OCR a window or screen region |
| `automation_assert` | `assert_text` | Verify text appears in a window |
| `get_window_state` | `use_ocr=True` | Enrich UIA element tree with OCR text |
| `get_desktop_state` | `use_ocr=True` | OCR-enrich full desktop tree |
| `api/v1/ocr/*` | REST endpoints | OCR via HTTP API |
| Adaptive cascade | OCR fallback | Find elements when UIA selectors fail |

## About Tesseract

[Tesseract](https://github.com/tesseract-ocr/tesseract) is the most widely used open-source OCR engine. Originally developed by HP in the 1980s, it was open-sourced in 2005 and later maintained by Google. Version 4.0 (2018) introduced an LSTM-based neural network classifier, and version 5.x (2021+) continues improvements.

- **GitHub:** https://github.com/tesseract-ocr/tesseract
- **Current version:** 5.5.0 (as of 2026)
- **License:** Apache 2.0
- **Language:** C++
- **Training data:** `tessdata` — language-specific `.traineddata` files with character models and dictionaries

## Known limitations

Discovered during testing of this repo:

| Issue | Detail |
|-------|--------|
| **ASCII art** | Widely separated symbol groups (e.g. `(__)` then spaces then `(__)`) confuse page layout analysis. The characters themselves (`(`, `)`, `\`, `/`) are read correctly in normal text flow. |
| **Minimum font size** | Characters smaller than ~10pt (x-height < 20px) degrade recognition. Notepad default ~9pt is marginal. Enlarge with `Ctrl+Shift+>` or use larger UI text. |
| **Consolas `/` and `\`** | These characters render similarly to letters in monospace fonts. `/` is often read as `[` or `1`, `\` as `V` or `]`. |
| **Keyboard shortcut `Ctrl`** | Frequently read as `Ctr1` (digit 1 replaces lowercase l). This is standard for OCR — most commercial engines have the same issue with small type. |
| **`$` sign** | Sometimes read as `@` or `S` depending on font. |

## Setup

### Automatic (recommended)

```powershell
just install-tesseract        # interactive dialog
.\scripts\install-tesseract.ps1  # silent
```

The NSIS installer also offers Tesseract as an optional checkbox during setup.

### Manual

Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/releases) and run the installer. Ensure `C:\Program Files\Tesseract-OCR` is in your PATH.

Tesseract 5.x requires the `eng` traineddata file, which is included in the installer (~5 MB). Additional languages can be downloaded from [tesseract-ocr/tessdata](https://github.com/tesseract-ocr/tessdata).

## Verification

```powershell
tesseract --version
tesseract --list-langs
```

Or from Python:

```python
import pytesseract
print(pytesseract.get_tesseract_version())
```

## Testing

OCR screenshots and results are saved to `ocr_scans/ocr_result_<timestamp>.txt` with corresponding PNG files. The autonomous demo (`just demo-autonomous`) runs a full pipeline: type text → screenshot → OCR → display → save.

## Competition

| Engine | License | Quality | Speed | Notes |
|--------|---------|---------|-------|-------|
| **Tesseract 5.x** | Apache 2.0 | Good | Fast | Default, free, self-hosted |
| **Windows Media OCR** | Proprietary | Good | Fast | Built into Windows, COM API, no install |
| **Azure AI Vision** | Commercial | Excellent | Fast | Cloud-based, pay-per-call |
| **Google Cloud Vision** | Commercial | Excellent | Fast | Cloud-based, pay-per-call |
| **AWS Textract** | Commercial | Excellent | Fast | Cloud-based, pay-per-page |
| **EasyOCR** | Apache 2.0 | Good | Moderate | Python, supports 80+ languages |
| **PaddleOCR** | Apache 2.0 | Good | Fast | Chinese-focused but multi-language |
| **Surya OCR** | MIT | Very Good | Moderate | Modern architecture, good for dense text |

### Windows Media OCR

Windows 10/11 includes a built-in OCR engine accessible via `Windows.Media.Ocr` COM API. It's the same engine used by Windows Snipping Tool and the Xbox Game Bar. It can be faster than Tesseract for UI text and doesn't require a separate install. Not currently integrated into this repo — a future enhancement could add it as an alternative provider.

## Future

- Windows Media OCR integration as an alternative backend
- Preprocessing pipeline: adaptive binarization, deskew, resolution upscaling
- OCR confidence scoring in `extract_text` results
- Configurable per-application OCR presets (e.g. terminal fonts vs prose)
