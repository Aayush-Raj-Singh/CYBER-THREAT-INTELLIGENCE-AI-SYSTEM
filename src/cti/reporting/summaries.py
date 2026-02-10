from __future__ import annotations

from typing import Dict, List


def build_summary(
    incident_type: str,
    sector: str,
    severity_label: str,
    ioc_count: int,
    mitre_tactics: List[str],
) -> str:
    # WHY: short, analyst-readable summary without overstating certainty.
    parts: List[str] = []
    if incident_type and incident_type != "unknown":
        parts.append(f"Likely {incident_type} activity")
    else:
        parts.append("Unclassified activity")

    if sector and sector != "unknown":
        parts.append(f"targeting {sector} sector")

    if severity_label:
        parts.append(f"severity assessed as {severity_label}")

    if ioc_count > 0:
        parts.append(f"{ioc_count} IOCs observed")

    if mitre_tactics:
        parts.append("MITRE tactics: " + ", ".join(mitre_tactics[:4]))

    return "; ".join(parts)
