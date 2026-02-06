from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
import logging

from cti.reporting.models import ReportBundle, ReportItem
from cti.reporting.readers import (
    read_analysis,
    read_campaigns,
    read_correlation,
    read_iocs,
    read_scores,
)
from cti.reporting.summaries import build_summary


class ReportingManager:
    def __init__(self, config: Dict[str, Any], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

    def generate(self) -> ReportBundle:
        reporting_cfg = self.config.get("reporting", {})
        analysis_cfg = self.config.get("analysis", {})
        correlation_cfg = self.config.get("correlation", {})
        ioc_cfg = self.config.get("ioc_extraction", {})
        scoring_cfg = self.config.get("scoring", {})

        analysis_path = reporting_cfg.get(
            "input_analysis_path",
            analysis_cfg.get("output_analysis_path", "data/analysis_results.jsonl"),
        )
        correlation_path = reporting_cfg.get(
            "input_correlation_path",
            correlation_cfg.get("output_correlation_path", "data/correlation_results.jsonl"),
        )
        scores_path = reporting_cfg.get(
            "input_scores_path",
            scoring_cfg.get("output_scores_path", "data/scores.jsonl"),
        )
        iocs_path = reporting_cfg.get(
            "input_iocs_path",
            ioc_cfg.get("output_iocs_path", "data/iocs.jsonl"),
        )
        campaigns_path = reporting_cfg.get(
            "input_campaigns_path",
            correlation_cfg.get("output_campaigns_path", "data/campaigns.jsonl"),
        )

        analysis_map = {item.event_id: item for item in read_analysis(analysis_path)}
        correlation_map = {item.event_id: item for item in read_correlation(correlation_path)}
        score_map = {item.event_id: item for item in read_scores(scores_path)}

        ioc_map: Dict[str, List[str]] = {}
        for ioc in read_iocs(iocs_path):
            ioc_map.setdefault(ioc.source_event_id, []).append(ioc.normalized_value)

        items: List[ReportItem] = []
        for event_id, analysis in analysis_map.items():
            corr = correlation_map.get(event_id)
            score = score_map.get(event_id)
            iocs = ioc_map.get(event_id, [])

            if score is None:
                continue

            mitre_tactics = corr.mitre_tactics if corr else []

            summary = build_summary(
                incident_type=analysis.incident_type,
                sector=analysis.sector,
                severity_label=score.severity_label,
                ioc_count=len(iocs),
                mitre_tactics=mitre_tactics,
            )

            items.append(
                ReportItem(
                    event_id=event_id,
                    incident_type=analysis.incident_type,
                    sector=analysis.sector,
                    severity_label=score.severity_label,
                    severity=score.severity,
                    confidence=score.confidence,
                    mitre_tactics=mitre_tactics,
                    iocs=iocs[:10],
                    summary=summary,
                )
            )

        items = sorted(items, key=lambda item: item.severity, reverse=True)
        campaigns = list(read_campaigns(campaigns_path))

        bundle = ReportBundle(generated_at=datetime.utcnow(), items=items, campaigns=campaigns)
        self.logger.info("Reporting generated items=%d campaigns=%d", len(items), len(campaigns))
        return bundle

    def write(self, bundle: ReportBundle) -> None:
        reporting_cfg = self.config.get("reporting", {})
        output_json = reporting_cfg.get("output_json_path", "reports/report.json")
        output_summary = reporting_cfg.get("output_summary_path", "reports/summary.txt")

        self._write_json(bundle, output_json)
        self._write_summary(bundle, output_summary)

    def _write_json(self, bundle: ReportBundle, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generated_at": bundle.generated_at.isoformat(),
            "items": [item.__dict__ for item in bundle.items],
            "campaigns": bundle.campaigns,
        }
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

    def _write_summary(self, bundle: ReportBundle, output_path: str) -> None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: List[str] = []
        lines.append(f"CTI Report generated at {bundle.generated_at.isoformat()}")
        lines.append("=")

        for item in bundle.items[:50]:
            lines.append(f"Event: {item.event_id}")
            lines.append(f"Summary: {item.summary}")
            lines.append(f"Severity: {item.severity_label} ({item.severity:.2f})")
            lines.append(f"Confidence: {item.confidence:.2f}")
            if item.mitre_tactics:
                lines.append("MITRE: " + ", ".join(item.mitre_tactics))
            if item.iocs:
                lines.append("IOCs: " + ", ".join(item.iocs))
            lines.append("-")

        path.write_text("\n".join(lines), encoding="utf-8")
