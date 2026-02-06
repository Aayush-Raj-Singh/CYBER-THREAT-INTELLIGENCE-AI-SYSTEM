from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from cti.correlation.models import Campaign, CorrelationResult


def write_correlation_results(results: Iterable[CorrelationResult], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for result in results:
            payload = {
                "event_id": result.event_id,
                "campaign_id": result.campaign_id,
                "shared_iocs": result.shared_iocs,
                "temporal_cluster": result.temporal_cluster,
                "mitre_tactics": result.mitre_tactics,
                "confidence": result.confidence,
            }
            handle.write(json.dumps(payload, ensure_ascii=True))
            handle.write("\n")
            count += 1
    return count


def write_campaigns(campaigns: Iterable[Campaign], output_path: str) -> int:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for campaign in campaigns:
            payload = {
                "campaign_id": campaign.campaign_id,
                "name": campaign.name,
                "start_time": campaign.start_time.isoformat(),
                "end_time": campaign.end_time.isoformat(),
                "event_ids": campaign.event_ids,
                "iocs": campaign.iocs,
                "mitre_tactics": campaign.mitre_tactics,
                "confidence": campaign.confidence,
            }
            handle.write(json.dumps(payload, ensure_ascii=True))
            handle.write("\n")
            count += 1
    return count
