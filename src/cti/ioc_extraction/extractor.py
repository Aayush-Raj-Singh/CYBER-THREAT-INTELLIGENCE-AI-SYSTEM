from __future__ import annotations

import re
from typing import Dict, Iterable, List

import tldextract


# Regex patterns intentionally conservative to reduce false positives.
PATTERNS: Dict[str, re.Pattern[str]] = {
    "ipv4": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "md5": re.compile(r"\b[a-fA-F0-9]{32}\b"),
    "sha1": re.compile(r"\b[a-fA-F0-9]{40}\b"),
    "sha256": re.compile(r"\b[a-fA-F0-9]{64}\b"),
    "url": re.compile(r"\bhttps?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]+\b"),
    "domain": re.compile(r"\b(?:[A-Za-z0-9-]{1,63}\.)+[A-Za-z]{2,}\b"),
}


def extract_iocs(text: str) -> Dict[str, List[str]]:
    hits: Dict[str, List[str]] = {key: [] for key in PATTERNS}
    for key, pattern in PATTERNS.items():
        hits[key] = list({match for match in pattern.findall(text)})
    return hits


def normalize_domain(domain: str) -> str:
    extracted = tldextract.extract(domain)
    if not extracted.domain or not extracted.suffix:
        return domain.lower()
    return f"{extracted.domain}.{extracted.suffix}".lower()


def normalize_url(url: str) -> str:
    return url.strip().lower()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_hash(hash_value: str) -> str:
    return hash_value.strip().lower()


def normalize_ip(ip: str) -> str:
    return ip.strip()


def normalize_ioc(ioc_type: str, value: str) -> str:
    if ioc_type == "domain":
        return normalize_domain(value)
    if ioc_type == "url":
        return normalize_url(value)
    if ioc_type == "email":
        return normalize_email(value)
    if ioc_type in {"md5", "sha1", "sha256"}:
        return normalize_hash(value)
    if ioc_type == "ipv4":
        return normalize_ip(value)
    return value.strip()
