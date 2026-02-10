from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Set, Tuple
import logging

import networkx as nx

from cti.analysis.models import AnalysisResult
from cti.correlation.mapping import extract_temporal_key, map_mitre_tactics
from cti.correlation.models import Campaign, CorrelationResult
from cti.ioc_extraction.models import IOC
from cti.preprocessing.models import NormalizedEvent


@dataclass
class CorrelationConfig:
    temporal_window_hours: int = 24
    min_shared_iocs: int = 1
    min_campaign_size: int = 2
    use_analysis_clusters: bool = True
    use_temporal_window: bool = True
    weights: Dict[str, float] = None


class CorrelationManager:
    def __init__(self, config: Dict[str, object], logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger

        corr_cfg = config.get("correlation", {})
        self.temporal_window_hours = int(corr_cfg.get("temporal_window_hours", 24))
        self.min_shared_iocs = int(corr_cfg.get("min_shared_iocs", 1))
        self.min_campaign_size = int(corr_cfg.get("min_campaign_size", 2))
        self.use_analysis_clusters = bool(corr_cfg.get("use_analysis_clusters", True))
        self.use_temporal_window = bool(corr_cfg.get("use_temporal_window", True))
        self.weights = corr_cfg.get(
            "weights",
            {
                "shared_ioc": 0.4,
                "analysis_cluster": 0.2,
                "temporal": 0.2,
                "incident_conf": 0.1,
                "sector_conf": 0.1,
            },
        )

    def correlate(
        self,
        events: Iterable[NormalizedEvent],
        iocs: Iterable[IOC],
        analyses: Iterable[AnalysisResult],
    ) -> Tuple[List[CorrelationResult], List[Campaign]]:
        event_map = {event.event_id: event for event in events}
        analysis_map = {analysis.event_id: analysis for analysis in analyses}

        iocs_by_event: Dict[str, List[IOC]] = defaultdict(list)
        ioc_to_events: Dict[str, Set[str]] = defaultdict(set)

        for ioc in iocs:
            iocs_by_event[ioc.source_event_id].append(ioc)
            ioc_to_events[ioc.normalized_value].add(ioc.source_event_id)

        shared_iocs_by_event: Dict[str, List[str]] = defaultdict(list)
        for ioc_value, event_ids in ioc_to_events.items():
            if len(event_ids) < 2:
                continue
            for event_id in event_ids:
                shared_iocs_by_event[event_id].append(ioc_value)

        temporal_keys: Dict[str, str] = {}
        temporal_groups: Dict[str, List[str]] = defaultdict(list)
        for event_id, event in event_map.items():
            timestamp = event.fetched_at.timestamp()
            key = extract_temporal_key(timestamp, self.temporal_window_hours)
            temporal_keys[event_id] = key
            temporal_groups[key].append(event_id)

        cluster_groups: Dict[Optional[int], List[str]] = defaultdict(list)
        for event_id, analysis in analysis_map.items():
            cluster_groups[analysis.cluster_id].append(event_id)

        graph = nx.Graph()
        graph.add_nodes_from(event_map.keys())

        # IOC reuse edges based on shared IOC counts per event pair.
        pair_shared_counts: Dict[Tuple[str, str], int] = defaultdict(int)
        for ioc_value, event_ids in ioc_to_events.items():
            if len(event_ids) < 2:
                continue
            event_list = list(event_ids)
            for i in range(len(event_list)):
                for j in range(i + 1, len(event_list)):
                    key = tuple(sorted((event_list[i], event_list[j])))
                    pair_shared_counts[key] += 1

        for (event_a, event_b), count in pair_shared_counts.items():
            if count >= self.min_shared_iocs:
                graph.add_edge(event_a, event_b, reason="shared_ioc", weight=count)

        # Analysis cluster edges
        if self.use_analysis_clusters:
            for cluster_id, event_ids in cluster_groups.items():
                if cluster_id is None or len(event_ids) < 2:
                    continue
                for i in range(len(event_ids)):
                    for j in range(i + 1, len(event_ids)):
                        graph.add_edge(event_ids[i], event_ids[j], reason="analysis_cluster")

        # Temporal window edges
        if self.use_temporal_window:
            for key, event_ids in temporal_groups.items():
                if len(event_ids) < 2:
                    continue
                for i in range(len(event_ids)):
                    for j in range(i + 1, len(event_ids)):
                        graph.add_edge(event_ids[i], event_ids[j], reason="temporal_window")

        campaigns: List[Campaign] = []
        event_to_campaign: Dict[str, str] = {}
        components = list(nx.connected_components(graph))

        for idx, component in enumerate(components, start=1):
            if len(component) < self.min_campaign_size:
                continue
            campaign_id = f"CAMP-{idx:04d}"
            component_events = list(component)
            campaign = self._build_campaign(campaign_id, component_events, event_map, shared_iocs_by_event)
            campaigns.append(campaign)
            for event_id in component_events:
                event_to_campaign[event_id] = campaign_id

        max_shared = max((len(v) for v in shared_iocs_by_event.values()), default=1)

        results: List[CorrelationResult] = []
        for event_id, event in event_map.items():
            analysis = analysis_map.get(event_id)
            shared_iocs = shared_iocs_by_event.get(event_id, [])
            temporal_key = temporal_keys.get(event_id)

            shared_score = min(1.0, len(shared_iocs) / float(max_shared)) if shared_iocs else 0.0
            cluster_score = 0.0
            temporal_score = 0.0

            if analysis and analysis.cluster_id is not None:
                if len(cluster_groups.get(analysis.cluster_id, [])) > 1:
                    cluster_score = 1.0

            if temporal_key and len(temporal_groups.get(temporal_key, [])) > 1:
                temporal_score = 1.0

            incident_conf = analysis.incident_confidence if analysis else 0.0
            sector_conf = analysis.sector_confidence if analysis else 0.0

            confidence = (
                self.weights.get("shared_ioc", 0.4) * shared_score
                + self.weights.get("analysis_cluster", 0.2) * cluster_score
                + self.weights.get("temporal", 0.2) * temporal_score
                + self.weights.get("incident_conf", 0.1) * incident_conf
                + self.weights.get("sector_conf", 0.1) * sector_conf
            )
            confidence = max(0.0, min(1.0, confidence))

            mitre_tactics = map_mitre_tactics(event.clean_text)

            results.append(
                CorrelationResult(
                    event_id=event_id,
                    campaign_id=event_to_campaign.get(event_id),
                    shared_iocs=shared_iocs,
                    temporal_cluster=temporal_key,
                    mitre_tactics=mitre_tactics,
                    confidence=confidence,
                )
            )

        self.logger.info("Correlation complete events=%d campaigns=%d", len(results), len(campaigns))
        return results, campaigns

    def _build_campaign(
        self,
        campaign_id: str,
        event_ids: List[str],
        event_map: Dict[str, NormalizedEvent],
        shared_iocs_by_event: Dict[str, List[str]],
    ) -> Campaign:
        events = [event_map[event_id] for event_id in event_ids if event_id in event_map]
        if not events:
            now = datetime.utcnow()
            return Campaign(campaign_id=campaign_id, name=campaign_id, start_time=now, end_time=now)

        start_time = min(event.fetched_at for event in events)
        end_time = max(event.fetched_at for event in events)

        iocs: Set[str] = set()
        for event_id in event_ids:
            iocs.update(shared_iocs_by_event.get(event_id, []))

        combined_text = "\n".join(event.clean_text for event in events)
        mitre_tactics = list({tactic for tactic in map_mitre_tactics(combined_text)})

        confidence = min(1.0, 0.5 + 0.1 * len(event_ids) + 0.05 * len(iocs))

        return Campaign(
            campaign_id=campaign_id,
            name=campaign_id,
            start_time=start_time,
            end_time=end_time,
            event_ids=event_ids,
            iocs=list(iocs),
            mitre_tactics=mitre_tactics,
            confidence=confidence,
        )
