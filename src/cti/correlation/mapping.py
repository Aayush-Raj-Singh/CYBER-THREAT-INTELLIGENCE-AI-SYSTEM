from __future__ import annotations

from typing import Dict, List

# High-level MITRE ATT&CK mapping based on common keywords (defensible, explainable).
TACTIC_KEYWORDS: Dict[str, List[str]] = {
    "Initial Access": ["phishing", "spearphish", "drive-by", "exploit", "malvertising"],
    "Execution": ["malware", "payload", "ransomware", "dropper"],
    "Persistence": ["persistence", "backdoor", "autorun", "registry"],
    "Privilege Escalation": ["privilege escalation", "elevation"],
    "Defense Evasion": ["obfuscation", "evas", "anti-debug"],
    "Credential Access": ["credential", "password", "hashdump", "token"],
    "Discovery": ["scan", "recon", "enumeration"],
    "Lateral Movement": ["lateral", "pivot", "remote exec"],
    "Collection": ["exfil", "collection", "archive"],
    "Command and Control": ["c2", "command and control", "beacon"],
    "Exfiltration": ["exfiltration", "data leak", "data breach"],
    "Impact": ["ddos", "denial of service", "destruction", "encryption"],
}


def map_mitre_tactics(text: str) -> List[str]:
    text_lower = text.lower()
    tactics: List[str] = []
    for tactic, keywords in TACTIC_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                tactics.append(tactic)
                break
    return tactics


def extract_temporal_key(timestamp: float, window_hours: int = 24) -> str:
    # WHY: simple time-bucketing supports explainable campaign grouping.
    window_seconds = window_hours * 3600
    bucket = int(timestamp // window_seconds) * window_seconds
    return f"window_{bucket}"
