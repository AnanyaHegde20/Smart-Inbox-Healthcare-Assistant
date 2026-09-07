"""Tesseract OCR provider implementation.

Requires ``pytesseract`` and the Tesseract binary installed on the system.
Falls back to a stub if Tesseract is unavailable so that the rest of the
system remains testable.

Configuration via environment variables:
    TESSERACT_PATH  – Path to the Tesseract executable (auto-detected if unset)
    TESSDATA_PREFIX  – Path to tessdata directory (optional)
"""

from __future__ import annotations

import io
import logging
import os
from typing import TYPE_CHECKING

from PIL import Image

from .provider import OCRPageResult, OCRProvider, OCRWord

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Words with confidence below this are flagged
_LOW_CONFIDENCE_THRESHOLD = 0.6

# Try importing pytesseract; mark availability
try:
    import pytesseract

    _TESSERACT_AVAILABLE = True
except ImportError:
    _TESSERACT_AVAILABLE = False
    logger.warning(
        "pytesseract not installed – TesseractProvider will return empty results. "
        "Install with: pip install pytesseract"
    )


def _configure_tesseract_path() -> None:
    """Configure pytesseract to use the Tesseract binary from env or auto-detect."""
    if not _TESSERACT_AVAILABLE:
        return

    # Check env var first
    env_path = os.environ.get("TESSERACT_PATH")
    if env_path and os.path.isfile(env_path):
        pytesseract.pytesseract.tesseract_cmd = env_path
        logger.info("Tesseract configured from TESSERACT_PATH: %s", env_path)
        return

    # Check common Windows install locations
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe"),
        "/usr/bin/tesseract",
        "/usr/local/bin/tesseract",
    ]
    for path in common_paths:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            logger.info("Tesseract auto-detected at: %s", path)
            return

    logger.warning(
        "Tesseract executable not found. Set TESSERACT_PATH env var or "
        "install Tesseract to a standard location."
    )


# Configure on module load
_configure_tesseract_path()


def _image_bytes_to_pil(image_bytes: bytes) -> Image.Image:
    return Image.open(io.BytesIO(image_bytes))


class TesseractProvider(OCRProvider):
    """OCR provider backed by Tesseract via pytesseract.

    If Tesseract is not installed, ``_run_ocr`` returns an empty result
    with zero confidence rather than raising, so downstream code can
    still run in CI or on machines without Tesseract.

    Parameters
    ----------
    lang : str
        Tesseract language code(s), e.g. "eng", "fra", "eng+fra".
        Defaults to "eng".
    """

    def __init__(self, lang: str = "eng") -> None:
        self.lang = lang

    def _run_ocr(self, image_bytes: bytes, page_number: int) -> OCRPageResult:
        if not _TESSERACT_AVAILABLE:
            logger.warning(
                "Tesseract not available – skipping OCR for page %d", page_number
            )
            return OCRPageResult(
                page_number=page_number,
                full_text="[OCR unavailable – pytesseract not installed]",
                words=[],
                mean_confidence=0.0,
                low_confidence_count=0,
            )

        # Verify the Tesseract binary is accessible
        try:
            pytesseract.get_tesseract_version()
        except Exception as exc:
            logger.error(
                "Tesseract binary not accessible: %s – skipping OCR for page %d",
                exc,
                page_number,
            )
            return OCRPageResult(
                page_number=page_number,
                full_text=f"[OCR unavailable – Tesseract binary error: {exc}]",
                words=[],
                mean_confidence=0.0,
                low_confidence_count=0,
            )

        img = _image_bytes_to_pil(image_bytes)

        # Get per-word data with confidence scores
        data = pytesseract.image_to_data(img, lang=self.lang, output_type=pytesseract.Output.DICT)

        words: list[OCRWord] = []
        confidences: list[float] = []
        low_count = 0

        n = len(data["text"])
        for i in range(n):
            text = data["text"][i].strip()
            conf_raw = data["conf"][i]

            # conf == -1 means non-word element (line break, block start, etc.)
            if conf_raw == -1 or not text:
                continue

            conf = conf_raw / 100.0  # Tesseract returns 0-100
            words.append(OCRWord(text=text, confidence=round(conf, 4)))
            confidences.append(conf)
            if conf < _LOW_CONFIDENCE_THRESHOLD:
                low_count += 1

        full_text = pytesseract.image_to_string(img, lang=self.lang).strip()
        mean_conf = sum(confidences) / len(confidences) if confidences else 0.0

        logger.info(
            "OCR page %d: %d words, mean confidence %.2f, %d low-confidence",
            page_number,
            len(words),
            mean_conf,
            low_count,
        )

        return OCRPageResult(
            page_number=page_number,
            full_text=full_text,
            words=words,
            mean_confidence=round(mean_conf, 4),
            low_confidence_count=low_count,
        )
