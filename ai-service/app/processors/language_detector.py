"""Detect the primary language of extracted text."""

from __future__ import annotations

import logging

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

logger = logging.getLogger(__name__)

# Make langdetect deterministic
DetectorFactory.seed = 0


def detect_language(text: str) -> str:
    """Return a BCP-47 language code (e.g. ``en``, ``fr``, ``de``).

    Returns ``"unknown"`` when the text is too short or detection fails.
    """
    if not text or len(text.strip()) < 10:
        logger.debug("Text too short for language detection (%d chars)", len(text))
        return "unknown"

    try:
        lang = detect(text)
        logger.debug("Detected language: %s", lang)
        return lang
    except LangDetectException:
        logger.warning("Language detection failed, returning 'unknown'")
        return "unknown"
