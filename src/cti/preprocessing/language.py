from __future__ import annotations

from typing import Tuple

from langdetect import detect_langs


def detect_language(text: str) -> Tuple[str, float]:
    try:
        results = detect_langs(text)
    except Exception:
        return "unknown", 0.0
    if not results:
        return "unknown", 0.0
    top = results[0]
    return top.lang, float(top.prob)
