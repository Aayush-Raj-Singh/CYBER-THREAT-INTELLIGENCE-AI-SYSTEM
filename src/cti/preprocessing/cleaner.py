from __future__ import annotations

import re
from typing import Iterable, List, Tuple

from bs4 import BeautifulSoup


def strip_html(text: str) -> str:
    if "<" not in text and ">" not in text:
        return text
    soup = BeautifulSoup(text, "lxml")
    return soup.get_text(" ")


def normalize_whitespace(text: str) -> str:
    text = text.replace("\u0000", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def remove_noise_lines(text: str, patterns: Iterable[str]) -> str:
    if not patterns:
        return text
    compiled = [re.compile(pat, flags=re.IGNORECASE) for pat in patterns]
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(pat.search(stripped) for pat in compiled):
            continue
        lines.append(stripped)
    return "\n".join(lines)


def clean_text(text: str, noise_patterns: Iterable[str]) -> str:
    # WHY: keep transformations minimal to preserve IOCs for later extraction.
    text = strip_html(text)
    text = remove_noise_lines(text, noise_patterns)
    text = normalize_whitespace(text)
    return text


def tokenize(text: str, min_token_length: int = 2) -> List[str]:
    # WHY: allow tokens to keep IOC-friendly characters like '.', ':', '/', '@'.
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9_\-\.:/@%\+=]*", text)
    if min_token_length <= 1:
        return tokens
    return [token for token in tokens if len(token) >= min_token_length]
